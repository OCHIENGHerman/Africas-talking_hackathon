"""
Africa's Talking SDK wrapper service.
Handles SMS sending and USSD responses.
Two-way SMS: we receive replies via callback (POST / or /incoming-sms) and send replies via this service.
"""
import africastalking
from app.config import settings
import logging
import time
import ssl

logger = logging.getLogger(__name__)

# Base URLs for Africa's Talking API (same as SDK)
AT_API_SANDBOX = "https://api.sandbox.africastalking.com/version1/messaging"
AT_API_PRODUCTION = "https://api.africastalking.com/version1/messaging"


class ATService:
    """Service wrapper for Africa's Talking SDK."""
    
    def __init__(self):
        """Initialize Africa's Talking SDK with credentials from settings."""
        try:
            # Sandbox requires username "sandbox" (literal); production uses AT_USERNAME
            if settings.AT_ENV in ("sandbox", "techtribe"):
                api_username = "sandbox"
                if settings.AT_USERNAME != "sandbox":
                    logger.info(
                        f"AT_ENV is {settings.AT_ENV}: using username 'sandbox' for API "
                        f"(AT_USERNAME '{settings.AT_USERNAME}' is for display only)"
                    )
            else:
                api_username = settings.AT_USERNAME
            
            africastalking.initialize(
                username=api_username,
                api_key=settings.AT_API_KEY
            )
            self.sms = africastalking.SMS
            self._api_username = api_username
            self._api_key = settings.AT_API_KEY
            self._base_url = AT_API_SANDBOX if api_username == "sandbox" else AT_API_PRODUCTION
            logger.info(
                f"Africa's Talking SDK initialized (username={api_username}, env={settings.AT_ENV})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking SDK: {e}")
            raise

    def _make_ssl_context(self) -> ssl.SSLContext:
        """Build TLS 1.2+ context with certifi CA bundle; sandbox can skip verify if AT_SSL_VERIFY=false."""
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except AttributeError:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        try:
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        except AttributeError:
            pass
        # Disable older protocols to avoid WRONG_VERSION_NUMBER / negotiation issues
        if hasattr(ssl, "OP_NO_SSLv2"):
            ctx.options |= ssl.OP_NO_SSLv2
        if hasattr(ssl, "OP_NO_SSLv3"):
            ctx.options |= ssl.OP_NO_SSLv3
        if hasattr(ssl, "OP_NO_TLSv1"):
            ctx.options |= ssl.OP_NO_TLSv1
        if hasattr(ssl, "OP_NO_TLSv1_1"):
            ctx.options |= ssl.OP_NO_TLSv1_1
        if settings.AT_SSL_VERIFY is False and self._api_username == "sandbox":
            logger.warning("AT_SSL_VERIFY=false: skipping SSL cert verify (sandbox only)")
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            try:
                import certifi
                ctx.load_verify_locations(certifi.where())
            except Exception as e:
                logger.warning(f"Could not load certifi CA bundle: {e}")
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    def _send_sms_direct(self, phone: str, message: str, sender_id: str | None) -> dict:
        """
        Send SMS via direct HTTP POST with explicit TLS 1.2 context and CA bundle.
        Uses certifi CA bundle to fix CERTIFICATE_VERIFY_FAILED on Windows.
        """
        import urllib.request
        import urllib.parse
        import json as _json
        data = {
            "username": self._api_username,
            "to": phone,
            "message": message,
            "bulkSMSMode": 1,
        }
        if sender_id:
            data["from"] = sender_id
        body = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(
            self._base_url,
            data=body,
            headers={
                "Accept": "application/json",
                "ApiKey": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        ctx = self._make_ssl_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            if resp.status != 200:
                raise Exception(f"AT API error {resp.status}: {resp.read().decode()}")
            return _json.loads(resp.read().decode())
    
    def send_sms(self, phone: str, message: str, sender_id: str | None = None) -> dict:
        """
        Send SMS to a phone number.
        
        Args:
            phone: Phone number in international format (e.g., +254712345678)
            message: SMS message content
            sender_id: Optional shortcode or sender_id (overrides settings.AT_SHORTCODE)
            
        Returns:
            Dictionary with response from Africa's Talking API
        """
        try:
            # Ensure phone number is in correct format
            if not phone.startswith("+"):
                # Assume Kenyan number, add +254 if it starts with 0 or 254
                if phone.startswith("0"):
                    phone = "+254" + phone[1:]
                elif phone.startswith("254"):
                    phone = "+" + phone
                else:
                    phone = "+254" + phone
            
            # Use provided sender_id or fall back to settings
            shortcode_or_sender = sender_id or settings.AT_SHORTCODE
            
            logger.info(
                f"Attempting to send SMS to {phone} "
                f"(sender_id provided: {sender_id}, "
                f"AT_SENDER_ID: {settings.AT_SENDER_ID}, AT_SHORTCODE: {settings.AT_SHORTCODE}, "
                f"using: {shortcode_or_sender or 'default'})"
            )
            
            # Sandbox: use direct HTTP first to avoid requests/SSL issues (e.g. WRONG_VERSION_NUMBER on Windows)
            use_direct_first = self._api_username == "sandbox"
            if use_direct_first:
                try:
                    response = self._send_sms_direct(
                        phone, message, str(shortcode_or_sender) if shortcode_or_sender else None
                    )
                    logger.info(f"SMS sent via direct HTTP to {phone}: {response}")
                    return response
                except Exception as e_direct:
                    logger.warning(f"Direct HTTP failed in sandbox, trying SDK: {e_direct}")
            # Try SDK (production or sandbox fallback)
            last_error = None
            for attempt in range(2):
                try:
                    if shortcode_or_sender:
                        response = self.sms.send(message, [phone], sender_id=str(shortcode_or_sender))
                    else:
                        response = self.sms.send(message, [phone])
                    logger.info(f"SMS sent via SDK to {phone} from {shortcode_or_sender or 'default'}: {response}")
                    return response
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    is_ssl = "ssl" in err_str or "wrong_version_number" in err_str or "certificate" in err_str
                    if is_ssl and attempt == 0:
                        time.sleep(0.5)
                        logger.warning(f"SDK SSL error (attempt {attempt + 1}/2), retrying: {e}")
                        continue
                    break
            # Final fallback: direct HTTP (if we didn't try it first)
            if not use_direct_first:
                try:
                    logger.warning(f"SDK failed, trying direct HTTP: {last_error}")
                    response = self._send_sms_direct(
                        phone, message, str(shortcode_or_sender) if shortcode_or_sender else None
                    )
                    logger.info(f"SMS sent via direct HTTP to {phone}: {response}")
                    return response
                except Exception as e2:
                    logger.error(f"Both SDK and direct HTTP failed: sdk={last_error}, direct={e2}")
                    raise last_error
            logger.error(f"SMS send failed (sandbox): direct HTTP and SDK both failed: {last_error}")
            raise last_error
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            raise


# Global service instance (lazy initialization)
_at_service_instance = None


def get_at_service() -> ATService:
    """Get or create the global AT service instance."""
    global _at_service_instance
    if _at_service_instance is None:
        try:
            _at_service_instance = ATService()
        except Exception as e:
            logger.warning(f"AT Service initialization failed (will retry on next call): {e}")
            # Return a mock service that logs instead of failing
            class MockATService:
                def send_sms(self, phone: str, message: str, sender_id: str | None = None) -> dict:
                    logger.warning(f"[MOCK] Would send SMS to {phone} from {sender_id or 'default'}: {message[:50]}...")
                    return {"status": "mocked", "message": "AT Service not initialized"}
            _at_service_instance = MockATService()  # Create instance
    return _at_service_instance


# For backward compatibility, create a property-like accessor
class ATServiceProxy:
    """Proxy class to allow at_service.send_sms() syntax."""
    
    def send_sms(self, phone: str, message: str, sender_id: str | None = None) -> dict:
        """Send SMS using the global service instance."""
        return get_at_service().send_sms(phone, message, sender_id=sender_id)


at_service = ATServiceProxy()
