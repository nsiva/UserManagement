import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-set-mfa',
  imports: [CommonModule, FormsModule],
  templateUrl: './set-mfa.html',
  styleUrl: './set-mfa.scss'
})
export class SetMfaComponent implements OnInit {
  qrCodeBase64: string | null = null;
  secret: string | null = null;
  provisioningUri: string | null = null;
  loading = false;
  error: string | null = null;
  success = false;
  showDropdown = false;
  userEmail: string | null = null;
  showPrompt = true; // Start with prompt instead of auto-generating

  constructor(
    private authService: AuthService,
    private router: Router
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

  toggleDropdown(): void {
    this.showDropdown = !this.showDropdown;
  }

  getUserInitials(): string {
    if (this.userEmail) {
      return this.userEmail.charAt(0).toUpperCase();
    }
    return 'U';
  }

  navigateToProfile(): void {
    this.router.navigate(['/profile']);
  }

  navigateToAdmin(): void {
    this.router.navigate(['/admin']);
  }

  logout(): void {
    this.authService.logout();
  }

  isAdmin(): boolean {
    return this.authService.isAdmin();
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
    if (this.authService.isAdmin()) {
      this.router.navigate(['/admin']);
    } else {
      this.router.navigate(['/profile']);
    }
  }
}
