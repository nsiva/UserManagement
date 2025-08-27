import { Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../../services/auth';
import { environment } from '../../../environments/environment';
import { API_PATHS } from '../../api-paths';
import { catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.scss'
})
export class ResetPasswordComponent implements OnInit, OnDestroy {
  currentPassword: string = '';
  newPassword: string = '';
  confirmPassword: string = '';
  isLoading: boolean = false;
  successMessage: string = '';
  errorMessage: string = '';
  formSubmitted: boolean = false;

  // Password requirements tracking
  passwordRequirements = {
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecialChar: false
  };

  constructor(
    private router: Router,
    private http: HttpClient,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Check if user is logged in
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/login']);
    }
    
    // Initialize password requirements validation
    this.validatePasswordRequirements();
  }

  navigateBack(): void {
    // Only clear form data when user cancels (navigating away without success)
    this.clearAllFields();
    this.router.navigate(['/profile']);
  }
  
  private clearAllFields(): void {
    this.currentPassword = '';
    this.newPassword = '';
    this.confirmPassword = '';
    this.formSubmitted = false;
    this.validatePasswordRequirements();
  }

  onNewPasswordChange(): void {
    this.validatePasswordRequirements();
  }

  // Only clear fields when user cancels/navigates away (not on successful submission)
  @HostListener('window:beforeunload', ['$event'])
  onBeforeUnload(event: BeforeUnloadEvent): void {
    // Only clear if there's no success message (user is navigating away without completing)
    if (!this.successMessage) {
      this.clearAllFields();
    }
  }

  ngOnDestroy(): void {
    // Only clear if there's no success message (component destroyed without success)
    if (!this.successMessage) {
      this.clearAllFields();
    }
  }

  validatePasswordRequirements(): void {
    const password = this.newPassword;
    
    this.passwordRequirements = {
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
  }

  resetPassword(): void {
    this.formSubmitted = true;
    this.errorMessage = '';
    this.successMessage = '';

    // Basic validation
    if (!this.currentPassword?.trim() || !this.newPassword?.trim() || !this.confirmPassword?.trim()) {
      this.errorMessage = 'All fields are required';
      return;
    }

    // Validate password requirements
    this.validatePasswordRequirements();
    const allRequirementsMet = Object.values(this.passwordRequirements).every(req => req);
    
    if (!allRequirementsMet) {
      this.errorMessage = 'Please ensure your new password meets all the requirements below';
      return;
    }

    if (this.newPassword !== this.confirmPassword) {
      this.errorMessage = 'New passwords do not match';
      return;
    }

    this.isLoading = true;

    const resetData = {
      current_password: this.currentPassword,
      new_password: this.newPassword
    };

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.post(`${environment.apiUrl}${API_PATHS.resetPassword}`, resetData, { headers })
      .pipe(
        catchError(error => {
          this.isLoading = false;
          
          if (error.status === 400) {
            this.errorMessage = 'Current password is incorrect';
          } else if (error.status === 401) {
            this.errorMessage = 'Session expired. Please log in again';
            setTimeout(() => {
              this.authService.logout();
            }, 2000);
          } else if (error.status === 404) {
            this.errorMessage = 'User not found';
          } else {
            this.errorMessage = 'An error occurred while resetting your password. Please try again.';
          }
          
          console.error('Password reset error:', error);
          return of(null);
        })
      )
      .subscribe(response => {
        this.isLoading = false;
        
        if (response) {
          this.successMessage = 'Password reset successfully! Redirecting to profile...';
          
          // Simulate a successful form submission event for password managers
          const form = document.querySelector('form');
          if (form) {
            // Create a submit event to trigger password manager detection
            const submitEvent = new Event('submit', { bubbles: true });
            form.dispatchEvent(submitEvent);
          }
          
          // Keep fields populated briefly so browser can detect the successful change
          // Redirect after giving browser time to offer password save
          setTimeout(() => {
            this.router.navigate(['/profile']);
          }, 3000);
        }
      });
  }
}
