import { Component, OnInit, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { UserService, UserRolesResponse } from '../../services/user';
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
  userRoles: UserRolesResponse | null = null;
  mfaPromptDismissed = false;
  
  // Tab management
  currentTab: string = 'profile';
  isLoadingRoles = false;
  rolesError: string | null = null;

  constructor(
    private authService: AuthService,
    private userProfileService: UserProfileService,
    private userService: UserService,
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
          
          // Load user roles when switching to roles tab or on init if needed
          if (this.currentTab === 'roles') {
            this.loadUserRoles();
          }
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

  // Tab management methods
  selectTab(tabId: string): void {
    this.currentTab = tabId;
    
    // Load roles data when switching to roles tab
    if (tabId === 'roles' && !this.userRoles && this.user) {
      this.loadUserRoles();
    }
  }

  // Load user roles data
  loadUserRoles(): void {
    if (this.isLoadingRoles) {
      return;
    }
    
    this.isLoadingRoles = true;
    this.rolesError = null;
    
    this.userService.getMyRoles().subscribe({
      next: (roles) => {
        this.userRoles = roles;
        this.isLoadingRoles = false;
      },
      error: (error) => {
        console.error('Error loading user roles:', error);
        this.rolesError = 'Failed to load role information. Please try again later.';
        this.isLoadingRoles = false;
      }
    });
  }

  // Utility method to group functional roles by category
  getFunctionalRolesByCategory(): {[key: string]: any[]} {
    if (!this.userRoles || !this.userRoles.functional_roles) {
      return {};
    }
    
    return this.userRoles.functional_roles.reduce((groups: {[key: string]: any[]}, role) => {
      const category = role.functional_role_category || 'Other';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(role);
      return groups;
    }, {});
  }

  // Get source display text
  getSourceDisplayText(source: string): string {
    switch (source) {
      case 'direct':
        return 'Directly Assigned';
      case 'business_unit':
        return 'From Business Unit';
      case 'organization':
        return 'From Organization';
      default:
        return source;
    }
  }

  // Get source CSS class for styling
  getSourceCssClass(source: string): string {
    switch (source) {
      case 'direct':
        return 'text-blue-600 bg-blue-50';
      case 'business_unit':
        return 'text-green-600 bg-green-50';
      case 'organization':
        return 'text-purple-600 bg-purple-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  }
}
