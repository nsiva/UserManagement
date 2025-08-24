import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-mfa',
  imports: [FormsModule, CommonModule],
  templateUrl: './mfa.html',
  styleUrls: ['./mfa.scss']
})
export class MfaComponent {
  mfaCode = '';
  userEmail: string | null = null;
  userName: string | null = null;
  userId: string | null = null;
  message: string | null = null;
  isError = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService
  ) {
    // Get user info from session storage instead of query params
    this.userEmail = sessionStorage.getItem('mfa_user_email');
    this.userName = sessionStorage.getItem('mfa_user_name');
    this.userId = sessionStorage.getItem('mfa_user_id');
    
    console.log('MFA Component - Retrieved email:', this.userEmail);
    console.log('MFA Component - Retrieved name:', this.userName);
    console.log('MFA Component - Retrieved userId:', this.userId);
    
    // If no user email found, redirect back to login
    if (!this.userEmail) {
      console.log('No email found in session storage, redirecting to login');
      this.router.navigate(['/login']);
    }
  }

  onSubmitMfa(): void {
    this.message = null;
    this.isError = false;
    console.log('MFA Submit - Email:', this.userEmail, 'Code:', this.mfaCode);
    
    if (!this.mfaCode) {
      this.message = 'Please enter the MFA code.';
      this.isError = true;
      return;
    }
    if (!this.userEmail) {
      this.message = 'Email is required for MFA verification.';
      this.isError = true;
      return;
    }
    
    console.log('Calling authService.verifyMfa with:', this.userEmail, this.mfaCode);
    this.authService.verifyMfa(this.userEmail, this.mfaCode).subscribe({
      next: (response: any) => {
        console.log('MFA verification successful:', response);
        this.message = 'MFA verification successful! You are now logged in.';
        this.isError = false;
        
        // Clear session storage
        sessionStorage.removeItem('mfa_user_email');
        sessionStorage.removeItem('mfa_user_name');
        
        // Redirect based on user type
        if (this.authService.isAdmin()) {
          this.router.navigate(['/admin']);
        } else {
          this.router.navigate(['/profile']);
        }
      },
      error: (error: HttpErrorResponse) => {
        console.error('MFA verification error details:', error);
        console.error('Error status:', error.status);
        console.error('Error message:', error.error);
        this.isError = true;
        this.message = error.error?.detail || 'MFA verification failed. Please try again.';
      }
    });
  }
}