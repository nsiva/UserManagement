import { Component, OnInit, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { UserService } from '../../services/user';
import { UserProfileService, UserProfile } from '../../services/user-profile.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';

@Component({
  selector: 'app-profile',
  imports: [FormsModule, CommonModule, HeaderComponent],
  templateUrl: './profile.html',
  styleUrls: ['./profile.scss']
})
export class ProfileComponent implements OnInit {
  // Header configuration
  headerConfig: HeaderConfig = {
    title: 'User Management Application',
    subtitle: 'Profile Page',
    showUserMenu: true
  };
  user: UserProfile | null = null;
  showDropdown = false;
  mfaPromptDismissed = false;

  constructor(
    private authService: AuthService,
    private userProfileService: UserProfileService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Update header config based on admin status
    this.headerConfig = {
      ...this.headerConfig,
      showAdminMenuItem: this.isAdmin()
    };

    (async () => {
      if (!this.authService.isLoggedIn()) {
        this.router.navigate(['/login']);
        return;
      }
      
      // Check if MFA prompt was previously dismissed
      this.mfaPromptDismissed = localStorage.getItem('mfa_prompt_dismissed') === 'true';
      
      const userId = this.authService.getUserId();
      if (userId) {
        try {
          const user = await import('rxjs').then(rxjs => rxjs.firstValueFrom(this.userProfileService.getCurrentUserProfile()));
          this.user = user;
          // Debug logging removed for production
        } catch (error) {
          console.error('Error fetching user profile:', error);
          this.router.navigate(['/login']);
        }
      } else {
        console.error('No user ID found in authentication service.');
        this.router.navigate(['/login']);
      }
    })();
  }

  toggleDropdown(): void {
    this.showDropdown = !this.showDropdown;
  }

  navigateToProfile(): void {
    this.showDropdown = false;
    // Already on profile page, just close dropdown
  }

  navigateToAdmin(): void {
    this.showDropdown = false;
    this.router.navigate(['/admin']);
  }

  navigateToResetPassword(): void {
    this.router.navigate(['/reset-password']);
  }

  navigateToSetMfa(): void {
    this.showDropdown = false;
    this.router.navigate(['/set-mfa']);
  }

  dismissMfaPrompt(): void {
    this.mfaPromptDismissed = true;
    // Optionally store this in localStorage to persist across sessions
    localStorage.setItem('mfa_prompt_dismissed', 'true');
  }

  // Method to reset MFA prompt dismissal (useful for testing)
  resetMfaPromptDismissal(): void {
    this.mfaPromptDismissed = false;
    localStorage.removeItem('mfa_prompt_dismissed');
  }

  isAdmin(): boolean {
    return this.authService.isAdmin();
  }

  getUserInitials(): string {
    // If user data is loaded and has first/last name, use them
    if (this.user && this.user.first_name && this.user.last_name) {
      return (this.user.first_name.charAt(0) + this.user.last_name.charAt(0)).toUpperCase();
    }
    
    // If only first name is available
    if (this.user && this.user.first_name) {
      return (this.user.first_name.charAt(0) + (this.user.first_name.charAt(1) || 'U')).toUpperCase();
    }
    
    // Fall back to email from auth service
    const email = this.authService.getUserEmail();
    if (!email) return 'U';
    
    const emailParts = email.split('@')[0];
    if (emailParts.length >= 2) {
      return emailParts.substring(0, 2).toUpperCase();
    }
    return emailParts.substring(0, 1).toUpperCase() + 'U';
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.relative')) {
      this.showDropdown = false;
    }
  }

  logout(): void {
    this.showDropdown = false;
    this.authService.logout();
  }
}
