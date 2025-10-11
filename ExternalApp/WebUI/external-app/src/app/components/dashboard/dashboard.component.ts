import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { AuthService, AuthStatus } from '../../services/auth.service';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

interface DashboardData {
  dashboard: {
    title: string;
    message: string;
    features: string[];
    stats: {
      total_users: number;
      active_sessions: number;
      last_login: string;
    };
  };
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="min-h-screen transition-colors duration-300 bg-green-light-50 dark:bg-green-dark-50">
      <div class="container mx-auto px-4 py-6">
        <!-- Authentication Check -->
        <ng-container *ngIf="authStatus$ | async as status">
          <div *ngIf="!status.authenticated" class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 transition-colors duration-300">
            <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-6">
              <strong class="text-red-700 dark:text-red-300">🔐 Authentication Required</strong><br>
              <span class="text-red-600 dark:text-red-400">You need to be logged in to access this dashboard.</span>
            </div>
            <div class="text-center">
              <button (click)="login()" 
                      class="bg-green-light-600 hover:bg-green-light-700 dark:bg-green-dark-600 dark:hover:bg-green-dark-700
                             text-white font-semibold px-6 py-3 rounded-lg transition-all duration-300
                             transform hover:scale-105 hover:shadow-lg">
                Login via User Management
              </button>
            </div>
          </div>
          
          <div *ngIf="status.authenticated" class="space-y-6">
            <!-- Welcome Section -->
            <div class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 transition-colors duration-300">
              <div class="border-b border-green-light-200 dark:border-green-dark-300 pb-4 mb-6">
                <h1 class="text-3xl font-bold text-green-light-900 dark:text-green-dark-900">📊 ExternalApp Dashboard</h1>
              </div>
              <div *ngIf="status.user">
                <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4 mb-6">
                  <strong class="text-green-700 dark:text-green-300">✅ Successfully Authenticated via OAuth PKCE</strong><br>
                  <span class="text-green-600 dark:text-green-400">
                    Welcome, {{ status.user.full_name || status.user.email }}! You completed the OAuth authentication flow including any required MFA steps.
                  </span>
                </div>
                
                <!-- Profile and Logout Links -->
                <div class="flex gap-4 p-4 bg-green-light-50 dark:bg-green-dark-200 rounded-lg">
                  <button (click)="showProfile()" 
                          class="bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800
                                 text-white font-semibold px-4 py-2 rounded-lg transition-all duration-300
                                 transform hover:scale-105">
                    👤 Profile
                  </button>
                  <button (click)="logout()" 
                          class="bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800
                                 text-white font-semibold px-4 py-2 rounded-lg transition-all duration-300
                                 transform hover:scale-105">
                    🚪 Logout
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Profile Details (shown when Profile is clicked) -->
            <div *ngIf="showProfileDetails && status.user" 
                 class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 transition-colors duration-300">
              <div class="border-b border-green-light-200 dark:border-green-dark-300 pb-4 mb-6">
                <h2 class="text-2xl font-semibold text-green-light-900 dark:text-green-dark-900">👤 User Profile</h2>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
                  <strong class="text-green-light-700 dark:text-green-dark-700">User ID:</strong>
                  <span class="text-green-light-600 dark:text-green-dark-600"> {{ status.user.id }}</span>
                </div>
                <div class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
                  <strong class="text-green-light-700 dark:text-green-dark-700">Email:</strong>
                  <span class="text-green-light-600 dark:text-green-dark-600"> {{ status.user.email }}</span>
                </div>
                <div *ngIf="status.user.full_name" class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
                  <strong class="text-green-light-700 dark:text-green-dark-700">Name:</strong>
                  <span class="text-green-light-600 dark:text-green-dark-600"> {{ status.user.full_name }}</span>
                </div>
                <div class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
                  <strong class="text-green-light-700 dark:text-green-dark-700">Admin:</strong>
                  <span class="text-green-light-600 dark:text-green-dark-600"> {{ status.user.is_admin ? 'Yes' : 'No' }}</span>
                </div>
                <div class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
                  <strong class="text-green-light-700 dark:text-green-dark-700">Roles:</strong>
                  <span class="text-green-light-600 dark:text-green-dark-600"> {{ status.user.roles.join(', ') || 'None' }}</span>
                </div>
                <div *ngIf="status.user.authenticated_at" class="bg-green-light-50 dark:bg-green-dark-200 p-3 rounded border border-green-light-200 dark:border-green-dark-300">
                  <strong class="text-green-light-700 dark:text-green-dark-700">Authenticated:</strong>
                  <span class="text-green-light-600 dark:text-green-dark-600"> {{ status.user.authenticated_at | date:'short' }}</span>
                </div>
              </div>
            </div>
            
