import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-forgot-password',
  imports: [FormsModule, CommonModule, HeaderComponent],
  templateUrl: './forgot-password.html',
  styleUrl: './forgot-password.scss'
})
export class ForgotPasswordComponent {
  // Header configuration for forgot-password page
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.FORGOT_PASSWORD,
    showUserMenu: false
  };
  email = '';
  message: string | null = null;
  isError = false;
  isLoading = false;

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  onForgotPassword(): void {
    this.message = null;
    this.isError = false;

    if (!this.email?.trim()) {
      this.message = 'Please enter your email address.';
      this.isError = true;
      return;
    }

    // Basic email validation
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(this.email)) {
      this.message = 'Please enter a valid email address.';
      this.isError = true;
      return;
    }

    this.isLoading = true;

    this.authService.forgotPassword(this.email).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.message = response.message || 'If the email exists in our system, a password reset link will be sent.';
        this.isError = false;
        
        // Clear the email field after successful submission
        this.email = '';
      },
      error: (error: HttpErrorResponse) => {
        this.isLoading = false;
        this.isError = true;
        
        // Always show a generic message for security (don't reveal if email exists)
        this.message = 'If the email exists in our system, a password reset link will be sent.';
        
        console.error('Forgot password error:', error);
      }
    });
  }

  onBackToLogin(): void {
    this.router.navigate(['/login']);
  }

  // Header event handlers (not used but required by template)
  onProfileClick(): void {}
  onAdminClick(): void {}
  onLogoutClick(): void {}
}