#!/usr/bin/env python3
"""
Test script for organization validation functionality.
This script demonstrates the validation features and can be used for testing.
"""

import sys
import os
import json

# Add the parent directory to Python path to import validators
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from validators.organization_validator import OrganizationValidator, OrganizationValidationError


def test_validation():
    """Test organization validation with various scenarios."""
    
    print("=" * 60)
    print("ORGANIZATION VALIDATION TESTING")
    print("=" * 60)
    
    # Test Case 1: Valid complete data
    print("\n1. Testing valid complete organization data:")
    valid_data = {
        'company_name': 'Acme Corporation',
        'address_1': '123 Business Street',
        'address_2': 'Suite 100',
        'city_town': 'Business City',
        'state': 'California',
        'zip': '90210',
        'country': 'United States',
        'email': 'contact@acme.com',
        'phone_number': '+1 (555) 123-4567'
    }
    
    try:
        validated = OrganizationValidator.validate_for_create(valid_data)
        print("✅ PASSED: Valid data accepted")
        print(f"   Validated data: {json.dumps(validated, indent=4)}")
    except OrganizationValidationError as e:
        print("❌ FAILED: Valid data rejected")
        print(f"   Errors: {json.dumps(e.errors, indent=4)}")
    
    # Test Case 2: Missing required fields
    print("\n2. Testing data with missing required fields:")
    incomplete_data = {
        'company_name': 'Test Corp',
        'email': 'test@example.com'
        # Missing: address_1, state, zip, country, phone_number
    }
    
    try:
        validated = OrganizationValidator.validate_for_create(incomplete_data)
        print("❌ FAILED: Incomplete data was accepted")
    except OrganizationValidationError as e:
        print("✅ PASSED: Incomplete data properly rejected")
        print(f"   Missing fields detected: {list(e.errors.keys())}")
    
    # Test Case 3: Invalid email format
    print("\n3. Testing invalid email format:")
    invalid_email_data = {
        'company_name': 'Test Corp',
        'address_1': '123 Main St',
        'state': 'CA',
        'zip': '90210',
        'country': 'US',
        'email': 'invalid-email',
        'phone_number': '555-123-4567'
    }
    
    try:
        validated = OrganizationValidator.validate_for_create(invalid_email_data)
        print("❌ FAILED: Invalid email was accepted")
    except OrganizationValidationError as e:
        print("✅ PASSED: Invalid email properly rejected")
        if 'email' in e.errors:
            print(f"   Email error: {e.errors['email']}")
    
    # Test Case 4: Invalid phone number
    print("\n4. Testing invalid phone number:")
    invalid_phone_data = {
        'company_name': 'Test Corp',
        'address_1': '123 Main St', 
        'state': 'CA',
        'zip': '90210',
        'country': 'US',
        'email': 'test@example.com',
        'phone_number': '123'  # Too short
    }
    
    try:
        validated = OrganizationValidator.validate_for_create(invalid_phone_data)
        print("❌ FAILED: Invalid phone number was accepted")
    except OrganizationValidationError as e:
        print("✅ PASSED: Invalid phone number properly rejected")
        if 'phone_number' in e.errors:
            print(f"   Phone error: {e.errors['phone_number']}")
    
    # Test Case 5: Update validation (partial data allowed)
    print("\n5. Testing update validation (partial data):")
    update_data = {
        'company_name': 'Updated Corp Name',
        'email': 'updated@example.com'
        # Only updating some fields
    }
    
    try:
        validated = OrganizationValidator.validate_for_update(update_data)
        print("✅ PASSED: Partial update data accepted")
        print(f"   Updated fields: {list(validated.keys())}")
    except OrganizationValidationError as e:
        print("❌ FAILED: Valid update data was rejected")
        print(f"   Errors: {json.dumps(e.errors, indent=4)}")
    
    # Test Case 6: Field length validation
    print("\n6. Testing field length validation:")
    too_long_data = {
        'company_name': 'A' * 300,  # Too long (max 255)
        'address_1': '123 Main St',
        'state': 'CA', 
        'zip': '90210',
        'country': 'US',
        'email': 'test@example.com',
        'phone_number': '555-123-4567'
    }
    
    try:
        validated = OrganizationValidator.validate_for_create(too_long_data)
        print("❌ FAILED: Overly long field was accepted")
    except OrganizationValidationError as e:
        print("✅ PASSED: Overly long field properly rejected")
        if 'company_name' in e.errors:
            print(f"   Length error: {e.errors['company_name']}")
    
    print("\n" + "=" * 60)
    print("VALIDATION TESTING COMPLETE")
    print("=" * 60)


def show_validation_schema():
    """Display the validation schema for reference."""
    print("\n" + "=" * 60)
    print("ORGANIZATION VALIDATION SCHEMA")
    print("=" * 60)
    
    schema = OrganizationValidator.get_validation_schema()
    print("\nField Requirements:")
    for field, constraints in schema['fields'].items():
        required = "REQUIRED" if constraints['required'] else "OPTIONAL"
        max_len = constraints['max_length']
        print(f"  {field:15} | {required:8} | Max Length: {max_len}")
    
    print(f"\nEmail Pattern: {schema['patterns']['email']}")
    print(f"Phone Patterns: {len(schema['patterns']['phone'])} patterns supported")
    print(f"ZIP Patterns: {len(schema['patterns']['zip_patterns'])} country formats supported")


if __name__ == "__main__":
    test_validation()
    show_validation_schema()