            <!-- Dashboard Content -->
            <div *ngIf="dashboardData" class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 transition-colors duration-300">
              <div class="border-b border-green-light-200 dark:border-green-dark-300 pb-4 mb-6">
                <h2 class="text-2xl font-semibold text-green-light-900 dark:text-green-dark-900">{{ dashboardData.dashboard.title }}</h2>
              </div>
              
              <p class="text-lg text-green-light-700 dark:text-green-dark-700 mb-6 leading-relaxed">
                {{ dashboardData.dashboard.message }}
              </p>
              
              <!-- Features -->
              <h3 class="text-xl font-semibold text-green-light-800 dark:text-green-dark-800 mb-4">🎯 Available Features</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                <div *ngFor="let feature of dashboardData.dashboard.features" 
                     class="bg-green-light-100 dark:bg-green-dark-200 p-4 rounded-lg border border-green-light-200 dark:border-green-dark-300">
                  <div class="flex items-center text-green-light-700 dark:text-green-dark-700">
                    <span class="mr-2">✅</span>
                    {{ feature }}
                  </div>
                </div>
              </div>
              
              <!-- Stats -->
              <h3 class="text-xl font-semibold text-green-light-800 dark:text-green-dark-800 mb-4">📈 Application Stats</h3>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg text-center border border-blue-200 dark:border-blue-700">
                  <div class="text-3xl font-bold text-blue-600 dark:text-blue-400">
                    {{ dashboardData.dashboard.stats.total_users }}
                  </div>
                  <div class="text-blue-500 dark:text-blue-300">Total Users</div>
                </div>
                
                <div class="bg-emerald-50 dark:bg-emerald-900/20 p-6 rounded-lg text-center border border-emerald-200 dark:border-emerald-700">
                  <div class="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
                    {{ dashboardData.dashboard.stats.active_sessions }}
                  </div>
                  <div class="text-emerald-500 dark:text-emerald-300">Active Sessions</div>
                </div>
                
                <div class="bg-purple-50 dark:bg-purple-900/20 p-6 rounded-lg text-center border border-purple-200 dark:border-purple-700">
                  <div class="text-lg font-bold text-purple-600 dark:text-purple-400">
                    {{ dashboardData.dashboard.stats.last_login | date:'short' }}
                  </div>
                  <div class="text-purple-500 dark:text-purple-300">Last Login</div>
                </div>
              </div>
            </div>
            
            <!-- Loading State -->
            <div *ngIf="!dashboardData && !error" class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 transition-colors duration-300">
              <div class="text-center py-10">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-light-600 dark:border-green-dark-600 mx-auto mb-4"></div>
                <p class="text-green-light-700 dark:text-green-dark-700">Loading dashboard data...</p>
              </div>
            </div>
            
            <!-- Error State -->
            <div *ngIf="error" class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 transition-colors duration-300">
              <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-4">
                <strong class="text-red-700 dark:text-red-300">❌ Error Loading Dashboard</strong><br>
                <span class="text-red-600 dark:text-red-400">{{ error }}</span>
              </div>
              <button (click)="loadDashboardData()" 
                      class="bg-green-light-600 hover:bg-green-light-700 dark:bg-green-dark-600 dark:hover:bg-green-dark-700
                             text-white font-semibold px-4 py-2 rounded-lg transition-all duration-300
                             transform hover:scale-105">
                Retry
              </button>
            </div>
            
