import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService, AuthStatus } from '../../services/auth.service';
import { TailwindThemeToggleComponent } from '../tailwind-theme-toggle/tailwind-theme-toggle.component';
import { TailwindThemeService } from '../../services/tailwind-theme.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule, TailwindThemeToggleComponent],
  template: `
    <nav class="navbar">
      <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
          <a routerLink="/" class="navbar-brand">
            🚀 ExternalApp
          </a>
          
          <div class="navbar-nav">
            <app-tailwind-theme-toggle></app-tailwind-theme-toggle>
            
            <ng-container *ngIf="authStatus$ | async as status">
              <ng-container *ngIf="status.authenticated && status.user">
                <span class="nav-link">Welcome, {{ status.user.email }}</span>
                <a routerLink="/dashboard" class="nav-link">Dashboard</a>
                <a routerLink="/profile" class="nav-link profile-link">👤 Profile</a>
                <button (click)="logout()" class="btn btn-danger logout-btn" style="padding: 8px 16px; font-size: 14px;">
                  🚪 Logout
                </button>
              </ng-container>
              
              <ng-container *ngIf="!status.authenticated">
                <button (click)="login()" class="btn btn-primary" style="padding: 8px 16px; font-size: 14px;">
                  Login via User Management
                </button>
              </ng-container>
            </ng-container>
          </div>
        </div>
      </div>
    </nav>
  `,
  styles: []
})
export class HeaderComponent implements OnInit {
  authStatus$: Observable<AuthStatus>;

  constructor(
    private authService: AuthService,
    private themeService: TailwindThemeService
  ) {
    this.authStatus$ = this.authService.getAuthStatus();
  }

  ngOnInit(): void {
    // Check auth status on component initialization
    this.authService.checkAuthStatus();
  }

  login(): void {
    const returnUrl = `${window.location.origin}/dashboard`;
    const selectedThemeUrl = this.themeService.selectedThemeUrl;
    
    this.authService.initiateLogin(returnUrl, selectedThemeUrl).subscribe({
      next: (response) => {
        if (response.success && response.login_url) {
          console.log('Redirecting to User Management for login:', response.login_url);
          window.location.href = response.login_url;
        }
      },
      error: (error) => {
        console.error('Error initiating login:', error);
        alert('Failed to initiate login. Please try again.');
      }
    });
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.authService.clearSession();
        console.log('Logged out successfully');
      },
      error: (error) => {
        console.error('Error during logout:', error);
        // Clear session anyway
        this.authService.clearSession();
      }
    });
  }
}