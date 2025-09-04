import { Injectable } from '@angular/core';
import { AbstractControl, ValidationErrors } from '@angular/forms';

export interface PasswordRequirements {
  minLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
  hasSpecialChar: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class PasswordValidationService {

  // Password validation requirements
  static validatePassword(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    
    if (!value) {
      return null; // Let required validator handle empty values
    }

    const requirements = PasswordValidationService.getPasswordRequirements(value);
    const allRequirementsMet = Object.values(requirements).every(req => req);
    
    if (!allRequirementsMet) {
      return { 
        passwordRequirements: { 
          value: value,
          requirements: requirements 
        } 
      };
    }

    return null;
  }

  // Get password requirements status
  static getPasswordRequirements(password: string): PasswordRequirements {
    return {
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
  }

  // Check if all requirements are met
  static areAllRequirementsMet(password: string): boolean {
    const requirements = this.getPasswordRequirements(password);
    return Object.values(requirements).every(req => req);
  }

  // Get the validation error message
  static getValidationMessage(): string {
    return 'Password must meet all the requirements below';
  }
}