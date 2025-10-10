import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService, AuthStatus } from '../../services/auth.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="container">
      <div class="card">
        <div class="card-header">
          <h1 class="card-title">🚀 Welcome to ExternalApp</h1>
        </div>
        
        <div>
          <p style="font-size: 18px; color: #6b7280; margin-bottom: 24px;">
            This is a demonstration application showing how external applications can integrate 
            with the User Management system for seamless authentication.
          </p>
          
          <ng-container *ngIf="authStatus$ | async as status">
            <div *ngIf="!status.authenticated" class="alert alert-info">
              <strong>🔐 Authentication Required</strong><br>
              To access protected features, please log in through the User Management system.
              This will redirect you to the User Management login page and bring you back here after successful authentication.
            </div>
            
            <div *ngIf="status.authenticated && status.user" class="alert alert-success">
              <strong>✅ Welcome back, {{ status.user.email }}!</strong><br>
              You are successfully authenticated. You can now access the protected dashboard.
            </div>
          </ng-container>
          
          <h2 style="margin-top: 32px; margin-bottom: 16px; color: #374151;">🎯 Integration Features</h2>
          
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 32px;">
            <div class="card" style="margin: 0;">
              <h3 style="color: #3b82f6; margin-bottom: 12px;">🔄 Seamless Redirect</h3>
              <p style="color: #6b7280;">
                Users are redirected to User Management for authentication and brought back 
                to the external application automatically.
              </p>
            </div>
            
            <div class="card" style="margin: 0;">
              <h3 style="color: #3b82f6; margin-bottom: 12px;">🛡️ MFA Support</h3>
              <p style="color: #6b7280;">
                Full support for Multi-Factor Authentication through the User Management system, 
                including TOTP codes and backup options.
              </p>
            </div>
            
            <div class="card" style="margin: 0;">
              <h3 style="color: #3b82f6; margin-bottom: 12px;">🎨 Custom UI</h3>
              <p style="color: #6b7280;">
                External applications maintain their own UI and branding while leveraging 
                centralized authentication infrastructure.
              </p>
            </div>
          </div>
          
          <div style="text-align: center; margin-top: 32px;">
            <ng-container *ngIf="authStatus$ | async as status">
              <button 
                *ngIf="!status.authenticated" 
                (click)="login()" 
                class="btn btn-primary"
                style="font-size: 18px; padding: 16px 32px;">
                🔐 Login via User Management
              </button>
              
              <a 
                *ngIf="status.authenticated" 
                routerLink="/dashboard" 
                class="btn btn-primary"
                style="font-size: 18px; padding: 16px 32px; text-decoration: none;">
                📊 Go to Dashboard
              </a>
            </ng-container>
          </div>
        </div>
      </div>
      
      <div class="card">
        <h2 style="margin-bottom: 16px; color: #374151;">🔧 Technical Details</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
          <div>
            <strong>Frontend:</strong> Angular 20 (Port 4202)
          </div>
          <div>
            <strong>Backend:</strong> FastAPI (Port 8002)
          </div>
          <div>
            <strong>User Management:</strong> localhost:4201
          </div>
          <div>
            <strong>Authentication:</strong> redirect_uri parameter
          </div>
        </div>
      </div>
    </div>
  `,
  styles: []
})
export class HomeComponent implements OnInit {
  authStatus$: Observable<AuthStatus>;

  constructor(private authService: AuthService) {
    this.authStatus$ = this.authService.getAuthStatus();
  }

  ngOnInit(): void {
    // Check if we're returning from authentication
    const urlParams = new URLSearchParams(window.location.search);
    const authReturn = urlParams.get('auth_return');
    
    if (authReturn === 'true') {
      console.log('Detected return from User Management authentication');
      this.authService.handleAuthReturn(urlParams);
      
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }

  login(): void {
    const returnUrl = `${window.location.origin}/dashboard`;
    
    this.authService.initiateLogin(returnUrl).subscribe({
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
}