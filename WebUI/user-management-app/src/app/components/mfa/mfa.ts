import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';
import { RoleService } from '../../services/role.service';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-mfa',
  imports: [FormsModule, CommonModule, HeaderComponent],
  templateUrl: './mfa.html',
  styleUrls: ['./mfa.scss']
})
export class MfaComponent {
  // Header configuration for MFA page
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.MFA,
    showUserMenu: false
  };
  mfaCode = '';
  userEmail: string | null = null;
  userName: string | null = null;
  userId: string | null = null;
  message: string | null = null;
  isError = false;
  private redirectUri: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService,
    private roleService: RoleService
  ) {
    // Get user info and redirect URI from session storage
    this.userEmail = sessionStorage.getItem('mfa_user_email');
    this.userName = sessionStorage.getItem('mfa_user_name');
    this.userId = sessionStorage.getItem('mfa_user_id');
    this.redirectUri = sessionStorage.getItem('login_redirect_uri');
    
    console.log('=== MFA COMPONENT DEBUG ===');
    console.log('Retrieved email:', this.userEmail);
    console.log('Retrieved name:', this.userName);
    console.log('Retrieved userId:', this.userId);
    console.log('Retrieved redirect URI:', this.redirectUri);
    console.log('All sessionStorage keys:', Object.keys(sessionStorage));
    console.log('SessionStorage login_redirect_uri:', sessionStorage.getItem('login_redirect_uri'));
    console.log('==========================');
    
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
        sessionStorage.removeItem('mfa_user_id');
        
        // Check if there's a redirect URI to use
        console.log('=== MFA SUCCESS REDIRECT DEBUG ===');
        console.log('Current redirectUri value:', this.redirectUri);
        console.log('SessionStorage login_redirect_uri:', sessionStorage.getItem('login_redirect_uri'));
        
        if (this.redirectUri) {
          console.log('MFA verification successful - redirecting to external URI:', this.redirectUri);
          sessionStorage.removeItem('login_redirect_uri'); // Clean up
          console.log('About to redirect to:', this.redirectUri);
          window.location.href = this.redirectUri;
          return;
        } else {
          console.log('No redirect URI found - using default redirect');
        }
        console.log('=================================');
        
        // Default redirect based on user type
        if (this.roleService.hasAdminPrivileges()) {
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


  // Header event handlers (not used but required by template)
  onProfileClick(): void {}
  onAdminClick(): void {}
  onLogoutClick(): void {}
}