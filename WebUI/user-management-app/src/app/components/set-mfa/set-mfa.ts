import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { RoleService } from '../../services/role.service';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { EnhancedMfaSetupModalComponent } from '../../shared/components/enhanced-mfa-setup-modal/enhanced-mfa-setup-modal.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-set-mfa',
  imports: [CommonModule, FormsModule, HeaderComponent, EnhancedMfaSetupModalComponent],
  templateUrl: './set-mfa.html',
  styleUrl: './set-mfa.scss'
})
export class SetMfaComponent implements OnInit {
  // Header configuration for set-mfa page
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.SET_MFA,
    showUserMenu: true
  };
  
  userEmail: string | null = null;
  showPrompt = true; // Start with prompt instead of auto-generating
  showEnhancedMfaSetupModal = false;

  constructor(
    private authService: AuthService,
    private router: Router,
    private roleService: RoleService
  ) {}

  ngOnInit(): void {
    this.userEmail = this.authService.getUserEmail();
    // Don't auto-generate MFA - wait for user confirmation
  }

  confirmSetupMfa(): void {
    // User confirmed they want to set up MFA - show enhanced modal
    this.showPrompt = false;
    this.showEnhancedMfaSetupModal = true;
  }

  onMfaSetupClosed(): void {
    this.showEnhancedMfaSetupModal = false;
    // Return to prompt in case user wants to try again
    this.showPrompt = true;
  }

  onMfaSetupComplete(event: { method: 'totp' | 'email'; userEmail: string }): void {
    this.showEnhancedMfaSetupModal = false;
    // MFA setup is complete - redirect to appropriate page
    this.redirectToLandingPage();
  }

  // Header event handlers
  onProfileClick(): void {
    this.router.navigate(['/profile']);
  }
  
  onAdminClick(): void {
    if (this.roleService.hasAdminPrivileges()) {
      this.router.navigate(['/admin']);
    }
  }
  
  onLogoutClick(): void {
    this.authService.logout();
  }


  goBack(): void {
    this.router.navigate(['/profile']);
  }

  skipMfaSetup(): void {
    // Don't permanently dismiss - just redirect for this session
    // This allows prompting again on next login
    this.redirectToLandingPage();
  }

  private redirectToLandingPage(): void {
    // Check for OAuth authorization flow or redirect URI from the login flow
    const storedReturnUrl = sessionStorage.getItem('login_return_url');
    const storedRedirectUri = sessionStorage.getItem('login_redirect_uri');
    
    console.log('=== SET-MFA REDIRECT DEBUG ===');
    console.log('Stored return URL:', storedReturnUrl);
    console.log('Stored redirect URI:', storedRedirectUri);
    console.log('SessionStorage keys:', Object.keys(sessionStorage));
    console.log('============================');
    
    // First priority: OAuth authorization flow
    if (storedReturnUrl) {
      console.log('MFA setup complete - redirecting to OAuth authorization URL:', storedReturnUrl);
      sessionStorage.removeItem('login_return_url'); // Clean up
      
      // Get the JWT token and append it to the OAuth URL (same as in login component)
      const token = this.authService.getToken();
      if (token) {
        const separator = storedReturnUrl.includes('?') ? '&' : '?';
        const urlWithToken = `${storedReturnUrl}${separator}access_token=${encodeURIComponent(token)}`;
        console.log('Redirecting to OAuth URL with token after MFA setup:', urlWithToken);
        window.location.href = urlWithToken;
      } else {
        console.error('No JWT token found after MFA setup, redirecting without token');
        window.location.href = storedReturnUrl;
      }
      return;
    }
    // Second priority: Legacy redirect URI
    else if (storedRedirectUri) {
      console.log('MFA setup complete - redirecting to external URI:', storedRedirectUri);
      sessionStorage.removeItem('login_redirect_uri'); // Clean up
      window.location.href = storedRedirectUri;
      return;
    }
    
    // Default redirect based on user type
    if (this.roleService.hasAdminPrivileges()) {
      this.router.navigate(['/admin']);
    } else {
      this.router.navigate(['/profile']);
    }
  }
}
