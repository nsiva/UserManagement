import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
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
export class LoginComponent implements OnInit {
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
  private redirectUri: string | null = null;
  private returnUrl: string | null = null;

  constructor(
    private http: HttpClient, 
    private router: Router,
    private route: ActivatedRoute,
    private authService: AuthService,
    private userProfileService: UserProfileService,
    private roleService: RoleService
  ) { }

  ngOnInit(): void {
    // Capture OAuth and redirect parameters
    this.route.queryParams.subscribe(params => {
      this.redirectUri = params['redirect_uri'] || null;
      // Properly decode the return_url which may be URL-encoded
      this.returnUrl = params['return_url'] ? decodeURIComponent(params['return_url']) : null;
      
      console.log('=== LOGIN COMPONENT DEBUG ===');
      console.log('Raw query params:', params);
      console.log('redirect_uri from params:', params['redirect_uri']);
      console.log('return_url from params:', params['return_url']);
      console.log('Decoded redirect_uri:', this.redirectUri);
      console.log('Decoded return_url:', this.returnUrl);
      console.log('Current URL:', window.location.href);
      console.log('==============================');

      // Show success message if OAuth was completed
      if (params['oauth_success'] === 'true' && params['message']) {
        this.message = params['message'];
        this.isError = false;
      }
    });
  }

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
          // MFA is required - store user info and redirect URI, then redirect to MFA page
          sessionStorage.setItem('mfa_user_email', this.email);
          sessionStorage.setItem('mfa_user_name', response.user_name || '');
          sessionStorage.setItem('mfa_user_id', response.user_id || '');
          
          // Store redirect information for use after MFA verification
          console.log('=== MFA REDIRECT STORAGE DEBUG ===');
          console.log('Storing return_url for MFA:', this.returnUrl);
          console.log('Storing redirect_uri for MFA:', this.redirectUri);
          
          if (this.returnUrl) {
            sessionStorage.setItem('login_return_url', this.returnUrl);
            console.log('Stored return_url in sessionStorage for MFA:', this.returnUrl);
          } else if (this.redirectUri) {
            sessionStorage.setItem('login_redirect_uri', this.redirectUri);
            console.log('Stored redirect_uri in sessionStorage for MFA:', this.redirectUri);
          } else {
            console.log('No return_url or redirect_uri to store - will use default redirect after MFA');
          }
          console.log('==================================');
          
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
          // MFA is required - store user info and redirect URI, then redirect to MFA page
          sessionStorage.setItem('mfa_user_email', this.email);
          if (error.error && error.error.user_name) {
            sessionStorage.setItem('mfa_user_name', error.error.user_name);
          }
          if (error.error && error.error.user_id) {
            sessionStorage.setItem('mfa_user_id', error.error.user_id);
          }
          
          // Store redirect information for use after MFA verification
          console.log('=== MFA REDIRECT STORAGE DEBUG (402 Error) ===');
          console.log('Storing return_url for MFA:', this.returnUrl);
          console.log('Storing redirect_uri for MFA:', this.redirectUri);
          
          if (this.returnUrl) {
            sessionStorage.setItem('login_return_url', this.returnUrl);
            console.log('Stored return_url in sessionStorage for MFA:', this.returnUrl);
          } else if (this.redirectUri) {
            sessionStorage.setItem('login_redirect_uri', this.redirectUri);
            console.log('Stored redirect_uri in sessionStorage for MFA:', this.redirectUri);
          } else {
            console.log('No return_url or redirect_uri to store - will use default redirect after MFA');
          }
          console.log('============================================');
          
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
        // User doesn't have MFA enabled
        console.log('User does not have MFA enabled');
        
        // For both OAuth and normal flows, redirect to MFA setup
        // The MFA setup component will handle OAuth redirects properly
        console.log('Redirecting to MFA setup');
        console.log('=== MFA SETUP REDIRECT DEBUG ===');
        console.log('Storing redirect_uri for MFA setup:', this.redirectUri);
        
        // Store redirect information for use after MFA setup completion
        if (this.returnUrl) {
          sessionStorage.setItem('login_return_url', this.returnUrl);
          console.log('Stored return_url in sessionStorage for MFA setup:', this.returnUrl);
        } else if (this.redirectUri) {
          sessionStorage.setItem('login_redirect_uri', this.redirectUri);
          console.log('Stored redirect_uri in sessionStorage for MFA setup:', this.redirectUri);
        } else {
          console.log('No return_url or redirect_uri to store for MFA setup');
        }
        console.log('===============================');
        
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
    // First priority: Handle OAuth authorization flow if return_url is present
    if (this.returnUrl) {
      console.log('Redirecting to OAuth authorization URL with token:', this.returnUrl);
      
      // Get the JWT token and append it to the OAuth URL
      const token = this.authService.getToken();
      if (token) {
        const separator = this.returnUrl.includes('?') ? '&' : '?';
        const urlWithToken = `${this.returnUrl}${separator}access_token=${encodeURIComponent(token)}`;
        console.log('Redirecting to OAuth URL with token:', urlWithToken);
        window.location.href = urlWithToken;
      } else {
        console.error('No JWT token found, redirecting without token');
        window.location.href = this.returnUrl;
      }
      return;
    }

    // Second priority: Check if there's a redirect URI to use (legacy support)
    if (this.redirectUri) {
      console.log('Redirecting to external URI:', this.redirectUri);
      window.location.href = this.redirectUri;
      return;
    }

    // Default redirect based on user type
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
