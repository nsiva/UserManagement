import { Component } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { API_PATHS } from '../../api-paths';
import { AuthService } from '../../services/auth';
import { UserProfileService } from '../../services/user-profile.service';
import { RoleService } from '../../services/role.service';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-login',
  imports: [FormsModule, CommonModule, HeaderComponent],
  templateUrl: './login.html',
  styleUrls: ['./login.scss']
})
export class LoginComponent {
  // Header configuration for login page
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.LOGIN,
    showUserMenu: false
  };
  email = '';
  password = '';
  message: string | null = null;
  isError = false;
  private apiUrl = environment.apiUrl;

  constructor(
    private http: HttpClient, 
    private router: Router, 
    private authService: AuthService,
    private userProfileService: UserProfileService,
    private roleService: RoleService
  ) { }

  onLogin(): void {
    this.message = null;
    this.isError = false;

    if (!this.email || !this.password) {
      this.message = 'Please enter both email and password.';
      this.isError = true;
      return;
    }

    this.authService.login(this.email, this.password).subscribe({
      next: (response: any) => {
        // Check if MFA is required based on response
        if (response.mfa_required === true || response.requires_mfa === true) {
          // MFA is required - store user info and redirect to MFA page
          sessionStorage.setItem('mfa_user_email', this.email);
          sessionStorage.setItem('mfa_user_name', response.user_name || '');
          sessionStorage.setItem('mfa_user_id', response.user_id || '');
          this.router.navigate(['/mfa']);
        } else {
          // No MFA required for this login - complete login and check MFA setup
          this.message = 'Login successful! Welcome.';
          this.isError = false;
          this.email = '';
          this.password = '';
          
          // Check if user has MFA set up for future
          this.checkMfaStatusAndRedirect();
        }
      },
      error: (error: HttpErrorResponse) => {
        // Handle MFA required (402 status)
        if (error.status === 402) {
          // MFA is required - store user info and redirect to MFA page
          sessionStorage.setItem('mfa_user_email', this.email);
          if (error.error && error.error.user_name) {
            sessionStorage.setItem('mfa_user_name', error.error.user_name);
          }
          if (error.error && error.error.user_id) {
            sessionStorage.setItem('mfa_user_id', error.error.user_id);
          }
          this.router.navigate(['/mfa']);
        } else {
          this.handleError(error);
        }
      }
    });
  }


  onForgotPassword(): void {
    this.router.navigate(['/forgot-password']);
  }

  private async checkMfaStatusAndRedirect(): Promise<void> {
    try {
      // Get user profile to check MFA status
      const userProfile = await import('rxjs').then(rxjs => 
        rxjs.firstValueFrom(this.userProfileService.getCurrentUserProfile())
      );
      
      if (!userProfile.mfa_enabled) {
        // User doesn't have MFA enabled - redirect to setup every time
        console.log('User does not have MFA enabled, redirecting to setup');
        this.router.navigate(['/set-mfa']);
        return;
      }
      
      // User has MFA enabled - redirect to normal landing page
      this.redirectToLandingPage();
      
    } catch (error) {
      console.error('Error checking MFA status:', error);
      // On error, just redirect to normal landing page
      this.redirectToLandingPage();
    }
  }

  private redirectToLandingPage(): void {
    // Redirect based on user type
    if (this.roleService.hasAdminPrivileges()) {
      this.router.navigate(['/admin']);
    } else {
      this.router.navigate(['/profile']);
    }
  }


  private handleError = (error: HttpErrorResponse) => {
    this.isError = true;
    if (error.error instanceof ErrorEvent) {
      this.message = `An error occurred: ${error.error.message}`;
    } else {
      console.error(
        `Backend returned code ${error.status}, ` +
        `body was: ${JSON.stringify(error.error)}`);
      if (error.error && error.error.detail) {
        this.message = `Error: ${error.error.detail}`;
      } else {
        this.message = `An unknown error occurred. Status: ${error.status}`;
      }
    }
    return throwError(() => new Error(this.message || 'Something bad happened; please try again later.'));
  };

  // Header event handlers (not used but required by template)
  onProfileClick(): void {}
  onAdminClick(): void {}
  onLogoutClick(): void {}
}
