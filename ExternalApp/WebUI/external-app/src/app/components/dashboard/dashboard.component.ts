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
    <div class="container">
      <!-- Authentication Check -->
      <ng-container *ngIf="authStatus$ | async as status">
        <div *ngIf="!status.authenticated" class="card">
          <div class="alert alert-error">
            <strong>🔐 Authentication Required</strong><br>
            You need to be logged in to access this dashboard.
          </div>
          <div style="text-align: center; margin-top: 20px;">
            <button (click)="login()" class="btn btn-primary">
              Login via User Management
            </button>
          </div>
        </div>
        
        <div *ngIf="status.authenticated">
          <!-- User Info -->
          <div class="card">
            <div class="card-header">
              <h1 class="card-title">📊 ExternalApp Dashboard</h1>
            </div>
            <div *ngIf="status.user">
              <div class="alert alert-success">
                <strong>✅ Successfully Authenticated</strong><br>
                Welcome, {{ status.user.email }}! You completed the authentication flow including any required MFA steps.
              </div>
              
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 20px;">
                <div>
                  <strong>User ID:</strong> {{ status.user.id }}
                </div>
                <div>
                  <strong>Email:</strong> {{ status.user.email }}
                </div>
                <div>
                  <strong>Roles:</strong> {{ status.user.roles.join(', ') }}
                </div>
                <div *ngIf="status.user.authenticated_at">
                  <strong>Authenticated:</strong> {{ status.user.authenticated_at | date:'short' }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- Dashboard Content -->
          <div *ngIf="dashboardData" class="card">
            <div class="card-header">
              <h2 class="card-title">{{ dashboardData.dashboard.title }}</h2>
            </div>
            
            <p style="font-size: 18px; color: #6b7280; margin-bottom: 24px;">
              {{ dashboardData.dashboard.message }}
            </p>
            
            <!-- Features -->
            <h3 style="margin-bottom: 16px; color: #374151;">🎯 Available Features</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-bottom: 32px;">
              <div *ngFor="let feature of dashboardData.dashboard.features" class="card" style="margin: 0; padding: 16px;">
                <div style="display: flex; align-items: center;">
                  <span style="margin-right: 8px;">✅</span>
                  {{ feature }}
                </div>
              </div>
            </div>
            
            <!-- Stats -->
            <h3 style="margin-bottom: 16px; color: #374151;">📈 Application Stats</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
              <div class="card" style="margin: 0; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #3b82f6;">
                  {{ dashboardData.dashboard.stats.total_users }}
                </div>
                <div style="color: #6b7280;">Total Users</div>
              </div>
              
              <div class="card" style="margin: 0; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #10b981;">
                  {{ dashboardData.dashboard.stats.active_sessions }}
                </div>
                <div style="color: #6b7280;">Active Sessions</div>
              </div>
              
              <div class="card" style="margin: 0; text-align: center;">
                <div style="font-size: 16px; font-weight: bold; color: #8b5cf6;">
                  {{ dashboardData.dashboard.stats.last_login | date:'short' }}
                </div>
                <div style="color: #6b7280;">Last Login</div>
              </div>
            </div>
          </div>
          
          <!-- Loading State -->
          <div *ngIf="!dashboardData && !error" class="card">
            <div style="text-align: center; padding: 40px;">
              <div class="loading-spinner" style="margin-bottom: 16px;"></div>
              <p>Loading dashboard data...</p>
            </div>
          </div>
          
          <!-- Error State -->
          <div *ngIf="error" class="card">
            <div class="alert alert-error">
              <strong>❌ Error Loading Dashboard</strong><br>
              {{ error }}
            </div>
            <button (click)="loadDashboardData()" class="btn btn-primary">
              Retry
            </button>
          </div>
          
          <!-- Actions -->
          <div class="card">
            <h3 style="margin-bottom: 16px; color: #374151;">🔧 Available Actions</h3>
            <div style="display: flex; gap: 16px; flex-wrap: wrap;">
              <button (click)="refreshData()" class="btn btn-secondary">
                🔄 Refresh Data
              </button>
              <a routerLink="/" class="btn btn-secondary" style="text-decoration: none;">
                🏠 Back to Home
              </a>
              <button (click)="logout()" class="btn btn-danger">
                🚪 Logout
              </button>
            </div>
          </div>
        </div>
      </ng-container>
    </div>
  `,
  styles: []
})
export class DashboardComponent implements OnInit {
  authStatus$: Observable<AuthStatus>;
  dashboardData: DashboardData | null = null;
  error: string | null = null;

  constructor(
    private authService: AuthService,
    private http: HttpClient,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.authStatus$ = this.authService.getAuthStatus();
  }

  ngOnInit(): void {
    // Check if we're returning from authentication
    this.route.queryParams.subscribe(params => {
      const authReturn = params['auth_return'];
      if (authReturn === 'true') {
        console.log('Detected return from User Management authentication to dashboard');
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

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.authService.clearSession();
        console.log('Logged out successfully');
        this.router.navigate(['/']);
      },
      error: (error) => {
        console.error('Error during logout:', error);
        // Clear session anyway
        this.authService.clearSession();
        this.router.navigate(['/']);
      }
    });
  }
}