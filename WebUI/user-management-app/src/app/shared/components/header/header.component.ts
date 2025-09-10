import { Component, Input, Output, EventEmitter, HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../services/auth';
import { RoleService } from '../../../services/role.service';
import { HeaderConfig } from '../../interfaces/header-config.interface';
import { APP_NAME } from '../../constants/app-constants';
import { ThemeSwitcher } from '../theme-switcher/theme-switcher';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, ThemeSwitcher],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent {
  @Input() config: HeaderConfig = {
    title: APP_NAME,
    subtitle: '',
    showUserMenu: true
  };

  @Output() profileClick = new EventEmitter<void>();
  @Output() adminClick = new EventEmitter<void>();
  @Output() logoutClick = new EventEmitter<void>();

  showDropdown = false;

  constructor(
    private router: Router,
    private authService: AuthService,
    private roleService: RoleService
  ) {}

  toggleDropdown(): void {
    this.showDropdown = !this.showDropdown;
  }

  getUserInitials(): string {
    if (this.config.userInitials) {
      return this.config.userInitials;
    }

    const email = this.authService.getUserEmail();
    if (email) {
      const emailParts = email.split('@')[0];
      if (emailParts.length >= 2) {
        return emailParts.substring(0, 2).toUpperCase();
      }
      return emailParts.substring(0, 1).toUpperCase() + 'U';
    }
    return 'U';
  }

  hasAdminPrivileges(): boolean {
    // Check if showAdminMenuItem is explicitly set to false
    if (this.config.showAdminMenuItem === false) {
      return false;
    }

    // Use centralized role service
    return this.roleService.hasAdminPrivileges();
  }

  navigateToProfile(): void {
    this.showDropdown = false;
    this.profileClick.emit();
  }

  navigateToAdmin(): void {
    this.showDropdown = false;
    this.adminClick.emit();
  }

  logout(): void {
    this.showDropdown = false;
    this.logoutClick.emit();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.relative')) {
      this.showDropdown = false;
    }
  }
}