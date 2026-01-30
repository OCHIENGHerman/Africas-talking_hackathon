"""
Mock price scraper for hackathon purposes.
Returns hardcoded Kenyan retail prices without actual web scraping.
"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class MockScraper:
    """
    Mock scraper that returns hardcoded price data for Kenyan retailers.
    Designed for fast USSD/SMS responses without real web scraping delays.
    """
    
    # Mock price database (Kenyan context). Spec: store with area e.g. "Naivas Kileleshwa", average price
    MOCK_PRICES = {
        "sugar": [
            {"shop": "Naivas", "price": 230, "rider_time": "5 min", "store_location": "Naivas Kileleshwa", "average": 240},
            {"shop": "Quickmart", "price": 245, "rider_time": "8 min", "store_location": "QuickMart Kileleshwa", "average": 255},
            {"shop": "Tuskys", "price": 250, "rider_time": "10 min", "store_location": "Tuskys Kileleshwa", "average": 260},
            {"shop": "Carrefour", "price": 235, "rider_time": "12 min", "store_location": "Carrefour Kileleshwa", "average": 245},
        ],
        "milk": [
            {"shop": "Naivas", "price": 120, "rider_time": "5 min", "store_location": "Naivas Kileleshwa", "average": 125},
            {"shop": "Quickmart", "price": 125, "rider_time": "8 min", "store_location": "QuickMart Kileleshwa", "average": 130},
            {"shop": "Tuskys", "price": 130, "rider_time": "10 min", "store_location": "Tuskys Kileleshwa", "average": 132},
            {"shop": "Carrefour", "price": 118, "rider_time": "12 min", "store_location": "Carrefour Kileleshwa", "average": 122},
        ],
        "bread": [
            {"shop": "Naivas", "price": 55, "rider_time": "5 min", "store_location": "Naivas Kileleshwa", "average": 58},
            {"shop": "Quickmart", "price": 60, "rider_time": "8 min", "store_location": "QuickMart Kileleshwa", "average": 62},
            {"shop": "Tuskys", "price": 58, "rider_time": "10 min", "store_location": "Tuskys Kileleshwa", "average": 60},
            {"shop": "Carrefour", "price": 57, "rider_time": "12 min", "store_location": "Carrefour Kileleshwa", "average": 59},
        ],
        "rice": [
            {"shop": "Naivas", "price": 180, "rider_time": "5 min", "store_location": "Naivas Kileleshwa", "average": 185},
            {"shop": "Quickmart", "price": 185, "rider_time": "8 min", "store_location": "QuickMart Kileleshwa", "average": 190},
            {"shop": "Tuskys", "price": 190, "rider_time": "10 min", "store_location": "Tuskys Kileleshwa", "average": 195},
            {"shop": "Carrefour", "price": 175, "rider_time": "12 min", "store_location": "Carrefour Kileleshwa", "average": 180},
        ],
        "cooking oil": [
            {"shop": "Naivas", "price": 450, "rider_time": "5 min", "store_location": "Naivas Kileleshwa", "average": 460},
            {"shop": "Quickmart", "price": 460, "rider_time": "8 min", "store_location": "QuickMart Kileleshwa", "average": 470},
            {"shop": "Tuskys", "price": 470, "rider_time": "10 min", "store_location": "Tuskys Kileleshwa", "average": 475},
            {"shop": "Carrefour", "price": 445, "rider_time": "12 min", "store_location": "Carrefour Kileleshwa", "average": 455},
        ],
        "tea": [
            {"shop": "Naivas", "price": 95, "rider_time": "5 min", "store_location": "Naivas Kileleshwa", "average": 98},
            {"shop": "Quickmart", "price": 100, "rider_time": "8 min", "store_location": "QuickMart Kileleshwa", "average": 102},
            {"shop": "Tuskys", "price": 98, "rider_time": "10 min", "store_location": "Tuskys Kileleshwa", "average": 100},
            {"shop": "Carrefour", "price": 92, "rider_time": "12 min", "store_location": "Carrefour Kileleshwa", "average": 95},
        ],
    }
    DELIVERY_FEE_KES = 150  # Spec: Delivery available for KES 150
    
    @classmethod
    def get_prices(cls, product_name: str, city: str = None) -> List[Dict[str, any]]:
        """
        Get mock prices for a product.
        
        Args:
            product_name: Name of the product (case-insensitive)
            city: City/location (not used in mock, but kept for API consistency)
            
        Returns:
            List of dictionaries with shop, price, and rider_time
        """
        product_key = product_name.lower().strip()
        
        # Check if product exists in mock data
        if product_key in cls.MOCK_PRICES:
            prices = cls.MOCK_PRICES[product_key].copy()
            logger.info(f"Found mock prices for '{product_name}': {len(prices)} shops")
            return prices
        
        # Default response for unknown products
        logger.warning(f"Product '{product_name}' not found in mock data, returning default")
        return [
            {"shop": "Naivas", "price": 200, "rider_time": "5 min", "store_location": "Naivas", "average": 210},
            {"shop": "Quickmart", "price": 210, "rider_time": "8 min", "store_location": "QuickMart", "average": 215},
            {"shop": "Tuskys", "price": 215, "rider_time": "10 min", "store_location": "Tuskys", "average": 220},
        ]
    
    @classmethod
    def get_prices_for_multiple_products(cls, product_names: List[str], city: str = None) -> Dict[str, List[Dict[str, any]]]:
        """
        Get prices for multiple products at once.
        
        Args:
            product_names: List of product names
            city: City/location
            
        Returns:
            Dictionary mapping product names to their price lists
        """
        result = {}
        for product in product_names:
            result[product] = cls.get_prices(product, city)
        return result
