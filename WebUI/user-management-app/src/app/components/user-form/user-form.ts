import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthService } from '../../services/auth';
import { UserService, UserCreate, UserUpdate, Role, User } from '../../services/user';
import { UserProfileService } from '../../services/user-profile.service';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { AlertComponent, AlertType } from '../../shared/components/alert/alert.component';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';
import { PasswordValidationService, PasswordRequirements } from '../../shared/services/password-validation.service';
import { PasswordRequirementsComponent } from '../../shared/components/password-requirements/password-requirements.component';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [FormsModule, CommonModule, ReactiveFormsModule, HeaderComponent, AlertComponent, PasswordRequirementsComponent],
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
  // Alert properties
  alertMessage: string | null = null;
  alertType: AlertType = 'info';
  isEditMode = false;
  userId: string | null = null;
  userToEdit: User | null = null;
  isLoading = false;
  private routeSubscription: Subscription | null = null;
  
  // Password requirements tracking
  passwordRequirements: PasswordRequirements = {
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecialChar: false
  };

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private route: ActivatedRoute,
    private authService: AuthService,
    private userService: UserService,
    private userProfileService: UserProfileService
  ) {
    this.userForm = this.fb.group({
      firstName: ['', UserFormComponent.noWhitespaceValidator],
      lastName: ['', UserFormComponent.noWhitespaceValidator],
      email: ['', [Validators.required, UserFormComponent.strictEmailValidator]],
      password: ['', [PasswordValidationService.validatePassword]] // Password with full validation
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
      this.loadRoles();
    });
  }

  ngOnDestroy(): void {
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
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
      // Password required for create mode
      this.userForm.get('password')?.setValidators([Validators.required, PasswordValidationService.validatePassword]);
      this.userForm.get('password')?.updateValueAndValidity();
      
      // Ensure form is blank for create mode
      this.userForm.reset({
        firstName: '',
        lastName: '',
        email: '',
        password: ''
      });
      this.selectedUserRole = 'user';
      
      // Add a timeout to clear form after any potential autofill
      setTimeout(() => {
        this.userForm.patchValue({
          firstName: '',
          lastName: '',
          email: '',
          password: ''
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
    this.userService.getUser(userId).subscribe({
      next: (user) => {
        this.userToEdit = user;
        
        // Populate form with user data
        this.userForm.patchValue({
          firstName: user.first_name || '',
          lastName: user.last_name || '',
          email: user.email,
          password: '' // Don't populate password for security
        });
        
        this.selectedUserRole = user.roles.length > 0 ? user.roles[0] : 'user';
        
        // Clear any previous alert messages
        this.alertMessage = null;
        
        
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
          setTimeout(() => this.router.navigate(['/admin']), 2000);
        } else {
          this.showError(err.error?.detail || 'Failed to load user.');
        }
      }
    });
  }


  loadRoles(): void {
    this.userService.getRoles().subscribe({
      next: (data) => {
        this.userRolesOptions = data;
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
      // Edit mode
      const userData: UserUpdate = {
        first_name: this.userForm.value.firstName,
        last_name: this.userForm.value.lastName,
        email: this.userForm.value.email,
        password: this.userForm.value.password || undefined, // Only include password if provided
        roles: this.selectedUserRole ? [this.selectedUserRole] : []
      };

      this.userService.updateUser(this.userId, userData).subscribe({
        next: () => {
          this.showSuccess('User updated successfully!');
          // Navigate back to admin page after 2 seconds
          setTimeout(() => {
            this.router.navigate(['/admin']);
          }, 2000);
        },
        error: (err: HttpErrorResponse) => {
          this.showError(err.error.detail || 'Failed to update user.');
          console.error('Error updating user:', err);
        }
      });
    } else {
      // Create mode
      if (!this.userForm.value.password) {
        this.showError('Password is required for new users.');
        return;
      }

      const userData: UserCreate = {
        first_name: this.userForm.value.firstName,
        last_name: this.userForm.value.lastName,
        email: this.userForm.value.email,
        password: this.userForm.value.password,
        roles: this.selectedUserRole ? [this.selectedUserRole] : []
      };

      this.userService.createUser(userData).subscribe({
        next: () => {
          this.showSuccess('User created successfully!');
          // Navigate back to admin page after 2 seconds
          setTimeout(() => {
            this.router.navigate(['/admin']);
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
    this.router.navigate(['/admin']);
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
    this.router.navigate(['/admin']);
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
      password: ''
    });
    
    // Approach 3: Clear individual controls
    this.userForm.get('firstName')?.setValue('');
    this.userForm.get('lastName')?.setValue('');
    this.userForm.get('email')?.setValue('');
    this.userForm.get('password')?.setValue('');
    
    console.log('UserFormComponent: Form values after reset:', this.userForm.value);
    
    // Force change detection
    this.userForm.markAsPristine();
    this.userForm.markAsUntouched();
  }
}
