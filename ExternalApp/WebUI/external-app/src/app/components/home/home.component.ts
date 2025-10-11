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
    <div class="min-h-screen transition-colors duration-300 bg-green-light-50 dark:bg-green-dark-50">
      <div class="container mx-auto px-4 py-8">
        <div class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 mb-6 transition-colors duration-300">
          <div class="border-b border-green-light-200 dark:border-green-dark-300 pb-4 mb-6">
            <h1 class="text-3xl font-bold text-green-light-900 dark:text-green-dark-900">🚀 Welcome to ExternalApp</h1>
          </div>
          
          <div>
            <p class="text-lg text-green-light-700 dark:text-green-dark-700 mb-6 leading-relaxed">
              This is a demonstration application showing how external applications can integrate 
              with the User Management system for seamless authentication.
            </p>
            
            <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-8">
              <strong class="text-blue-700 dark:text-blue-300">🔐 Authentication Required</strong><br>
              <span class="text-blue-600 dark:text-blue-400">
                Welcome to ExternalApp! To access the application features, please log in through the User Management system.
                This will securely authenticate you and redirect you to the dashboard.
              </span>
            </div>
            
            <h2 class="text-2xl font-semibold text-green-light-800 dark:text-green-dark-800 mt-8 mb-4">🎯 Integration Features</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              <div class="bg-green-light-100 dark:bg-green-dark-200 rounded-lg p-4 border border-green-light-200 dark:border-green-dark-300">
                <h3 class="text-green-light-600 dark:text-green-dark-600 font-semibold mb-3">🔄 Seamless Redirect</h3>
                <p class="text-green-light-700 dark:text-green-dark-700 text-sm">
                  Users are redirected to User Management for authentication and brought back 
                  to the external application automatically.
                </p>
              </div>
              
              <div class="bg-green-light-100 dark:bg-green-dark-200 rounded-lg p-4 border border-green-light-200 dark:border-green-dark-300">
                <h3 class="text-green-light-600 dark:text-green-dark-600 font-semibold mb-3">🛡️ MFA Support</h3>
                <p class="text-green-light-700 dark:text-green-dark-700 text-sm">
                  Full support for Multi-Factor Authentication through the User Management system, 
                  including TOTP codes and backup options.
                </p>
              </div>
              
              <div class="bg-green-light-100 dark:bg-green-dark-200 rounded-lg p-4 border border-green-light-200 dark:border-green-dark-300">
                <h3 class="text-green-light-600 dark:text-green-dark-600 font-semibold mb-3">🎨 Custom UI</h3>
                <p class="text-green-light-700 dark:text-green-dark-700 text-sm">
                  External applications maintain their own UI and branding while leveraging 
                  centralized authentication infrastructure.
                </p>
              </div>
            </div>
            
            <div class="text-center mt-8">
              <button 
                (click)="login()" 
                class="bg-green-light-600 hover:bg-green-light-700 dark:bg-green-dark-600 dark:hover:bg-green-dark-700
                       text-white font-semibold px-8 py-4 rounded-lg transition-all duration-300
                       transform hover:scale-105 hover:shadow-lg text-lg">
                🔐 Login via User Management
              </button>
            </div>
          </div>
        </div>
        
        <div class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 transition-colors duration-300">
          <h2 class="text-xl font-semibold text-green-light-800 dark:text-green-dark-800 mb-4">🔧 Technical Details</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
              <strong class="text-green-light-700 dark:text-green-dark-700">Frontend:</strong>
              <span class="text-green-light-600 dark:text-green-dark-600"> Angular 20 (Port 4202)</span>
            </div>
            <div class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
              <strong class="text-green-light-700 dark:text-green-dark-700">Backend:</strong>
              <span class="text-green-light-600 dark:text-green-dark-600"> FastAPI (Port 8002)</span>
            </div>
            <div class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
              <strong class="text-green-light-700 dark:text-green-dark-700">User Management:</strong>
              <span class="text-green-light-600 dark:text-green-dark-600"> localhost:4201</span>
            </div>
            <div class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
              <strong class="text-green-light-700 dark:text-green-dark-700">Authentication:</strong>
              <span class="text-green-light-600 dark:text-green-dark-600"> OAuth 2.0 PKCE</span>
            </div>
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
    // Home page doesn't need OAuth handling - that's handled in dashboard
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