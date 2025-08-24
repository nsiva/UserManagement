import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth';
import { UserService, UserCreate, UserUpdate, Role, User } from '../../services/user';
import { UserProfileService } from '../../services/user-profile.service';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [FormsModule, CommonModule, ReactiveFormsModule],
  templateUrl: './user-form.html',
  styleUrl: './user-form.scss'
})
export class UserFormComponent implements OnInit {
  userForm: FormGroup;
  userRolesOptions: Role[] = [];
  selectedUserRole: string = 'user';
  errorMessage: string | null = null;
  successMessage: string | null = null;
  showDropdown = false;
  currentUser: any = null;
  isEditMode = false;
  userId: string | null = null;
  userToEdit: User | null = null;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private route: ActivatedRoute,
    private authService: AuthService,
    private userService: UserService,
    private userProfileService: UserProfileService
  ) {
    this.userForm = this.fb.group({
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.minLength(6)]] // Password optional for edit
    });
  }

  ngOnInit(): void {
    // Ensure authentication token exists before making API calls
    if (!this.authService.getToken()) {
      this.router.navigate(['/login']);
      return;
    }
    
    this.checkMode();
    this.loadRoles();
    this.loadCurrentUser();
  }

  checkMode(): void {
    this.userId = this.route.snapshot.paramMap.get('id');
    this.isEditMode = !!this.userId;
    
    
    if (this.isEditMode && this.userId) {
      // Make password optional for edit mode first
      this.userForm.get('password')?.clearValidators();
      this.userForm.get('password')?.updateValueAndValidity();
      
      // Then load user data
      this.loadUserForEdit(this.userId);
    } else {
      // Password required for create mode
      this.userForm.get('password')?.setValidators([Validators.required, Validators.minLength(6)]);
      this.userForm.get('password')?.updateValueAndValidity();
    }
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
        
        // Clear any previous error messages
        this.errorMessage = null;
        
        
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

  loadCurrentUser(): void {
    this.userProfileService.getCurrentUserProfile().subscribe({
      next: (user) => {
        this.currentUser = user;
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error loading current user profile:', err);
        // Don't show error to user as this is background loading
      }
    });
  }

  loadRoles(): void {
    this.userService.getRoles().subscribe({
      next: (data) => {
        this.userRolesOptions = data;
        // Only clear error message if it's not a user loading error
        if (this.errorMessage && !this.errorMessage.includes('load user')) {
          this.errorMessage = null;
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
    this.errorMessage = message;
    this.successMessage = null;
  }

  showSuccess(message: string): void {
    this.successMessage = message;
    this.errorMessage = null;
  }

  // Navigation methods for dropdown
  toggleDropdown(): void {
    this.showDropdown = !this.showDropdown;
  }

  navigateToProfile(): void {
    this.showDropdown = false;
    this.router.navigate(['/profile']);
  }

  navigateToAdmin(): void {
    this.showDropdown = false;
    this.router.navigate(['/admin']);
  }

  isAdmin(): boolean {
    return this.authService.isAdmin();
  }

  getUserInitials(): string {
    // If current user data is loaded and has first/last name, use them
    if (this.currentUser && this.currentUser.first_name && this.currentUser.last_name) {
      return (this.currentUser.first_name.charAt(0) + this.currentUser.last_name.charAt(0)).toUpperCase();
    }
    
    // If only first name is available
    if (this.currentUser && this.currentUser.first_name) {
      return (this.currentUser.first_name.charAt(0) + (this.currentUser.first_name.charAt(1) || 'U')).toUpperCase();
    }
    
    // Fall back to email from auth service
    const email = this.authService.getUserEmail();
    if (!email) return 'U';
    
    const emailParts = email.split('@')[0];
    if (emailParts.length >= 2) {
      return emailParts.substring(0, 2).toUpperCase();
    }
    return emailParts.substring(0, 1).toUpperCase() + 'U';
  }

  logout(): void {
    this.showDropdown = false;
    this.authService.logout();
  }
}
