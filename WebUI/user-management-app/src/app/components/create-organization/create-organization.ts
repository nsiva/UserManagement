import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth';
import { OrganizationService, OrganizationCreate, OrganizationUpdate, Organization } from '../../services/organization';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { AlertComponent, AlertType } from '../../shared/components/alert/alert.component';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';
import { EntityTabsComponent } from '../entity-tabs/entity-tabs.component';

@Component({
  selector: 'app-create-organization',
  standalone: true,
  imports: [FormsModule, CommonModule, ReactiveFormsModule, HeaderComponent, AlertComponent, EntityTabsComponent],
  templateUrl: './create-organization.html',
  styleUrl: './create-organization.scss'
})
export class CreateOrganizationComponent implements OnInit, OnDestroy {
  // Enhanced validator for required text fields with minimum length
  private static requiredTextValidator(minLength: number = 2): (control: AbstractControl) => ValidationErrors | null {
    return (control: AbstractControl): ValidationErrors | null => {
      const value = control.value;
      if (!value || typeof value !== 'string' || value.trim().length === 0) {
        return { required: true };
      }
      if (value.trim().length < minLength) {
        return { minlength: { requiredLength: minLength, actualLength: value.trim().length } };
      }
      return null;
    };
  }

  // Enhanced email validator (required)
  private static emailValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value || typeof value !== 'string' || value.trim().length === 0) {
      return { required: true };
    }
    
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    
    if (!emailPattern.test(value.trim())) {
      return { email: true };
    }
    
    return null;
  }

  // Enhanced phone validator (required)
  private static phoneValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value || typeof value !== 'string' || value.trim().length === 0) {
      return { required: true };
    }
    
    const cleanValue = value.replace(/[\s\-\(\)]/g, '');
    // International phone pattern - more comprehensive
    const phonePattern = /^[\+]?[1-9][\d\s\-\(\)]{6,18}$/;
    
    if (!phonePattern.test(value)) {
      return { phone: true };
    }
    
    if (cleanValue.length < 7 || cleanValue.length > 15) {
      return { phoneLength: true };
    }
    
    return null;
  }

  // ZIP/Postal code validator (required)
  private static zipValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value || typeof value !== 'string' || value.trim().length === 0) {
      return { required: true };
    }
    
    if (value.trim().length < 3 || value.trim().length > 20) {
      return { zipLength: true };
    }
    
    // Basic ZIP pattern - allows international formats
    const zipPattern = /^[A-Za-z0-9\s\-]{3,20}$/;
    if (!zipPattern.test(value.trim())) {
      return { zipFormat: true };
    }
    
    return null;
  }

  // Optional text validator for address fields
  private static optionalTextValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    // Allow empty values for optional fields
    if (!value) {
      return null;
    }
    
    if (typeof value === 'string' && value.trim().length > 0) {
      return null;
    }
    
    return { invalidText: true };
  }

  // Header configuration
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: 'Create Organization',
    showUserMenu: true
  };

  organizationForm: FormGroup;
  isSubmitting = false;
  isEditMode = false;
  organizationId: string | null = null;
  organizationToEdit: Organization | null = null;
  isLoading = false;
  private routeSubscription: Subscription | null = null;
  
  // Functional roles management
  showFunctionalRoles = false;

  // Alert properties
  alertMessage: string | null = null;
  alertType: AlertType = 'info';
  
  // Inline alert properties (for alerts above save buttons)
  inlineAlertMessage: string | null = null;
  inlineAlertType: AlertType = 'info';

  constructor(
    private authService: AuthService,
    private organizationService: OrganizationService,
    private fb: FormBuilder,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.organizationForm = this.fb.group({
      companyName: ['', [CreateOrganizationComponent.requiredTextValidator(2), Validators.maxLength(255)]],
      email: ['', [CreateOrganizationComponent.emailValidator, Validators.maxLength(255)]],
      phoneNumber: ['', [CreateOrganizationComponent.phoneValidator, Validators.maxLength(50)]],
      address1: ['', [CreateOrganizationComponent.requiredTextValidator(5), Validators.maxLength(255)]],
      address2: ['', [CreateOrganizationComponent.optionalTextValidator, Validators.maxLength(255)]],
      cityTown: ['', [CreateOrganizationComponent.requiredTextValidator(2), Validators.maxLength(100)]],
      state: ['', [CreateOrganizationComponent.requiredTextValidator(2), Validators.maxLength(100)]],
      zip: ['', [CreateOrganizationComponent.zipValidator, Validators.maxLength(20)]],
      country: ['', [CreateOrganizationComponent.requiredTextValidator(2), Validators.maxLength(100)]]
    });
  }

  ngOnInit(): void {
    // Ensure authentication token exists before making API calls
    if (!this.authService.getToken()) {
      this.router.navigate(['/login']);
      return;
    }

    // Subscribe to route parameter changes to handle component reuse
    this.routeSubscription = this.route.paramMap.subscribe(params => {
      // Reset form and component state first
      this.resetComponent();
      this.checkMode();
    });
  }

  ngOnDestroy(): void {
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
  }

  checkMode(): void {
    this.organizationId = this.route.snapshot.paramMap.get('id');
    this.isEditMode = !!this.organizationId;
    
    // Update header subtitle based on mode
    this.headerConfig = {
      ...this.headerConfig,
      subtitle: this.isEditMode ? 'Edit Organization' : 'Create Organization'
    };
    
    console.log('CreateOrganizationComponent: checkMode - organizationId:', this.organizationId, 'isEditMode:', this.isEditMode);
    
    if (this.isEditMode && this.organizationId) {
      // Load organization data for editing
      this.loadOrganizationForEdit(this.organizationId);
      // Show functional roles section immediately for edit mode
      this.showFunctionalRoles = true;
    } else {
      // Ensure form is blank for create mode
      this.organizationForm.reset({
        companyName: '',
        email: '',
        phoneNumber: '',
        address1: '',
        address2: '',
        cityTown: '',
        state: '',
        zip: '',
        country: ''
      });
      
      console.log('CreateOrganizationComponent: Create mode - form reset to blank values:', this.organizationForm.value);
    }

    // Show functional roles section for both create and edit modes
    this.showFunctionalRoles = true;

    // Check if user has admin or super_user role
    if (!this.hasAdminOrSuperUserRole()) {
      this.showError('You do not have permission to manage organizations.');
      this.router.navigate(['/admin']);
      return;
    }
  }

  loadOrganizationForEdit(organizationId: string): void {
    this.isLoading = true;
    this.organizationService.getOrganization(organizationId).subscribe({
      next: (organization) => {
        this.organizationToEdit = organization;
        
        // Populate form with organization data
        this.organizationForm.patchValue({
          companyName: organization.company_name || '',
          email: organization.email || '',
          phoneNumber: organization.phone_number || '',
          address1: organization.address_1 || '',
          address2: organization.address_2 || '',
          cityTown: organization.city_town || '',
          state: organization.state || '',
          zip: organization.zip || '',
          country: organization.country || ''
        });
        
        // Clear any previous alert messages
        this.alertMessage = null;
        
        this.isLoading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.isLoading = false;
        console.error('Error loading organization:', err);
        
        // Handle different error scenarios
        if (err.status === 401) {
          this.showError('Authentication failed. Redirecting to login...');
          setTimeout(() => this.router.navigate(['/login']), 2000);
        } else if (err.status === 403) {
          this.showError('Access denied. You may not have permission to view this organization.');
        } else if (err.status === 404) {
          this.showError('Organization not found.');
          setTimeout(() => this.router.navigate(['/admin']), 2000);
        } else {
          this.showError(err.error?.detail || 'Failed to load organization.');
        }
      }
    });
  }

  resetComponent(): void {
    console.log('CreateOrganizationComponent: Resetting component state');
    
    // Reset all component state
    this.alertMessage = null;
    this.isEditMode = false;
    this.organizationId = null;
    this.organizationToEdit = null;
    this.isLoading = false;
    this.isSubmitting = false;
    
    // Reset form
    this.organizationForm.reset();
    this.organizationForm.markAsPristine();
    this.organizationForm.markAsUntouched();
  }

  hasAdminOrSuperUserRole(): boolean {
    const roles = this.authService.getUserRoles();
    return roles.includes('admin') || roles.includes('super_user');
  }

  onSubmit(): void {
    if (this.organizationForm.invalid) {
      const message = 'Please fill in all required fields correctly.';
      this.showError(message);
      this.showInlineError(message);
      this.markFormGroupTouched();
      return;
    }

    if (this.isSubmitting) {
      return;
    }

    this.isSubmitting = true;
    this.alertMessage = null;
    this.inlineAlertMessage = null;

    const formData = this.organizationForm.value;
    const organizationData = {
      company_name: formData.companyName.trim(),
      email: formData.email ? formData.email.trim() : undefined,
      phone_number: formData.phoneNumber ? formData.phoneNumber.trim() : undefined,
      address_1: formData.address1 ? formData.address1.trim() : undefined,
      address_2: formData.address2 ? formData.address2.trim() : undefined,
      city_town: formData.cityTown ? formData.cityTown.trim() : undefined,
      state: formData.state ? formData.state.trim() : undefined,
      zip: formData.zip ? formData.zip.trim() : undefined,
      country: formData.country ? formData.country.trim() : undefined
    };

    if (this.isEditMode && this.organizationId) {
      // Edit mode - update existing organization
      this.organizationService.updateOrganization(this.organizationId, organizationData as OrganizationUpdate).subscribe({
        next: (response) => {
          const message = 'Organization updated successfully!';
          this.showSuccess(message);
          this.showInlineSuccess(message);
          this.isSubmitting = false;
          // Functional roles section already visible in edit mode
        },
        error: (err: HttpErrorResponse) => {
          this.isSubmitting = false;
          let errorMessage = 'Failed to update organization.';
          
          if (err.error?.detail) {
            errorMessage = err.error.detail;
          } else if (err.status === 409) {
            errorMessage = 'An organization with this information already exists.';
          } else if (err.status === 403) {
            errorMessage = 'You do not have permission to update organizations.';
          } else if (err.status === 404) {
            errorMessage = 'Organization not found.';
          }
          
          this.showError(errorMessage);
          this.showInlineError(errorMessage);
          console.error('Error updating organization:', err);
        }
      });
    } else {
      // Create mode - create new organization
      this.organizationService.createOrganization(organizationData as OrganizationCreate).subscribe({
        next: (response) => {
          this.organizationId = response.id; // Set the organization ID for functional roles
          this.organizationToEdit = response;
          this.isEditMode = true; // Switch to edit mode
          const message = 'Organization created successfully! Functional roles are now available for configuration.';
          this.showSuccess(message);
          this.showInlineSuccess(message);
          // Functional roles section is already visible from checkMode()
          this.isSubmitting = false;
        },
        error: (err: HttpErrorResponse) => {
          this.isSubmitting = false;
          let errorMessage = 'Failed to create organization.';
          
          if (err.error?.detail) {
            errorMessage = err.error.detail;
          } else if (err.status === 409) {
            errorMessage = 'An organization with this information already exists.';
          } else if (err.status === 403) {
            errorMessage = 'You do not have permission to create organizations.';
          }
          
          this.showError(errorMessage);
          this.showInlineError(errorMessage);
          console.error('Error creating organization:', err);
        }
      });
    }
  }

  private markFormGroupTouched(): void {
    Object.keys(this.organizationForm.controls).forEach(key => {
      const control = this.organizationForm.get(key);
      control?.markAsTouched();
    });
  }

  showError(message: string): void {
    this.alertMessage = message;
    this.alertType = 'error';
  }

  showSuccess(message: string): void {
    this.alertMessage = message;
    this.alertType = 'success';
  }

  onAlertDismissed(): void {
    this.alertMessage = null;
  }

  // Inline alert methods
  showInlineError(message: string): void {
    this.inlineAlertMessage = message;
    this.inlineAlertType = 'error';
  }

  showInlineSuccess(message: string): void {
    this.inlineAlertMessage = message;
    this.inlineAlertType = 'success';
  }

  onInlineAlertDismissed(): void {
    this.inlineAlertMessage = null;
  }

  // Header event handlers
  navigateToProfile(): void {
    this.router.navigate(['/profile']);
  }

  navigateToAdmin(): void {
    this.router.navigate(['/admin']);
  }

  logout(): void {
    this.authService.logout();
  }

  // Form validation helpers
  isFieldInvalid(fieldName: string): boolean {
    const field = this.organizationForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(fieldName: string): string {
    const field = this.organizationForm.get(fieldName);
    if (field && field.errors) {
      const fieldLabel = this.getFieldLabel(fieldName);
      
      if (field.errors['required']) {
        return this.getRequiredErrorMessage(fieldName);
      }
      if (field.errors['minlength']) {
        const requiredLength = field.errors['minlength'].requiredLength;
        return this.getMinLengthErrorMessage(fieldName, requiredLength);
      }
      if (field.errors['maxlength']) {
        const maxLength = field.errors['maxlength'].requiredLength;
        return `${fieldLabel} must be ${maxLength} characters or less.`;
      }
      if (field.errors['email']) {
        return 'Please enter a valid email address (e.g., contact@company.com).';
      }
      if (field.errors['phone']) {
        return 'Please enter a valid phone number (e.g., +1 555-123-4567).';
      }
      if (field.errors['phoneLength']) {
        return 'Phone number must contain between 7 and 15 digits.';
      }
      if (field.errors['zipLength']) {
        return 'ZIP/postal code must be between 3 and 20 characters.';
      }
      if (field.errors['zipFormat']) {
        return this.getZipErrorMessage();
      }
      if (field.errors['invalidText']) {
        return `Please enter a valid ${fieldLabel.toLowerCase()}.`;
      }
    }
    return '';
  }

  private getRequiredErrorMessage(fieldName: string): string {
    const messages: { [key: string]: string } = {
      companyName: 'Company name is required.',
      email: 'Email address is required for contact purposes.',
      phoneNumber: 'Phone number is required for contact purposes.',
      address1: 'Primary address is required.',
      cityTown: 'City or town is required.',
      state: 'State or province is required.',
      zip: 'ZIP or postal code is required.',
      country: 'Country is required.'
    };
    return messages[fieldName] || `${this.getFieldLabel(fieldName)} is required.`;
  }

  private getMinLengthErrorMessage(fieldName: string, requiredLength: number): string {
    const messages: { [key: string]: string } = {
      companyName: `Company name must be at least ${requiredLength} characters long.`,
      address1: `Address must be at least ${requiredLength} characters long.`,
      cityTown: `City/town must be at least ${requiredLength} characters long.`,
      state: `State/province must be at least ${requiredLength} characters long.`,
      country: `Country must be at least ${requiredLength} characters long.`
    };
    return messages[fieldName] || `${this.getFieldLabel(fieldName)} must be at least ${requiredLength} characters long.`;
  }

  private getZipErrorMessage(): string {
    return 'Please enter a valid ZIP or postal code (e.g., 12345, A1B 2C3, or SW1A 1AA).';
  }

  private getFieldLabel(fieldName: string): string {
    const labels: { [key: string]: string } = {
      companyName: 'Company Name',
      email: 'Email',
      phoneNumber: 'Phone Number',
      address1: 'Address 1',
      address2: 'Address 2',
      cityTown: 'City/Town',
      state: 'State',
      zip: 'ZIP Code',
      country: 'Country'
    };
    return labels[fieldName] || fieldName;
  }

  // Tab and functional roles event handlers
  onTabChanged(tabId: string): void {
    console.log('Tab changed to:', tabId);
  }

  onFunctionalRolesChanged(event: any): void {
    console.log('Functional roles changed:', event);
    if (event.context === 'organization') {
      const message = `Organization functional roles updated: ${event.roles.join(', ')}`;
      this.showSuccess(message);
      this.showInlineSuccess(message);
    }
  }

  finishAndNavigateToAdmin(): void {
    this.router.navigate(['/admin']);
  }
}