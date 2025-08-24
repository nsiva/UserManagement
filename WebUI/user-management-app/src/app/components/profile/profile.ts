import { Component, OnInit, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { UserService } from '../../services/user';
import { UserProfileService } from '../../services/user-profile.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-profile',
  imports: [FormsModule, CommonModule],
  templateUrl: './profile.html',
  styleUrls: ['./profile.scss']
})
export class ProfileComponent implements OnInit {
  user: any;
  showDropdown = false;

  constructor(
    private authService: AuthService,
    private userProfileService: UserProfileService,
    private router: Router
  ) {}

  ngOnInit(): void {
    (async () => {
      if (!this.authService.isLoggedIn()) {
        this.router.navigate(['/login']);
        return;
      }
      const userId = this.authService.getUserId();
      if (userId) {
        try {
          const user = await import('rxjs').then(rxjs => rxjs.firstValueFrom(this.userProfileService.getCurrentUserProfile()));
          this.user = user;
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
