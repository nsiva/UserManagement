import { Component, OnInit, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { UserService } from '../../services/user';
import { UserProfileService, UserProfile } from '../../services/user-profile.service';
import { RoleService } from '../../services/role.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-profile',
  imports: [FormsModule, CommonModule, HeaderComponent],
  templateUrl: './profile.html',
  styleUrls: ['./profile.scss']
})
export class ProfileComponent implements OnInit {
  // Header configuration
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.PROFILE,
    showUserMenu: true
  };
  user: UserProfile | null = null;
  mfaPromptDismissed = false;

  constructor(
    private authService: AuthService,
    private userProfileService: UserProfileService,
    private router: Router,
    private roleService: RoleService
  ) {}

  ngOnInit(): void {
    // Update header config based on admin status
    this.headerConfig = {
      ...this.headerConfig,
      showAdminMenuItem: this.roleService.hasAdminPrivileges()
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

  // Header event handlers
  navigateToProfile(): void {
    // Already on profile page, no navigation needed
  }

  navigateToAdmin(): void {
    this.router.navigate(['/admin']);
  }

  navigateToResetPassword(): void {
    this.router.navigate(['/reset-password']);
  }

  navigateToSetMfa(): void {
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



  logout(): void {
    this.authService.logout();
  }
}
