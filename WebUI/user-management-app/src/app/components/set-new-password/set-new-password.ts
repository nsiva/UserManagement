import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-set-new-password',
  imports: [FormsModule, CommonModule, HeaderComponent],
  templateUrl: './set-new-password.html',
  styleUrl: './set-new-password.scss'
})
export class SetNewPasswordComponent implements OnInit {
  // Header configuration for set-new-password page
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.SET_NEW_PASSWORD,
    showUserMenu: false
  };

  token: string = '';
  newPassword: string = '';
  confirmPassword: string = '';
  userEmail: string = '';
  isValidatingToken = false;
  tokenValid = false;
  isLoading = false;
  errorMessage: string = '';
  successMessage: string = '';

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
    private route: ActivatedRoute,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Get token from URL parameters
    this.route.queryParams.subscribe(params => {
      this.token = params['token'];
      if (this.token) {
        this.validateToken();
      } else {
        this.errorMessage = 'No reset token provided';
        this.tokenValid = false;
      }
    });
  }

  validateToken(): void {
    if (!this.token) {
      this.tokenValid = false;
      return;
    }

    this.isValidatingToken = true;
    this.errorMessage = '';

    this.authService.verifyResetToken(this.token).subscribe({
      next: (response) => {
        this.isValidatingToken = false;
        this.tokenValid = response.valid;
        if (response.valid && response.email) {
          this.userEmail = response.email;
        } else {
          this.errorMessage = 'Invalid or expired reset token';
        }
      },
      error: (error: HttpErrorResponse) => {
        this.isValidatingToken = false;
        this.tokenValid = false;
        this.errorMessage = 'Invalid or expired reset token';
        console.error('Token validation error:', error);
      }
    });
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

  isPasswordValid(): boolean {
    const allRequirementsMet = Object.values(this.passwordRequirements).every(req => req);
    const passwordsMatch = this.newPassword === this.confirmPassword;
    return allRequirementsMet && passwordsMatch && this.newPassword.trim() !== '';
  }

  onSetNewPassword(): void {
    this.errorMessage = '';
    this.successMessage = '';

    if (!this.newPassword?.trim() || !this.confirmPassword?.trim()) {
      this.errorMessage = 'Please fill in all fields';
      return;
    }

    if (this.newPassword !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match';
      return;
    }

    if (!this.isPasswordValid()) {
      this.errorMessage = 'Please ensure your password meets all the requirements';
      return;
    }

    this.isLoading = true;

    this.authService.setNewPassword(this.token, this.newPassword).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.successMessage = response.message || 'Password has been reset successfully!';
        
        // Clear form
        this.newPassword = '';
        this.confirmPassword = '';
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 3000);
      },
      error: (error: HttpErrorResponse) => {
        this.isLoading = false;
        
        if (error.status === 400) {
          this.errorMessage = error.error?.detail || 'Invalid or expired reset token';
        } else if (error.status === 500) {
          this.errorMessage = 'Server error. Please try again later.';
        } else {
          this.errorMessage = 'An error occurred. Please try again.';
        }
        
        console.error('Set new password error:', error);
      }
    });
  }

  onRequestNewLink(): void {
    this.router.navigate(['/forgot-password']);
  }

  onBackToLogin(): void {
    this.router.navigate(['/login']);
  }

  // Header event handlers (not used but required by template)
  onProfileClick(): void {}
  onAdminClick(): void {}
  onLogoutClick(): void {}
}