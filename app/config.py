from dataclasses import dataclass
from typing import Dict, Any
from decimal import Decimal


@dataclass
class ServiceCategory:
    id: str
    name: str
    description: str


@dataclass
class TaxConfig:
    rate: Decimal
    description: str


class AppConfig:
    # Application specific settings
    APPOINTMENT_DURATION = 30  # Default appointment duration in minutes
    MAX_DAILY_APPOINTMENTS = 50
    BUSINESS_HOURS = {
        'Monday': ('9:00', '18:00'),
        'Tuesday': ('9:00', '18:00'),
        'Wednesday': ('9:00', '18:00'),
        'Thursday': ('9:00', '18:00'),
        'Friday': ('9:00', '18:00'),
        'Saturday': ('10:00', '16:00'),
        'Sunday': ('Closed', 'Closed')
    }

    # Service categories
    SERVICE_CATEGORIES = [
        ServiceCategory('anti-aging', 'Anti-Aging Treatments', 'Advanced anti-aging procedures'),
        ServiceCategory('facial', 'Facial Treatments', 'Customized facial services'),
        ServiceCategory('body', 'Body Treatments', 'Professional body treatments'),
        ServiceCategory('skin', 'Skin Care', 'Specialized skin care services')
    ]

    # Tax configurations
    TAX_CONFIGS = {
        'default': TaxConfig(Decimal('0.08'), 'Standard Tax'),
        'service': TaxConfig(Decimal('0.06'), 'Service Tax'),
        'product': TaxConfig(Decimal('0.08'), 'Product Tax')
    }

    # Payment methods
    PAYMENT_METHODS = [
        'Cash',
        'Credit Card',
        'Debit Card',
        'Gift Card',
        'Bank Transfer'
    ]

    # Discount types
    DISCOUNT_TYPES = {
        'percentage': 'Percentage off',
        'fixed': 'Fixed amount off',
        'bogo': 'Buy one get one free',
        'package': 'Package deal'
    }

    # Notification settings
    NOTIFICATION_SETTINGS = {
        'appointment_reminder': 24,  # hours before
        'follow_up': 48,  # hours after
        'birthday_offer': 7,  # days before
    }

    # Service duration intervals (in minutes)
    SERVICE_DURATIONS = [15, 30, 45, 60, 90, 120]

    @staticmethod
    def get_tax_rate(category: str) -> Decimal:
        """Get tax rate for a specific category"""
        return AppConfig.TAX_CONFIGS.get(
            category,
            AppConfig.TAX_CONFIGS['default']
        ).rate

    @staticmethod
    def validate_business_hours(time: str, day: str) -> bool:
        """Validate if given time is within business hours"""
        if day not in AppConfig.BUSINESS_HOURS:
            return False
        open_time, close_time = AppConfig.BUSINESS_HOURS[day]
        if open_time == 'Closed':
            return False
        return open_time <= time <= close_time


# Example usage in your application:
"""
from app.utils.config import AppConfig
from config import Config

# Using root config for paths and environment settings
Config.ensure_directories()
db_path = Config.DATABASE_PATH

# Using app config for business logic
if AppConfig.validate_business_hours('14:30', 'Monday'):
    tax_rate = AppConfig.get_tax_rate('service')
    # Process the service...
"""