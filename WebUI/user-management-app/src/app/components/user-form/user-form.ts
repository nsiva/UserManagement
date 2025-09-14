import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth';
import { UserService, UserCreate, UserUpdate, Role, User } from '../../services/user';
import { UserProfileService } from '../../services/user-profile.service';
import { BusinessUnitService, BusinessUnit } from '../../services/business-unit';
import { OrganizationService, Organization } from '../../services/organization';
import { RoleService } from '../../services/role.service';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { AlertComponent, AlertType } from '../../shared/components/alert/alert.component';
import { AutocompleteComponent, AutocompleteOption } from '../../shared/components/autocomplete/autocomplete.component';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';
import { 
  ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN,
  hasAdminAccess, hasOrganizationAdminAccess, hasBusinessUnitAdminAccess 
} from '../../constants/roles';
import { PasswordValidationService, PasswordRequirements } from '../../shared/services/password-validation.service';
import { PasswordRequirementsComponent } from '../../shared/components/password-requirements/password-requirements.component';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [FormsModule, CommonModule, ReactiveFormsModule, HeaderComponent, AlertComponent, PasswordRequirementsComponent, AutocompleteComponent],
  templateUrl: './user-form.html',
  styleUrl: './user-form.scss'
})
export class UserFormComponent implements OnInit, OnDestroy {
  // Custom validator for non-whitespace text
  private static noWhitespaceValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value) {
      return { required: true };
    }
    if (typeof value === 'string' && value.trim().length === 0) {
      return { whitespace: true };
    }
    return null;
  }

  // Strict email validator
  private static strictEmailValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value) {
      return null; // Let required validator handle empty values
    }
    
    // More strict email pattern that requires proper domain format
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    
    if (!emailPattern.test(value)) {
      return { strictEmail: true };
    }
    
    return null;
  }
  // Header configuration
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.USER_FORM,
    showUserMenu: true
  };
  userForm: FormGroup;
  userRolesOptions: Role[] = [];
  selectedUserRole: string = 'user';
  organizationsOptions: Organization[] = [];
  businessUnitsOptions: BusinessUnit[] = [];
  filteredBusinessUnitsOptions: BusinessUnit[] = [];
  selectedOrganizationId: string = '';
  
  // Password options
  passwordOption: string = 'send_link'; // 'generate_now' or 'send_link'
  showPasswordField: boolean = false;
  sendPasswordReset: boolean = false; // For edit mode password reset
  
  // Autocomplete options
  organizationAutocompleteOptions: AutocompleteOption[] = [];
  businessUnitAutocompleteOptions: AutocompleteOption[] = [];
  // Alert properties
  alertMessage: string | null = null;
  alertType: AlertType = 'info';
  isEditMode = false;
  userId: string | null = null;
  userToEdit: User | null = null;
  isLoading = false;
  isEditingSelf = false;
  isEditingOwnProfile = false;
  private routeSubscription: Subscription | null = null;
  
  // Password requirements tracking
  passwordRequirements: PasswordRequirements = {
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecialChar: false
  };

  // Return navigation parameters
  private returnQueryParams: any = {};

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private route: ActivatedRoute,
    private authService: AuthService,
    private userService: UserService,
    private userProfileService: UserProfileService,
    private businessUnitService: BusinessUnitService,
    private organizationService: OrganizationService,
    private roleService: RoleService
  ) {
    this.userForm = this.fb.group({
      firstName: ['', UserFormComponent.noWhitespaceValidator],
      lastName: ['', UserFormComponent.noWhitespaceValidator],
      email: ['', [Validators.required, UserFormComponent.strictEmailValidator]],
      organization: ['', Validators.required], // Organization is required
      businessUnit: ['', Validators.required], // Business unit is required
      password: ['', [PasswordValidationService.validatePassword]], // Password with full validation
      passwordOption: ['send_link'], // Password setup option
      sendPasswordReset: [false] // For edit mode password reset
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
    this.routeSubscription = this.route.paramMap.subscribe(params => {
      // Reset form and component state first
      this.resetComponent();
      // Load data first, then check mode to ensure all data is available for edit mode
      this.loadRoles();
      this.loadOrganizations();
      this.loadBusinessUnits();
      this.checkMode();
    });
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
    if (queryParams['buId']) {
      this.returnQueryParams['buId'] = queryParams['buId'];
    }
    
    console.log('UserFormComponent: Captured return parameters:', this.returnQueryParams);
  }

  checkMode(): void {
    this.userId = this.route.snapshot.paramMap.get('id');
    this.isEditMode = !!this.userId;
    
    // Update header subtitle based on mode
    this.headerConfig = {
      ...this.headerConfig,
      subtitle: this.isEditMode ? 'Edit User' : 'Create New User'
    };
    
    console.log('UserFormComponent: checkMode - userId:', this.userId, 'isEditMode:', this.isEditMode);
    
    if (this.isEditMode && this.userId) {
      // Make password optional for edit mode first
      this.userForm.get('password')?.clearValidators();
      this.userForm.get('password')?.updateValueAndValidity();
      
      // Then load user data
      this.loadUserForEdit(this.userId);
    } else {
      // Create mode - set up default password option behavior
      
      // Ensure form is blank for create mode
      this.userForm.reset({
        firstName: '',
        lastName: '',
        email: '',
        organization: '',
        businessUnit: '',
        password: '',
        passwordOption: 'send_link' // Set default password option
      });
      this.selectedUserRole = 'user';
      
      // Configure password field based on default option (send_link)
      this.passwordOption = 'send_link';
      this.showPasswordField = false;
      
      // Disable password field since default is "send_link"
      const passwordControl = this.userForm.get('password');
      passwordControl?.clearValidators();
      passwordControl?.setValue('');
      passwordControl?.disable();
      passwordControl?.updateValueAndValidity();
      
      // Add a timeout to clear form after any potential autofill
      setTimeout(() => {
        this.userForm.patchValue({
          firstName: '',
          lastName: '',
          email: '',
          organization: '',
          businessUnit: '',
          password: '',
          passwordOption: 'send_link'
        });
        console.log('UserFormComponent: Create mode - delayed form clear:', this.userForm.value);
      }, 100);
      
      console.log('UserFormComponent: Create mode - form reset to blank values:', this.userForm.value);
    }
    
    // Initialize password requirements validation
    this.validatePasswordRequirements();
  }
  
  onPasswordChange(): void {
    this.validatePasswordRequirements();
  }
  
  validatePasswordRequirements(): void {
    const password = this.userForm.get('password')?.value || '';
    this.passwordRequirements = PasswordValidationService.getPasswordRequirements(password);
  }

  loadUserForEdit(userId: string): void {
    this.isLoading = true;
    console.log('UserFormComponent: Loading user for edit, userId:', userId);
    console.log('UserFormComponent: Current user email:', this.authService.getUserEmail());
    console.log('UserFormComponent: Current user roles:', this.authService.getUserRoles());
    
    // Check if user is editing themselves by comparing user IDs
    const currentUserId = this.authService.getUserId();
    const isEditingSelf = currentUserId === userId;
    console.log('UserFormComponent: Current user ID:', currentUserId, 'Target user ID:', userId, 'Is editing self:', isEditingSelf);
    console.log('UserFormComponent: Current user ID type:', typeof currentUserId, 'Target user ID type:', typeof userId);
    console.log('UserFormComponent: Using API endpoint:', isEditingSelf ? 'profiles/me/full' : 'admin/users/' + userId);
    
    // Use appropriate endpoint based on whether user is editing themselves
    const userRequest = isEditingSelf ? 
      this.userService.getMyProfile() : 
      this.userService.getUser(userId);
    
    userRequest.subscribe({
      next: (user) => {
        this.userToEdit = user;
        
        // Check if user is editing their own profile first
        const currentUserEmail = this.authService.getUserEmail();
        this.isEditingOwnProfile = (user.email === currentUserEmail);
        
        // First populate form with basic user data (except organization and business unit)
        this.userForm.patchValue({
          firstName: user.first_name || '',
          lastName: user.last_name || '',
          email: user.email,
          password: '' // Don't populate password for security
        });
        
        // Set selected organization and load business units for that organization
        if (user.organization_id) {
          console.log('UserFormComponent: User has organization_id:', user.organization_id);
          console.log('UserFormComponent: User has business_unit_id:', user.business_unit_id);
          this.selectedOrganizationId = user.organization_id;
          
          // First update organization autocomplete options
          this.updateOrganizationAutocompleteOptions();
          
          // Set organization value after options are ready with a small delay
          setTimeout(() => {
            this.userForm.patchValue({
              organization: user.organization_id || ''
            });
            // Force change detection to ensure autocomplete updates
            this.userForm.get('organization')?.updateValueAndValidity();
            console.log('UserFormComponent: Organization value set after timeout:', user.organization_id);
          }, 10);
          
          // Load business units for the organization, then set business unit value
          this.loadBusinessUnitsForOrganizationAndSetValue(user.organization_id, user.business_unit_id || '');
        } else {
          console.log('UserFormComponent: User has no organization_id');
          // Set empty values if no organization
          this.userForm.patchValue({
            organization: '',
            businessUnit: ''
          });
        }
        
        this.selectedUserRole = user.roles.length > 0 ? user.roles[0] : 'user';
        
        // Check if current user has permission to edit this user
        if (!this.roleService.canEditUser(user.roles, user.email)) {
          this.showError('Permission denied: You do not have permission to edit this user.');
          // Redirect back to admin page after 5 seconds
          setTimeout(() => {
            this.navigateToAdmin();
          }, 5000);
          this.isLoading = false;
          return;
        }
        
        // Clear any previous alert messages
        this.alertMessage = null;
        
        // Reload roles with the user context to check if editing self
        this.loadRoles();
        
        console.log('UserFormComponent: User loaded for edit successfully');
        
        this.isLoading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.isLoading = false;
        console.error('Error loading user:', err);
        
        // Handle different error scenarios
        if (err.status === 405) {
          this.showError('Method not allowed. Please try again or contact support.');
        } else if (err.status === 401) {
          this.showError('Authentication failed. Redirecting to login...');
          setTimeout(() => this.router.navigate(['/login']), 2000);
        } else if (err.status === 403) {
          this.showError('Access denied. You may not have permission to view this user.');
        } else if (err.status === 404) {
          this.showError('User not found.');
          setTimeout(() => this.navigateToAdmin(), 2000);
        } else {
          this.showError(err.error?.detail || 'Failed to load user.');
        }
      }
    });
  }


  loadRoles(): void {
    this.userService.getRoles().subscribe({
      next: (data) => {
        // Filter roles based on current user's permissions and whether editing self
        if (this.isEditMode && this.userToEdit) {
          const currentUserEmail = this.authService.getUserEmail();
          this.isEditingSelf = this.roleService.isEditingSelf(this.userToEdit.email, currentUserEmail || '');
          this.userRolesOptions = this.roleService.getAssignableRolesForUser(
            data, 
            this.userToEdit.email, 
            currentUserEmail || ''
          );
        } else {
          // For create mode, use normal role filtering
          this.userRolesOptions = this.roleService.getAssignableRoles(data);
        }
        
        // Only clear alert message if it's not a user loading error
        if (this.alertMessage && !this.alertMessage.includes('load user')) {
          this.alertMessage = null;
        }
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load roles.');
        console.error('Error loading roles:', err);
      }
    });
  }

  loadOrganizations(): void {
    this.organizationService.getOrganizations().subscribe({
      next: (organizations) => {
        this.organizationsOptions = organizations;
        this.updateOrganizationAutocompleteOptions();
        // Clear alert message if it's not a user loading error
        if (this.alertMessage && !this.alertMessage.includes('load user')) {
          this.alertMessage = null;
        }
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load organizations.');
        console.error('Error loading organizations:', err);
      }
    });
  }

  loadBusinessUnits(): void {
    // Call business units API without organization filter - backend handles role-based filtering
    this.businessUnitService.getBusinessUnits().subscribe({
      next: (response) => {
        this.businessUnitsOptions = response.business_units;
        // Initially show no business units until organization is selected
        this.filteredBusinessUnitsOptions = [];
        // Clear alert message if it's not a user loading error
        if (this.alertMessage && !this.alertMessage.includes('load user')) {
          this.alertMessage = null;
        }
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load business units.');
        console.error('Error loading business units:', err);
      }
    });
  }

  loadBusinessUnitsForOrganization(organizationId: string): void {
    console.log('UserFormComponent: loadBusinessUnitsForOrganization called with organizationId:', organizationId);
    console.log('UserFormComponent: Current businessUnitsOptions length:', this.businessUnitsOptions.length);
    
    // Load business units for the specific organization directly from the API
    this.businessUnitService.getBusinessUnits(organizationId).subscribe({
      next: (response) => {
        console.log('UserFormComponent: Received business units for organization:', response.business_units.length);
        this.filteredBusinessUnitsOptions = response.business_units;
        this.updateBusinessUnitAutocompleteOptions();
        console.log('UserFormComponent: Filtered business units:', this.filteredBusinessUnitsOptions);
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load business units.');
        console.error('Error loading business units for organization:', err);
      }
    });
  }

  loadBusinessUnitsForOrganizationAndSetValue(organizationId: string, businessUnitId: string): void {
    console.log('UserFormComponent: loadBusinessUnitsForOrganizationAndSetValue called with organizationId:', organizationId, 'businessUnitId:', businessUnitId);
    
    // Load business units for the specific organization directly from the API
    this.businessUnitService.getBusinessUnits(organizationId).subscribe({
      next: (response) => {
        console.log('UserFormComponent: Received business units for organization:', response.business_units.length);
        this.filteredBusinessUnitsOptions = response.business_units;
        this.updateBusinessUnitAutocompleteOptions();
        console.log('UserFormComponent: Filtered business units:', this.filteredBusinessUnitsOptions);
        
        // Now that business unit options are loaded, set the form value
        if (businessUnitId) {
          console.log('UserFormComponent: Setting business unit value:', businessUnitId);
          // Use setTimeout to ensure the autocomplete options are ready before setting the value
          setTimeout(() => {
            this.userForm.patchValue({
              businessUnit: businessUnitId
            });
            // Force change detection to ensure autocomplete updates
            this.userForm.get('businessUnit')?.updateValueAndValidity();
            console.log('UserFormComponent: Business unit value set after timeout:', businessUnitId);
          }, 10);
        }
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load business units.');
        console.error('Error loading business units for organization:', err);
      }
    });
  }

  onOrganizationChange(): void {
    const organizationId = this.userForm.get('organization')?.value;
    this.selectedOrganizationId = organizationId;
    
    // Reset business unit selection when organization changes
    this.userForm.get('businessUnit')?.setValue('');
    
    if (organizationId) {
      this.loadBusinessUnitsForOrganization(organizationId);
    } else {
      this.filteredBusinessUnitsOptions = [];
    }
  }

  onRoleRadioChange(roleName: string): void {
    this.selectedUserRole = roleName;
  }

  onUserSubmit(): void {
    if (this.userForm.invalid) {
      this.showError('Please fill in all required user fields correctly.');
      return;
    }

    // Additional password validation for create mode and edit mode when password is provided
    if ((!this.isEditMode || this.userForm.value.password) && this.userForm.value.password) {
      if (!PasswordValidationService.areAllRequirementsMet(this.userForm.value.password)) {
        this.showError('Please ensure your password meets all the requirements below.');
        return;
      }
    }

    if (this.isEditMode && this.userId) {
      // Edit mode - different handling for own profile vs other users
      if (this.isEditingOwnProfile) {
        // When editing own profile, use the self-profile update endpoint
        const profileData = {
          first_name: this.userForm.value.firstName,
          last_name: this.userForm.value.lastName
        };

        this.userService.updateMyProfile(profileData).subscribe({
          next: () => {
            this.showSuccess('Profile updated successfully!');
            // Navigate back to admin page after 2 seconds
            setTimeout(() => {
              this.navigateToAdmin();
            }, 2000);
          },
          error: (err: HttpErrorResponse) => {
            this.showError(err.error?.detail || 'Failed to update profile.');
            console.error('Error updating profile:', err);
          }
        });
      } else {
        // Normal edit mode for other users - use admin endpoint
        const userData: UserUpdate = {
          first_name: this.userForm.value.firstName,
          last_name: this.userForm.value.lastName,
          email: this.userForm.value.email,
          password: this.userForm.value.password || undefined, // Only include password if provided
          send_password_reset: this.sendPasswordReset, // Send password reset email if checked
          roles: this.selectedUserRole ? [this.selectedUserRole] : [],
          business_unit_id: this.userForm.value.businessUnit || undefined
        };

        this.userService.updateUser(this.userId, userData).subscribe({
          next: () => {
            this.showSuccess('User updated successfully!');
            // Navigate back to admin page after 2 seconds
            setTimeout(() => {
              this.navigateToAdmin();
            }, 2000);
          },
          error: (err: HttpErrorResponse) => {
            this.showError(err.error.detail || 'Failed to update user.');
            console.error('Error updating user:', err);
          }
        });
      }
    } else {
      // Create mode
      const passwordOption = this.userForm.value.passwordOption || 'generate_now';
      
      if (passwordOption === 'generate_now' && !this.userForm.value.password) {
        this.showError('Password is required when "Generate password now" option is selected.');
        return;
      }

      const userData: UserCreate = {
        first_name: this.userForm.value.firstName,
        last_name: this.userForm.value.lastName,
        email: this.userForm.value.email,
        password: passwordOption === 'generate_now' ? this.userForm.value.password : undefined,
        password_option: passwordOption,
        roles: this.selectedUserRole ? [this.selectedUserRole] : [],
        business_unit_id: this.userForm.value.businessUnit
      };

      this.userService.createUser(userData).subscribe({
        next: () => {
          this.showSuccess('User created successfully!');
          // Navigate back to admin page after 2 seconds
          setTimeout(() => {
            this.navigateToAdmin();
          }, 2000);
        },
        error: (err: HttpErrorResponse) => {
          this.showError(err.error.detail || 'Failed to create user.');
          console.error('Error creating user:', err);
        }
      });
    }
  }

  cancel(): void {
    this.navigateToAdmin();
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

  // Navigation methods for dropdown
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

  resetComponent(): void {
    console.log('UserFormComponent: Resetting component state');
    
    // Reset all component state
    this.alertMessage = null;
    this.isEditMode = false;
    this.userId = null;
    this.userToEdit = null;
    this.isLoading = false;
    this.selectedUserRole = 'user';
    
    // Multiple approaches to clear form
    console.log('UserFormComponent: Form values before reset:', this.userForm.value);
    
    // Approach 1: Reset form
    this.userForm.reset();
    
    // Approach 2: Set each control value explicitly
    this.userForm.patchValue({
      firstName: '',
      lastName: '',
      email: '',
      organization: '',
      businessUnit: '',
      password: ''
    });
    
    // Approach 3: Clear individual controls
    this.userForm.get('firstName')?.setValue('');
    this.userForm.get('lastName')?.setValue('');
    this.userForm.get('email')?.setValue('');
    this.userForm.get('organization')?.setValue('');
    this.userForm.get('businessUnit')?.setValue('');
    this.userForm.get('password')?.setValue('');
    
    console.log('UserFormComponent: Form values after reset:', this.userForm.value);
    
    // Force change detection
    this.userForm.markAsPristine();
    this.userForm.markAsUntouched();
  }

  // --- Autocomplete Options Update Methods ---
  private updateOrganizationAutocompleteOptions(): void {
    this.organizationAutocompleteOptions = this.organizationsOptions.map(org => ({
      id: org.id,
      label: org.company_name
    }));
  }

  private updateBusinessUnitAutocompleteOptions(): void {
    this.businessUnitAutocompleteOptions = this.filteredBusinessUnitsOptions.map(unit => ({
      id: unit.id,
      label: unit.name
    }));
  }

  // --- Autocomplete Event Handlers ---
  onOrganizationAutocompleteChange(organizationId: string): void {
    this.userForm.get('organization')?.setValue(organizationId);
    this.onOrganizationChange();
  }

  onBusinessUnitAutocompleteChange(businessUnitId: string): void {
    this.userForm.get('businessUnit')?.setValue(businessUnitId);
  }

  // --- Password Option Handlers ---
  onPasswordOptionChange(): void {
    this.passwordOption = this.userForm.get('passwordOption')?.value || 'generate_now';
    this.showPasswordField = this.passwordOption === 'generate_now';
    
    // Update password field validation based on option
    const passwordControl = this.userForm.get('password');
    if (this.showPasswordField) {
      passwordControl?.setValidators([PasswordValidationService.validatePassword]);
      passwordControl?.enable();
    } else {
      passwordControl?.clearValidators();
      passwordControl?.setValue('');
      passwordControl?.disable();
    }
    passwordControl?.updateValueAndValidity();
  }

  onSendPasswordResetChange(): void {
    this.sendPasswordReset = this.userForm.get('sendPasswordReset')?.value || false;
    
    // Disable password field if sending reset email
    const passwordControl = this.userForm.get('password');
    if (this.sendPasswordReset) {
      passwordControl?.disable();
      passwordControl?.setValue('');
    } else {
      passwordControl?.enable();
    }
  }
}
