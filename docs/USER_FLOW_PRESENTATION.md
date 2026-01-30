# PriceChekRider – User Flow (Presentation)

**USSD + SMS retail price comparison and delivery for the Kenyan market.**

---

## Overview

| Channel | Role |
|--------|------|
| **USSD** | Onboarding: welcome menu, city selection, then handoff to SMS |
| **SMS** | Two-way: location, product search, results, order & delivery |

**One-line pitch:** Dial a shortcode → get an SMS → reply with location and products → receive cheapest prices → reply ORDER for delivery.

---

## Step-by-Step User Flow

### 1. User dials USSD

**Action:** Customer dials `*384*XXXXX#` (your USSD shortcode).

**Screen 1 – Welcome**
```
Welcome to PriceChekRider!
1. Compare Prices
2. Order Delivery
3. Help
4. Exit
```

**User chooses:** `1` (Compare Prices)

---

### 2. City code (USSD)

**Screen 2**
```
Enter your city code (e.g., NAI for Nairobi):
```

**User enters:** `NAI`

**Screen 3 – Handoff to SMS**
```
END We have noted your city.
We are sending you an SMS. Please reply with your location (e.g. NAI-Kileleshwa).
```

**System:** Sends first SMS to the same phone number.

---

### 3. First SMS – Location (SMS)

**SMS to user:**
```
Welcome to PriceChekRider! Reply with:
LOCATION-FORMAT: CityCode-Area
Example: NAI-Kileleshwa or NAI-Kasarani
```

**User replies:** `NAI-Kileleshwa`

**System:** Saves location, asks for search type.

---

### 4. Search type (SMS)

**SMS to user:**
```
Search for:
1. Single product
2. Multiple products

Reply 1 or 2
```

**User replies:** `2` (Multiple products)

---

### 5. Product list (SMS)

**SMS to user:**
```
List products (comma separated):
Example: Sugar 2kg, Rice 1kg, Cooking Oil
```

**User replies:** `Sugar 2kg, Rice 1kg, Milk 500ml`

**System:** Fetches prices (mock scraper), builds results.

---

### 6. Results (SMS)

**SMS to user:**
```
PriceChekRider Results:

*Sugar 2kg*: Cheapest: KES 189 @ Naivas Kileleshwa, Average: KES 195
*Rice 1kg*: Cheapest: KES 125 @ Quickmart Kasarani, Average: KES 132
*Milk 500ml*: Cheapest: KES 58 @ Naivas Kileleshwa, Average: KES 62

Total Cheapest: KES 372
Delivery available for KES 150

Reply ORDER to confirm delivery or NEW to search again
```

---

### 7. Order (SMS)

**User replies:** `ORDER`

**SMS to user:**
```
Order confirmed! Estimated delivery: 45 mins.
Rider John (0722 XXX XXX) will contact you.
Track at: https://pricechekrider.co.ke/track/123

Reply CANCEL within 5 mins to cancel.
```

---

### 8. Optional: Cancel or new search (SMS)

| User reply | System response |
|------------|------------------|
| `CANCEL` | "Order cancelled. Reply with products to search again or dial *384# to start over." |
| `NEW` | "List products (comma separated): Example: Sugar 2kg, Rice 1kg..." (new search) |

---

## Flow Diagram (Simplified)

```
[User]  Dial *384*XXXXX#
   ↓
[USSD]  Welcome → 1. Compare Prices → Enter city (NAI)
   ↓
[SMS]   "Reply with: CityCode-Area"  ←  User: NAI-Kileleshwa
   ↓
[SMS]   "1. Single / 2. Multiple"    ←  User: 2
   ↓
[SMS]   "List products (comma sep)"  ←  User: Sugar, Rice, Milk
   ↓
[SMS]   Results (cheapest + average + total + delivery fee)
   ↓
[SMS]   "Reply ORDER or NEW"         ←  User: ORDER
   ↓
[SMS]   Order confirmed + rider + track URL + CANCEL option
```

---

## Channels Summary

| Phase | Channel | User action | System response |
|-------|---------|-------------|-----------------|
| Onboarding | USSD | Dial, choose 1, enter NAI | Welcome menu, city prompt, END + “we’re sending SMS” |
| Location | SMS | Reply NAI-Kileleshwa | Ask single vs multiple |
| Search | SMS | Reply 1 or 2 | Ask for product list |
| Products | SMS | Reply Sugar, Rice, Milk | Price results + ORDER/NEW |
| Delivery | SMS | Reply ORDER | Confirmation + rider + track + CANCEL |
| Control | SMS | Reply CANCEL or NEW | Cancel ack or new search |

---

## Demo Talking Points

1. **No app install** – USSD + SMS work on any feature phone.
2. **Clear path** – USSD gets city, SMS does the rest (location → products → order).
3. **Transparent pricing** – Cheapest per item, average, total, and delivery fee in one message.
4. **Two-way SMS** – User can ORDER, CANCEL, or start a NEW search without dialing again.
5. **Delivery** – Confirmation with rider contact and track link; CANCEL within 5 minutes.

---

## Technical Callbacks (for reference)

| Event | Method | Endpoint | Purpose |
|-------|--------|----------|---------|
| USSD session | POST | `/` or `/ussd/at` | Menu & city; trigger first SMS |
| Incoming SMS | POST | `/` or `/incoming-sms` | Location, products, ORDER, CANCEL, NEW |

*In sandbox, set both USSD and SMS callback URLs to your public base URL (e.g. ngrok).*