            <!-- Actions -->
            <div class="bg-white dark:bg-green-dark-100 rounded-lg shadow-lg p-6 transition-colors duration-300">
              <h3 class="text-xl font-semibold text-green-light-800 dark:text-green-dark-800 mb-4">🔧 Available Actions</h3>
              <div class="flex gap-4 flex-wrap">
                <button (click)="refreshData()" 
                        class="bg-gray-600 hover:bg-gray-700 dark:bg-gray-700 dark:hover:bg-gray-800
                               text-white font-semibold px-4 py-2 rounded-lg transition-all duration-300
                               transform hover:scale-105">
                  🔄 Refresh Data
                </button>
                <a routerLink="/" 
                   class="bg-gray-600 hover:bg-gray-700 dark:bg-gray-700 dark:hover:bg-gray-800
                          text-white font-semibold px-4 py-2 rounded-lg transition-all duration-300
                          transform hover:scale-105 no-underline">
                  🏠 Back to Home
                </a>
                <button (click)="logout()" 
                        class="bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800
                               text-white font-semibold px-4 py-2 rounded-lg transition-all duration-300
                               transform hover:scale-105">
                  🚪 Logout
                </button>
              </div>
            </div>
          </div>
        </ng-container>
      </div>
    </div>
  `,
  styles: []
})
export class DashboardComponent implements OnInit {
  authStatus$: Observable<AuthStatus>;
  dashboardData: DashboardData | null = null;
  error: string | null = null;
  showProfileDetails: boolean = false;

  constructor(
    private authService: AuthService,
    private http: HttpClient,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.authStatus$ = this.authService.getAuthStatus();
  }

  ngOnInit(): void {
    // Check if we're returning from OAuth authentication
    this.route.queryParams.subscribe(params => {
      const sessionId = params['session_id'];
      const authSuccess = params['auth_success'];
      const authReturn = params['auth_return'];
      
      if (sessionId || authSuccess) {
        console.log('Detected return from OAuth authentication to dashboard');
        const urlParams = new URLSearchParams(window.location.search);
        this.authService.handleOAuthReturn(urlParams);
        
        // Clean up URL
        this.router.navigate(['/dashboard'], { replaceUrl: true });
      } else if (authReturn === 'true') {
        console.log('Detected legacy return from User Management authentication to dashboard');
        this.authService.handleAuthReturn(params);
        
        // Clean up URL
        this.router.navigate(['/dashboard'], { replaceUrl: true });
      }
    });

    // Check authentication and load data
    this.authStatus$.subscribe(status => {
      if (status.authenticated) {
        this.loadDashboardData();
      }
    });
  }

  loadDashboardData(): void {
    this.error = null;
    
    this.http.get<DashboardData>(`${environment.apiUrl}/dashboard/data`).subscribe({
      next: (data) => {
        this.dashboardData = data;
        console.log('Dashboard data loaded:', data);
      },
      error: (error) => {
        console.error('Error loading dashboard data:', error);
        this.error = 'Failed to load dashboard data. Please try again.';
      }
    });
  }

  refreshData(): void {
    this.dashboardData = null;
    this.loadDashboardData();
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

  showProfile(): void {
    this.showProfileDetails = !this.showProfileDetails;
  }

  logout(): void {
    // Call logout on both UserManagement API and local session
    this.http.post('http://localhost:8001/auth/logout', {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
      }
    }).subscribe({
      next: () => {
        console.log('Logged out from User Management API');
      },
      error: (error) => {
        console.warn('Warning: Failed to logout from User Management API:', error);
      },
      complete: () => {
        // Always clear local session regardless of API call result
        this.authService.logout().subscribe({
          next: () => {
            this.authService.clearSession();
            console.log('Logged out successfully from ExternalApp');
            this.router.navigate(['/home']);
          },
          error: (error) => {
            console.error('Error during ExternalApp logout:', error);
            // Clear session anyway
            this.authService.clearSession();
            this.router.navigate(['/home']);
          }
        });
      }
    });
  }
}