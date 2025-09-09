"""
Organization validation utilities following best practices.
Provides comprehensive validation for organization data including field formats,
business rules, and database constraints.
"""

import re
from typing import Dict, List, Optional, Any
# Remove pydantic dependency - we'll handle validation independently


class OrganizationValidationError(Exception):
    """Custom exception for organization validation errors."""
    
    def __init__(self, errors: Dict[str, List[str]]):
        self.errors = errors
        self.message = "Organization validation failed"
        super().__init__(self.message)


class OrganizationValidator:
    """
    Comprehensive validation utility for organization data.
    Follows database schema constraints and business rules.
    """
    
    # Email validation pattern (RFC 5322 compliant)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Phone number patterns (supports international formats)
    PHONE_PATTERNS = [
        re.compile(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'),  # US format
        re.compile(r'^\+?[1-9]\d{6,14}$'),  # International E.164 format (min 7 digits)
        re.compile(r'^[\+]?[1-9][\d\s\-\(\)]{6,18}$'),  # General international format
    ]
    
    # ZIP code patterns for common countries
    ZIP_PATTERNS = {
        'US': re.compile(r'^\d{5}(-\d{4})?$'),
        'CA': re.compile(r'^[A-Za-z]\d[A-Za-z][\s\-]?\d[A-Za-z]\d$'),
        'UK': re.compile(r'^[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}$'),
        'generic': re.compile(r'^[A-Za-z0-9\s\-]{3,10}$'),
    }
    
    # Field length constraints based on database schema
    FIELD_CONSTRAINTS = {
        'company_name': {'max_length': 255, 'required': True},
        'address_1': {'max_length': 255, 'required': True},
        'address_2': {'max_length': 255, 'required': False},
        'city_town': {'max_length': 100, 'required': True},
        'state': {'max_length': 100, 'required': True},
        'zip': {'max_length': 20, 'required': True},
        'country': {'max_length': 100, 'required': True},
        'email': {'max_length': 255, 'required': True},
        'phone_number': {'max_length': 50, 'required': True},
    }
    
    @classmethod
    def validate_organization_data(cls, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """
        Validate organization data according to database schema and business rules.
        
        Args:
            data: Organization data to validate
            is_update: If True, performs update validation (allows partial data)
            
        Returns:
            Cleaned and validated data
            
        Raises:
            OrganizationValidationError: If validation fails
        """
        errors = {}
        cleaned_data = {}
        
        # Validate each field
        for field_name, constraints in cls.FIELD_CONSTRAINTS.items():
            value = data.get(field_name)
            
            # Check required fields for create operations
            if not is_update and constraints['required'] and not value:
                errors.setdefault(field_name, []).append(f"{field_name} is required.")
                continue
            
            # Skip validation for empty optional fields in updates
            if is_update and not value and not constraints['required']:
                continue
                
            # Skip validation for empty fields that aren't required
            if not value and not constraints['required']:
                cleaned_data[field_name] = None
                continue
            
            # Validate field if value exists
            if value:
                field_errors = cls._validate_field(field_name, value, constraints)
                if field_errors:
                    errors[field_name] = field_errors
                else:
                    cleaned_data[field_name] = cls._clean_field(field_name, value)
        
        # Business rule validations
        business_errors = cls._validate_business_rules(cleaned_data, is_update)
        if business_errors:
            errors.update(business_errors)
        
        if errors:
            raise OrganizationValidationError(errors)
        
        return cleaned_data
    
    @classmethod
    def _validate_field(cls, field_name: str, value: Any, constraints: Dict) -> List[str]:
        """Validate individual field according to its constraints."""
        errors = []
        
        # Convert to string and strip whitespace
        if not isinstance(value, str):
            value = str(value)
        value = value.strip()
        
        # Check if empty after stripping
        if not value and constraints['required']:
            errors.append(f"{field_name} cannot be empty.")
            return errors
        
        # Length validation
        if len(value) > constraints['max_length']:
            errors.append(f"{field_name} must be {constraints['max_length']} characters or less.")
        
        # Field-specific validation
        if field_name == 'email':
            if not cls.EMAIL_PATTERN.match(value):
                errors.append("Please enter a valid email address.")
        
        elif field_name == 'phone_number':
            # Clean the phone number for pattern matching
            clean_phone = value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if len(clean_phone) < 7:
                errors.append("Phone number must have at least 7 digits.")
            elif not any(pattern.match(value) or pattern.match(clean_phone) for pattern in cls.PHONE_PATTERNS):
                errors.append("Please enter a valid phone number.")
        
        elif field_name == 'zip':
            # Try to match common ZIP patterns
            if not any(pattern.match(value) for pattern in cls.ZIP_PATTERNS.values()):
                errors.append("Please enter a valid ZIP/postal code.")
        
        elif field_name == 'company_name':
            if len(value) < 2:
                errors.append("Company name must be at least 2 characters long.")
        
        elif field_name == 'state':
            if len(value) < 2:
                errors.append("State must be at least 2 characters long.")
        
        elif field_name == 'country':
            if len(value) < 2:
                errors.append("Country must be at least 2 characters long.")
        
        return errors
    
    @classmethod
    def _clean_field(cls, field_name: str, value: str) -> str:
        """Clean and normalize field values."""
        value = value.strip()
        
        # Normalize email to lowercase
        if field_name == 'email':
            value = value.lower()
        
        # Normalize country and state to title case
        elif field_name in ['country', 'state', 'city_town']:
            value = value.title()
        
        # Clean phone number formatting
        elif field_name == 'phone_number':
            # Keep original formatting but remove excessive whitespace
            value = ' '.join(value.split())
        
        return value
    
    @classmethod
    def _validate_business_rules(cls, data: Dict[str, Any], is_update: bool) -> Dict[str, List[str]]:
        """Validate business rules that span multiple fields."""
        errors = {}
        
        # Example: If US country, validate state and ZIP format
        country = data.get('country', '').upper() if data.get('country') else None
        zip_code = data.get('zip')
        
        if country == 'UNITED STATES' or country == 'US' or country == 'USA':
            if zip_code and not cls.ZIP_PATTERNS['US'].match(zip_code):
                errors.setdefault('zip', []).append("Please enter a valid US ZIP code (e.g., 12345 or 12345-6789).")
        
        elif country == 'CANADA' or country == 'CA':
            if zip_code and not cls.ZIP_PATTERNS['CA'].match(zip_code):
                errors.setdefault('zip', []).append("Please enter a valid Canadian postal code (e.g., A1B 2C3).")
        
        elif country == 'UNITED KINGDOM' or country == 'UK' or country == 'GB':
            if zip_code and not cls.ZIP_PATTERNS['UK'].match(zip_code):
                errors.setdefault('zip', []).append("Please enter a valid UK postal code (e.g., SW1A 1AA).")
        
        return errors
    
    @classmethod
    def validate_for_create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for organization creation."""
        return cls.validate_organization_data(data, is_update=False)
    
    @classmethod
    def validate_for_update(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for organization update."""
        return cls.validate_organization_data(data, is_update=True)
    
    @classmethod
    def get_validation_schema(cls) -> Dict[str, Dict[str, Any]]:
        """Get validation schema for frontend consumption."""
        return {
            'fields': cls.FIELD_CONSTRAINTS,
            'patterns': {
                'email': cls.EMAIL_PATTERN.pattern,
                'phone': [pattern.pattern for pattern in cls.PHONE_PATTERNS],
                'zip_patterns': {k: v.pattern for k, v in cls.ZIP_PATTERNS.items()}
            }
        }