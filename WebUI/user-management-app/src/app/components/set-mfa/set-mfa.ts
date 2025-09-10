import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { RoleService } from '../../services/role.service';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-set-mfa',
  imports: [CommonModule, FormsModule, HeaderComponent],
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
  qrCodeBase64: string | null = null;
  secret: string | null = null;
  provisioningUri: string | null = null;
  loading = false;
  error: string | null = null;
  success = false;
  userEmail: string | null = null;
  showPrompt = true; // Start with prompt instead of auto-generating

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
    // User confirmed they want to set up MFA
    this.showPrompt = false;
    this.setupMfa();
  }

  setupMfa(): void {
    this.loading = true;
    this.error = null;

    this.authService.setupMfa().subscribe({
      next: (response) => {
        this.qrCodeBase64 = response.qr_code_base64;
        this.secret = response.secret;
        this.provisioningUri = response.provisioning_uri;
        this.success = true;
        this.loading = false;
      },
      error: (error) => {
        console.error('MFA setup error:', error);
        this.error = error.error?.detail || 'Failed to setup MFA. Please try again.';
        this.loading = false;
      }
    });
  }

  copySecret(): void {
    if (this.secret) {
      navigator.clipboard.writeText(this.secret).then(() => {
        // You might want to show a toast notification here
      });
    }
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
    // Redirect based on user type
    if (this.roleService.hasAdminPrivileges()) {
      this.router.navigate(['/admin']);
    } else {
      this.router.navigate(['/profile']);
    }
  }
}
