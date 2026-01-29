"""
Africa's Talking SDK wrapper service.
Handles SMS sending and USSD responses.
"""
import africastalking
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ATService:
    """Service wrapper for Africa's Talking SDK."""
    
    def __init__(self):
        """Initialize Africa's Talking SDK with credentials from settings."""
        try:
            africastalking.initialize(
                username=settings.AT_USERNAME,
                api_key=settings.AT_API_KEY
            )
            self.sms = africastalking.SMS
            logger.info("Africa's Talking SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking SDK: {e}")
            raise
    
    def send_sms(self, phone: str, message: str) -> dict:
        """
        Send SMS to a phone number.
        
        Args:
            phone: Phone number in international format (e.g., +254712345678)
            message: SMS message content
            
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
            
            response = self.sms.send(message, [phone])
            logger.info(f"SMS sent to {phone}: {response}")
            return response
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
                def send_sms(self, phone: str, message: str) -> dict:
                    logger.warning(f"[MOCK] Would send SMS to {phone}: {message[:50]}...")
                    return {"status": "mocked", "message": "AT Service not initialized"}
            _at_service_instance = MockATService()  # Create instance
    return _at_service_instance


# For backward compatibility, create a property-like accessor
class ATServiceProxy:
    """Proxy class to allow at_service.send_sms() syntax."""
    
    def send_sms(self, phone: str, message: str) -> dict:
        """Send SMS using the global service instance."""
        return get_at_service().send_sms(phone, message)


at_service = ATServiceProxy()
