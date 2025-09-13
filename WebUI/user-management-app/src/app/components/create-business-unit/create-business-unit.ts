import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth';
import { BusinessUnitService, BusinessUnitCreate, BusinessUnitUpdate, BusinessUnit } from '../../services/business-unit';
import { OrganizationService, Organization } from '../../services/organization';
import { UserService, User } from '../../services/user';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { AlertComponent, AlertType } from '../../shared/components/alert/alert.component';
import { APP_NAME } from '../../shared/constants/app-constants';
import { 
  ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN,
  hasAdminAccess, hasOrganizationAdminAccess, hasAnyAdminAccess 
} from '../../constants/roles';

@Component({
  selector: 'app-create-business-unit',
  standalone: true,
  imports: [FormsModule, CommonModule, ReactiveFormsModule, HeaderComponent, AlertComponent],
  templateUrl: './create-business-unit.html',
  styleUrl: './create-business-unit.scss'
})
export class CreateBusinessUnitComponent implements OnInit, OnDestroy {
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

  // Enhanced email validator (optional)
  private static emailValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value || typeof value !== 'string' || value.trim().length === 0) {
      return null; // Email is optional
    }
    
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    
    if (!emailPattern.test(value.trim())) {
      return { email: true };
    }
    
    return null;
  }

  // Enhanced phone validator (optional)
  private static phoneValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value || typeof value !== 'string' || value.trim().length === 0) {
      return null; // Phone is optional
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

  // Code validator
  private static codeValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value || typeof value !== 'string' || value.trim().length === 0) {
      return null; // Code is optional
    }
    
    if (value.trim().length < 2) {
      return { minlength: { requiredLength: 2, actualLength: value.trim().length } };
    }
    
    const codePattern = /^[A-Z0-9_-]*$/;
    if (!codePattern.test(value.trim())) {
      return { pattern: true };
    }
    
    return null;
  }

  // Header configuration
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: 'Create Business Unit',
    showUserMenu: true
  };

  businessUnitForm: FormGroup;
  isSubmitting = false;
  isEditMode = false;
  businessUnitId: string | null = null;
  businessUnitToEdit: BusinessUnit | null = null;
  isLoading = false;
  private routeSubscription: Subscription | null = null;

  // Available options
  availableOrganizations: Organization[] = [];
  availableParentUnits: BusinessUnit[] = [];
  availableManagers: User[] = [];
  allUsers: User[] = []; // Store all users for filtering
  selectedOrganizationId: string | null = null;

  // Alert properties
  alertMessage: string | null = null;
  alertType: AlertType = 'info';

  // Return navigation parameters
  private returnQueryParams: any = {};

  constructor(
    private authService: AuthService,
    private businessUnitService: BusinessUnitService,
    private organizationService: OrganizationService,
    private userService: UserService,
    private fb: FormBuilder,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.businessUnitForm = this.fb.group({
      organization_id: ['', [Validators.required]],
      name: ['', [CreateBusinessUnitComponent.requiredTextValidator(2), Validators.maxLength(255)]],
      parent_unit_id: [''],
      code: ['', [CreateBusinessUnitComponent.codeValidator, Validators.maxLength(50)]],
      description: ['', [Validators.maxLength(1000)]],
      manager_id: [''],
      location: ['', [Validators.maxLength(255)]],
      country: ['', [Validators.minLength(2), Validators.maxLength(100)]],
      region: ['', [Validators.maxLength(100)]],
      email: ['', [CreateBusinessUnitComponent.emailValidator, Validators.maxLength(255)]],
      phone_number: ['', [CreateBusinessUnitComponent.phoneValidator, Validators.maxLength(50)]],
      is_active: [true, [Validators.required]]
    });
  }

  ngOnInit(): void {
    // Ensure authentication token exists before making API calls
    if (!this.authService.getToken()) {
      this.router.navigate(['/login']);
      return;
    }

    // Capture query parameters for return navigation
    this.captureReturnParameters();

    // Subscribe to route parameter changes to handle component reuse
    this.routeSubscription = this.route.paramMap.subscribe(_ => {
      // Reset form and component state first
      this.resetComponent();
      this.checkMode();
    });

    // Load available data
    this.loadOrganizations();
    this.loadUsers();
  }

  ngOnDestroy(): void {
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
  }

  private captureReturnParameters(): void {
    const queryParams = this.route.snapshot.queryParams;
    
    // Store query parameters for return navigation
    this.returnQueryParams = {};
    if (queryParams['tab']) {
      this.returnQueryParams['tab'] = queryParams['tab'];
    }
    if (queryParams['orgId']) {
      this.returnQueryParams['orgId'] = queryParams['orgId'];
    }
    
    console.log('CreateBusinessUnitComponent: Captured return parameters:', this.returnQueryParams);
  }

  checkMode(): void {
    this.businessUnitId = this.route.snapshot.paramMap.get('id');
    this.isEditMode = !!this.businessUnitId;
    
    // Update header subtitle based on mode
    this.headerConfig = {
      ...this.headerConfig,
      subtitle: this.isEditMode ? 'Edit Business Unit' : 'Create Business Unit'
    };
    
    console.log('CreateBusinessUnitComponent: checkMode - businessUnitId:', this.businessUnitId, 'isEditMode:', this.isEditMode);
    
    if (this.isEditMode && this.businessUnitId) {
      // Load business unit data for editing
      this.loadBusinessUnitForEdit(this.businessUnitId);
    } else {
      // Ensure form is blank for create mode
      this.businessUnitForm.reset({
        organization_id: '',
        name: '',
        parent_unit_id: '',
        code: '',
        description: '',
        manager_id: '',
        location: '',
        country: '',
        region: '',
        email: '',
        phone_number: '',
        is_active: true
      });
      
      console.log('CreateBusinessUnitComponent: Create mode - form reset to blank values:', this.businessUnitForm.value);
    }

    // Check if user has appropriate role
    if (!this.hasBusinessUnitAccess()) {
      this.showError('You do not have permission to manage business units.');
      this.router.navigate(['/admin']);
      return;
    }
  }

  loadBusinessUnitForEdit(businessUnitId: string): void {
    this.isLoading = true;
    this.businessUnitService.getBusinessUnitById(businessUnitId).subscribe({
      next: (businessUnit) => {
        this.businessUnitToEdit = businessUnit;
        this.selectedOrganizationId = businessUnit.organization_id;
        
        // Populate form with business unit data
        this.businessUnitForm.patchValue({
          organization_id: businessUnit.organization_id || '',
          name: businessUnit.name || '',
          parent_unit_id: businessUnit.parent_unit_id || '',
          code: businessUnit.code || '',
          description: businessUnit.description || '',
          manager_id: businessUnit.manager_id || '',
          location: businessUnit.location || '',
          country: businessUnit.country || '',
          region: businessUnit.region || '',
          email: businessUnit.email || '',
          phone_number: businessUnit.phone_number || '',
          is_active: businessUnit.is_active
        });
        
        // Load parent units for the organization
        if (businessUnit.organization_id) {
          this.loadParentUnitsForOrganization(businessUnit.organization_id);
        }
        
        // Ensure firm_admin users can only see their organization in edit mode
        const userRoles = this.authService.getUserRoles();
        if (hasOrganizationAdminAccess(userRoles)) {
          // Organizations will be filtered by the backend to show only user's organization
          console.log('Organization admin editing business unit - organizations will be filtered by backend');
        }
        
        // Clear any previous alert messages
        this.alertMessage = null;
        
        this.isLoading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.isLoading = false;
        console.error('Error loading business unit:', err);
        
        // Handle different error scenarios
        if (err.status === 401) {
          this.showError('Authentication failed. Redirecting to login...');
          setTimeout(() => this.router.navigate(['/login']), 2000);
        } else if (err.status === 403) {
          this.showError('Access denied. You may not have permission to view this business unit.');
        } else if (err.status === 404) {
          this.showError('Business unit not found.');
          setTimeout(() => this.router.navigate(['/admin']), 2000);
        } else {
          this.showError(err.error?.detail || 'Failed to load business unit.');
        }
      }
    });
  }

  loadOrganizations(): void {
    this.organizationService.getOrganizations().subscribe({
      next: (organizations) => {
        this.availableOrganizations = organizations;
        
        // For firm_admin users who should only see their organization, 
        // auto-select it if there's only one organization available
        const userRoles = this.authService.getUserRoles();
        if (hasOrganizationAdminAccess(userRoles) && organizations.length === 1 && !this.isEditMode) {
          this.businessUnitForm.get('organization_id')?.setValue(organizations[0].id);
          this.selectedOrganizationId = organizations[0].id;
          // Load parent units for the auto-selected organization
          this.loadParentUnitsForOrganization(organizations[0].id);
          console.log('Auto-selected organization for firm_admin:', organizations[0].company_name);
        }
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error loading organizations:', err);
        this.showError('Failed to load organizations.');
      }
    });
  }

  loadUsers(): void {
    this.userService.getUsers().subscribe({
      next: (users) => {
        // Store all users for filtering
        this.allUsers = users;
        this.filterManagersByOrganization();
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error loading users:', err);
        this.showError('Failed to load users for manager selection.');
      }
    });
  }

  onOrganizationChange(): void {
    const organizationId = this.businessUnitForm.get('organization_id')?.value;
    this.selectedOrganizationId = organizationId;
    
    if (organizationId) {
      this.loadParentUnitsForOrganization(organizationId);
    } else {
      this.availableParentUnits = [];
    }
    
    // Filter managers by selected organization
    this.filterManagersByOrganization();
    
    // Reset parent unit and manager selections when organization changes
    this.businessUnitForm.get('parent_unit_id')?.setValue('');
    this.businessUnitForm.get('manager_id')?.setValue('');
  }

  loadParentUnitsForOrganization(organizationId: string): void {
    console.log('Loading parent units for organization:', organizationId);
    this.businessUnitService.getBusinessUnits(organizationId).subscribe({
      next: (response) => {
        console.log('Received business units from API:', response.business_units.length, 'units');
        console.log('Organization in response:', response.organization_id);
        
        // Filter out the current business unit being edited to prevent self-parenting
        // and ensure all units belong to the selected organization
        this.availableParentUnits = response.business_units.filter(unit => {
          const isNotSelf = unit.id !== this.businessUnitId;
          const belongsToOrganization = unit.organization_id === organizationId;
          
          console.log(`Unit ${unit.name}: isNotSelf=${isNotSelf}, belongsToOrganization=${belongsToOrganization}, orgId=${unit.organization_id}`);
          
          return isNotSelf && belongsToOrganization;
        });
        
        console.log('Filtered parent units:', this.availableParentUnits.length);
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error loading parent units:', err);
        this.availableParentUnits = [];
      }
    });
  }

  filterManagersByOrganization(): void {
    const selectedOrgId = this.selectedOrganizationId || this.businessUnitForm.get('organization_id')?.value;
    
    if (!selectedOrgId || this.allUsers.length === 0) {
      // If no organization selected or no users loaded, show no managers
      this.availableManagers = [];
      return;
    }

    // Filter users based on create vs edit mode
    if (this.isEditMode && this.businessUnitToEdit) {
      // Edit mode: Show users within the same business unit with business unit admin role
      this.availableManagers = this.allUsers.filter(user => {
        return user.business_unit_id === this.businessUnitToEdit!.id && 
               user.roles.includes(BUSINESS_UNIT_ADMIN);
      });
      console.log('Filtered managers for business unit (edit mode):', this.businessUnitToEdit.id, 'Count:', this.availableManagers.length);
    } else {
      // Create mode: Show users within the selected organization with business unit admin role
      this.availableManagers = this.allUsers.filter(user => {
        return user.organization_id === selectedOrgId && 
               user.roles.includes(BUSINESS_UNIT_ADMIN);
      });
      console.log('Filtered managers for organization (create mode):', selectedOrgId, 'Count:', this.availableManagers.length);
    }
  }

  resetComponent(): void {
    console.log('CreateBusinessUnitComponent: Resetting component state');
    
    // Reset all component state
    this.alertMessage = null;
    this.isEditMode = false;
    this.businessUnitId = null;
    this.businessUnitToEdit = null;
    this.isLoading = false;
    this.isSubmitting = false;
    this.selectedOrganizationId = null;
    this.availableParentUnits = [];
    this.availableManagers = [];
    this.allUsers = [];
    
    // Reset form
    this.businessUnitForm.reset({
      organization_id: '',
      name: '',
      parent_unit_id: '',
      code: '',
      description: '',
      manager_id: '',
      location: '',
      country: '',
      region: '',
      email: '',
      phone_number: '',
      is_active: true
    });
    this.businessUnitForm.markAsPristine();
    this.businessUnitForm.markAsUntouched();
  }

  hasBusinessUnitAccess(): boolean {
    const roles = this.authService.getUserRoles();
    return hasAnyAdminAccess(roles);
  }

  onSubmit(): void {
    if (this.businessUnitForm.invalid) {
      this.showError('Please fill in all required fields correctly.');
      this.markFormGroupTouched();
      return;
    }

    if (this.isSubmitting) {
      return;
    }

    this.isSubmitting = true;
    this.alertMessage = null;

    const formData = this.businessUnitForm.value;
    console.log('=== FORM DATA DEBUG ===');
    console.log('Raw form data:', formData);
    console.log('is_active raw value:', formData.is_active);
    console.log('is_active type:', typeof formData.is_active);
    console.log('is_active === true:', formData.is_active === true);
    console.log('is_active === false:', formData.is_active === false);
    console.log('is_active === null:', formData.is_active === null);
    console.log('is_active === undefined:', formData.is_active === undefined);
    
    const convertedBoolean = this.ensureBoolean(formData.is_active);
    console.log('Converted boolean value:', convertedBoolean);
    console.log('=====================');
    
    const businessUnitData = {
      organization_id: formData.organization_id,
      name: formData.name.trim(),
      parent_unit_id: formData.parent_unit_id || undefined,
      code: formData.code ? formData.code.trim() : undefined,
      description: formData.description ? formData.description.trim() : undefined,
      manager_id: formData.manager_id || undefined,
      location: formData.location ? formData.location.trim() : undefined,
      country: formData.country ? formData.country.trim() : undefined,
      region: formData.region ? formData.region.trim() : undefined,
      email: formData.email ? formData.email.trim() : undefined,
      phone_number: formData.phone_number ? formData.phone_number.trim() : undefined,
      is_active: convertedBoolean
    };
    
    console.log('Final business unit data being sent:', businessUnitData);

    if (this.isEditMode && this.businessUnitId) {
      // Edit mode - update existing business unit
      // Remove organization_id from update data as it shouldn't be changed
      const { organization_id, ...updateData } = businessUnitData;
      
      this.businessUnitService.updateBusinessUnit(this.businessUnitId, updateData as BusinessUnitUpdate).subscribe({
        next: () => {
          this.showSuccess('Business unit updated successfully!');
          setTimeout(() => {
            this.navigateToAdmin();
          }, 2000);
        },
        error: (err: HttpErrorResponse) => {
          this.isSubmitting = false;
          this.handleBusinessUnitError(err, 'update');
        }
      });
    } else {
      // Create mode - create new business unit
      this.businessUnitService.createBusinessUnit(businessUnitData as BusinessUnitCreate).subscribe({
        next: () => {
          this.showSuccess('Business unit created successfully!');
          setTimeout(() => {
            this.navigateToAdmin();
          }, 2000);
        },
        error: (err: HttpErrorResponse) => {
          this.isSubmitting = false;
          this.handleBusinessUnitError(err, 'create');
        }
      });
    }
  }

  handleBusinessUnitError(err: HttpErrorResponse, operation: string): void {
    console.error(`Error ${operation} business unit:`, err);
    
    let errorMessage = `Failed to ${operation} business unit.`;
    
    if (err.status === 422 && err.error?.detail?.errors) {
      // Validation errors
      const errors = err.error.detail.errors;
      const errorMessages = Object.values(errors).flat() as string[];
      errorMessage = errorMessages.join(' ');
    } else if (err.status === 409) {
      errorMessage = err.error?.detail || 'A business unit with this name or code already exists in the organization.';
    } else if (err.status === 400) {
      errorMessage = err.error?.detail || 'Invalid business unit data. Please check all fields.';
    } else if (err.status === 404) {
      errorMessage = operation === 'update' ? 'Business unit not found.' : 'Organization or parent unit not found.';
    } else if (err.status === 403) {
      errorMessage = err.error?.detail || 'You do not have permission to perform this action.';
    } else if (err.error?.detail) {
      errorMessage = err.error.detail;
    }
    
    this.showError(errorMessage);
  }

  private markFormGroupTouched(): void {
    Object.keys(this.businessUnitForm.controls).forEach(key => {
      const control = this.businessUnitForm.get(key);
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

  onActiveStatusChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    const isChecked = target.checked;
    console.log('=== CHECKBOX CHANGE EVENT ===');
    console.log('Checkbox state:', isChecked);
    console.log('Event target:', target);
    
    // Explicitly set the form control value
    this.businessUnitForm.get('is_active')?.setValue(isChecked);
    
    console.log('Form control value after update:', this.businessUnitForm.get('is_active')?.value);
    console.log('Form control value type:', typeof this.businessUnitForm.get('is_active')?.value);
    console.log('============================');
  }

  // Header event handlers
  navigateToProfile(): void {
    this.router.navigate(['/profile']);
  }

  navigateToAdmin(): void {
    // Navigate back to admin with preserved state if available
    if (Object.keys(this.returnQueryParams).length > 0) {
      this.router.navigate(['/admin'], { queryParams: this.returnQueryParams });
    } else {
      this.router.navigate(['/admin']);
    }
  }

  logout(): void {
    this.authService.logout();
  }

  // Form validation helpers
  isFieldInvalid(fieldName: string): boolean {
    const field = this.businessUnitForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(fieldName: string): string {
    const field = this.businessUnitForm.get(fieldName);
    if (field && field.errors) {
      const fieldLabel = this.getFieldLabel(fieldName);
      
      if (field.errors['required']) {
        return this.getRequiredErrorMessage(fieldName);
      }
      if (field.errors['minlength']) {
        const requiredLength = field.errors['minlength'].requiredLength;
        return `${fieldLabel} must be at least ${requiredLength} characters long.`;
      }
      if (field.errors['maxlength']) {
        const maxLength = field.errors['maxlength'].requiredLength;
        return `${fieldLabel} must be ${maxLength} characters or less.`;
      }
      if (field.errors['email']) {
        return 'Please enter a valid email address.';
      }
      if (field.errors['phone']) {
        return 'Please enter a valid phone number.';
      }
      if (field.errors['phoneLength']) {
        return 'Phone number must contain between 7 and 15 digits.';
      }
      if (field.errors['pattern']) {
        return fieldName === 'code' ? 'Code must contain only uppercase letters, numbers, underscores, and hyphens.' : `Please enter a valid ${fieldLabel.toLowerCase()}.`;
      }
    }
    return '';
  }

  private getRequiredErrorMessage(fieldName: string): string {
    const messages: { [key: string]: string } = {
      organization_id: 'Organization is required.',
      name: 'Business unit name is required.'
    };
    return messages[fieldName] || `${this.getFieldLabel(fieldName)} is required.`;
  }

  private getFieldLabel(fieldName: string): string {
    const labels: { [key: string]: string } = {
      organization_id: 'Organization',
      name: 'Business Unit Name',
      parent_unit_id: 'Parent Unit',
      code: 'Code',
      description: 'Description',
      manager_id: 'Manager',
      location: 'Location',
      country: 'Country',
      region: 'Region',
      email: 'Email',
      phone_number: 'Phone Number',
      is_active: 'Active Status'
    };
    return labels[fieldName] || fieldName;
  }

  /**
   * Ensures a value is converted to a proper boolean
   * Handles null, undefined, and string values properly
   */
  private ensureBoolean(value: any): boolean {
    if (value === null || value === undefined) {
      return false;
    }
    if (typeof value === 'boolean') {
      return value;
    }
    if (typeof value === 'string') {
      return value.toLowerCase() === 'true';
    }
    // For any other type, convert to boolean
    return Boolean(value);
  }
}
