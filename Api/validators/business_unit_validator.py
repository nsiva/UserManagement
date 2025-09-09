"""
Business Unit validation utilities following best practices.
Provides comprehensive validation for business unit data including field formats,
business rules, and organizational constraints.
"""

import re
from typing import Dict, List, Optional, Any
from uuid import UUID


class BusinessUnitValidationError(Exception):
    """Custom exception for business unit validation errors."""
    
    def __init__(self, errors: Dict[str, List[str]]):
        self.errors = errors
        self.message = "Business unit validation failed"
        super().__init__(self.message)


class BusinessUnitValidator:
    """
    Comprehensive validation utility for business unit data.
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
    
    # Code validation pattern (alphanumeric, underscore, hyphen)
    CODE_PATTERN = re.compile(r'^[A-Z0-9_-]+$')
    
    # Field length constraints based on database schema
    FIELD_CONSTRAINTS = {
        'name': {'max_length': 255, 'min_length': 2, 'required': True},
        'description': {'max_length': 1000, 'required': False},
        'code': {'max_length': 50, 'min_length': 2, 'required': False},
        'location': {'max_length': 255, 'required': False},
        'country': {'max_length': 100, 'min_length': 2, 'required': False},
        'region': {'max_length': 100, 'required': False},
        'email': {'max_length': 255, 'required': False},
        'phone_number': {'max_length': 50, 'required': False},
        'organization_id': {'required': True},
        'parent_unit_id': {'required': False},
        'manager_id': {'required': False},
        'is_active': {'required': False},
    }
    
    @classmethod
    def validate_business_unit_data(cls, data: Dict[str, Any], is_update: bool = False, 
                                  organization_context: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Validate business unit data according to database schema and business rules.
        
        Args:
            data: Business unit data to validate
            is_update: If True, performs update validation (allows partial data)
            organization_context: Organization ID for context validation
            
        Returns:
            Cleaned and validated data
            
        Raises:
            BusinessUnitValidationError: If validation fails
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
            if value is not None:
                field_errors = cls._validate_field(field_name, value, constraints)
                if field_errors:
                    errors[field_name] = field_errors
                else:
                    cleaned_data[field_name] = cls._clean_field(field_name, value)
        
        # Business rule validations
        business_errors = cls._validate_business_rules(cleaned_data, is_update, organization_context)
        if business_errors:
            errors.update(business_errors)
        
        if errors:
            raise BusinessUnitValidationError(errors)
        
        return cleaned_data
    
    @classmethod
    def _validate_field(cls, field_name: str, value: Any, constraints: Dict) -> List[str]:
        """Validate individual field according to its constraints."""
        errors = []
        
        # Handle UUID fields
        if field_name in ['organization_id', 'parent_unit_id', 'manager_id']:
            if isinstance(value, str):
                try:
                    UUID(value)
                except ValueError:
                    errors.append(f"Invalid {field_name} format.")
            return errors
        
        # Handle boolean fields
        if field_name == 'is_active':
            if not isinstance(value, bool):
                errors.append("is_active must be true or false.")
            return errors
        
        # Convert to string and strip whitespace for text fields
        if not isinstance(value, str):
            value = str(value)
        value = value.strip()
        
        # Check if empty after stripping
        if not value and constraints['required']:
            errors.append(f"{field_name} cannot be empty.")
            return errors
        
        # Length validation
        if constraints.get('max_length') and len(value) > constraints['max_length']:
            errors.append(f"{field_name} must be {constraints['max_length']} characters or less.")
        
        if constraints.get('min_length') and len(value) < constraints['min_length']:
            errors.append(f"{field_name} must be at least {constraints['min_length']} characters long.")
        
        # Field-specific validation
        if field_name == 'email' and value:
            if not cls.EMAIL_PATTERN.match(value):
                errors.append("Please enter a valid email address.")
        
        elif field_name == 'phone_number' and value:
            # Clean the phone number for pattern matching
            clean_phone = value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if len(clean_phone) < 7:
                errors.append("Phone number must have at least 7 digits.")
            elif not any(pattern.match(value) or pattern.match(clean_phone) for pattern in cls.PHONE_PATTERNS):
                errors.append("Please enter a valid phone number.")
        
        elif field_name == 'code' and value:
            if not cls.CODE_PATTERN.match(value.upper()):
                errors.append("Code must contain only uppercase letters, numbers, underscores, and hyphens.")
        
        elif field_name == 'name' and value:
            if len(value) < 2:
                errors.append("Business unit name must be at least 2 characters long.")
        
        return errors
    
    @classmethod
    def _clean_field(cls, field_name: str, value: Any) -> Any:
        """Clean and normalize field values."""
        # Handle UUID fields
        if field_name in ['organization_id', 'parent_unit_id', 'manager_id']:
            if isinstance(value, str):
                return UUID(value)
            return value
        
        # Handle boolean fields
        if field_name == 'is_active':
            return bool(value)
        
        # Handle text fields
        if isinstance(value, str):
            value = value.strip()
            
            # Normalize email to lowercase
            if field_name == 'email':
                value = value.lower()
            
            # Normalize code to uppercase
            elif field_name == 'code':
                value = value.upper()
            
            # Normalize country and region to title case
            elif field_name in ['country', 'region']:
                value = value.title()
            
            # Clean phone number formatting
            elif field_name == 'phone_number':
                # Keep original formatting but remove excessive whitespace
                value = ' '.join(value.split())
        
        return value
    
    @classmethod
    def _validate_business_rules(cls, data: Dict[str, Any], is_update: bool, 
                               organization_context: Optional[UUID]) -> Dict[str, List[str]]:
        """Validate business rules that span multiple fields."""
        errors = {}
        
        # Validate organization context if provided
        if organization_context and 'organization_id' in data:
            if data['organization_id'] != organization_context:
                errors.setdefault('organization_id', []).append(
                    "You can only create business units within your organization."
                )
        
        # Validate parent unit relationship
        if 'parent_unit_id' in data and data['parent_unit_id']:
            # Note: Additional validation for parent-child organization consistency
            # will be handled at the database/repository level
            pass
        
        return errors
    
    @classmethod
    def validate_for_create(cls, data: Dict[str, Any], organization_context: Optional[UUID] = None) -> Dict[str, Any]:
        """Validate data for business unit creation."""
        return cls.validate_business_unit_data(data, is_update=False, organization_context=organization_context)
    
    @classmethod
    def validate_for_update(cls, data: Dict[str, Any], organization_context: Optional[UUID] = None) -> Dict[str, Any]:
        """Validate data for business unit update."""
        return cls.validate_business_unit_data(data, is_update=True, organization_context=organization_context)
    
    @classmethod
    def get_validation_schema(cls) -> Dict[str, Dict[str, Any]]:
        """Get validation schema for frontend consumption."""
        return {
            'fields': cls.FIELD_CONSTRAINTS,
            'patterns': {
                'email': cls.EMAIL_PATTERN.pattern,
                'phone': [pattern.pattern for pattern in cls.PHONE_PATTERNS],
                'code': cls.CODE_PATTERN.pattern
            }
        }