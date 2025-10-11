import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService, User } from '../../services/auth.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

interface DetailedUserProfile {
  id: string;
  email: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  full_name?: string;
  roles: string[];
  is_admin: boolean;
  authenticated_at?: string;
  mfa_enabled?: boolean;
  created_at?: string;
  updated_at?: string;
  organization?: string;
  business_unit?: string;
}

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container">
      <div class="card">
        <div class="card-header">
          <h1 class="card-title">👤 User Profile</h1>
          <p style="color: #6b7280; margin: 0;">
            Profile information retrieved from User Management system
          </p>
        </div>
        
        <div *ngIf="!isAuthenticated" class="alert alert-warning">
          <strong>⚠️ Not Authenticated</strong><br>
          You must be logged in to view your profile information.
          <div style="margin-top: 16px;">
            <button (click)="login()" class="btn btn-primary">
              🔐 Login via User Management
            </button>
          </div>
        </div>

        <div *ngIf="isAuthenticated && profile" class="profile-content">
          <!-- Basic Information -->
          <div class="profile-section">
            <h2 class="section-title">📋 Basic Information</h2>
            <div class="profile-grid">
              <div class="profile-item">
                <label>Full Name:</label>
                <span>{{ profile.full_name || 'Not provided' }}</span>
              </div>
              <div class="profile-item">
                <label>Email:</label>
                <span>{{ profile.email }}</span>
              </div>
              <div class="profile-item">
                <label>User ID:</label>
                <span class="monospace">{{ profile.id }}</span>
              </div>
              <div class="profile-item">
                <label>Account Type:</label>
                <span class="badge" [class.admin]="profile.is_admin" [class.user]="!profile.is_admin">
                  {{ profile.is_admin ? 'Administrator' : 'User' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Security Information -->
          <div class="profile-section">
            <h2 class="section-title">🔒 Security</h2>
            <div class="profile-grid">
              <div class="profile-item">
                <label>Multi-Factor Authentication:</label>
                <span class="badge" [class.enabled]="profile.mfa_enabled" [class.disabled]="!profile.mfa_enabled">
                  {{ profile.mfa_enabled ? '✅ Enabled' : '❌ Disabled' }}
                </span>
              </div>
              <div class="profile-item">
                <label>Last Login:</label>
                <span>{{ profile.authenticated_at | date:'medium' }}</span>
              </div>
            </div>
          </div>

          <!-- Roles and Permissions -->
          <div class="profile-section">
            <h2 class="section-title">👥 Roles & Permissions</h2>
            <div class="roles-container">
              <div *ngIf="profile.roles && profile.roles.length > 0; else noRoles">
                <div class="role-badges">
                  <span *ngFor="let role of profile.roles" class="role-badge">
                    {{ role }}
                  </span>
                </div>
              </div>
              <ng-template #noRoles>
                <span class="no-data">No roles assigned</span>
              </ng-template>
            </div>
          </div>

          <!-- Organization Information -->
          <div class="profile-section" *ngIf="profile.organization || profile.business_unit">
            <h2 class="section-title">🏢 Organization</h2>
            <div class="profile-grid">
              <div class="profile-item" *ngIf="profile.organization">
                <label>Organization:</label>
                <span>{{ profile.organization }}</span>
              </div>
              <div class="profile-item" *ngIf="profile.business_unit">
                <label>Business Unit:</label>
                <span>{{ profile.business_unit }}</span>
              </div>
            </div>
          </div>

          <!-- Account Details -->
          <div class="profile-section">
            <h2 class="section-title">📅 Account Details</h2>
            <div class="profile-grid">
              <div class="profile-item" *ngIf="profile.created_at">
                <label>Account Created:</label>
                <span>{{ profile.created_at | date:'medium' }}</span>
              </div>
              <div class="profile-item" *ngIf="profile.updated_at">
                <label>Last Updated:</label>
                <span>{{ profile.updated_at | date:'medium' }}</span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="profile-actions">
            <button (click)="refreshProfile()" class="btn btn-secondary" [disabled]="isLoading">
              🔄 {{ isLoading ? 'Refreshing...' : 'Refresh Profile' }}
            </button>
            <button (click)="logout()" class="btn btn-outline">
              🚪 Logout
            </button>
            <button (click)="goHome()" class="btn btn-primary">
              🏠 Back to Home
            </button>
          </div>
        </div>

        <div *ngIf="isAuthenticated && !profile && !isLoading" class="alert alert-error">
          <strong>❌ Profile Load Error</strong><br>
          Unable to load profile information. Please try refreshing or contact support.
        </div>

        <div *ngIf="isLoading" class="loading-state">
          <div class="spinner"></div>
          <span>Loading profile information...</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .container {
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }

    .card {
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      overflow: hidden;
    }

    .card-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 24px;
      text-align: center;
    }

    .card-title {
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 600;
    }

    .profile-content {
      padding: 24px;
    }

    .profile-section {
      margin-bottom: 32px;
    }

    .section-title {
      color: #374151;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 2px solid #e5e7eb;
      font-size: 20px;
      font-weight: 600;
    }

    .profile-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
    }

    .profile-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .profile-item label {
      font-weight: 600;
      color: #374151;
      font-size: 14px;
    }

    .profile-item span {
      color: #6b7280;
      padding: 8px 12px;
      background: #f9fafb;
      border-radius: 6px;
      border: 1px solid #e5e7eb;
    }

    .monospace {
      font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace !important;
      font-size: 13px !important;
    }

    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .badge.admin {
      background: #fef3c7;
      color: #92400e;
    }

    .badge.user {
      background: #dbeafe;
      color: #1e40af;
    }

    .badge.enabled {
      background: #d1fae5;
      color: #065f46;
    }

    .badge.disabled {
      background: #fee2e2;
      color: #991b1b;
    }

    .roles-container {
      margin-top: 8px;
    }

    .role-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .role-badge {
      background: #e0e7ff;
      color: #3730a3;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 500;
    }

    .no-data {
      color: #9ca3af;
      font-style: italic;
    }

    .profile-actions {
      display: flex;
      gap: 12px;
      justify-content: center;
      margin-top: 32px;
      padding-top: 24px;
      border-top: 1px solid #e5e7eb;
      flex-wrap: wrap;
    }

    .btn {
      padding: 12px 24px;
      border-radius: 8px;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      font-size: 14px;
    }

    .btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .btn-primary {
      background: #3b82f6;
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      background: #2563eb;
    }

    .btn-secondary {
      background: #6b7280;
      color: white;
    }

    .btn-secondary:hover:not(:disabled) {
      background: #4b5563;
    }

    .btn-outline {
      background: transparent;
      color: #6b7280;
      border: 2px solid #d1d5db;
    }

    .btn-outline:hover {
      background: #f9fafb;
      border-color: #9ca3af;
    }

    .alert {
      padding: 16px;
      border-radius: 8px;
      margin-bottom: 24px;
    }

    .alert-warning {
      background: #fef3c7;
      color: #92400e;
      border: 1px solid #fbbf24;
    }

    .alert-error {
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #f87171;
    }

    .loading-state {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding: 40px;
      color: #6b7280;
    }

    .spinner {
      width: 20px;
      height: 20px;
      border: 2px solid #e5e7eb;
      border-top: 2px solid #3b82f6;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    @media (max-width: 640px) {
      .profile-grid {
        grid-template-columns: 1fr;
      }
      
      .profile-actions {
        flex-direction: column;
      }
      
      .btn {
        width: 100%;
      }
    }
  `]
})
export class ProfileComponent implements OnInit {
  profile: DetailedUserProfile | null = null;
  isAuthenticated = false;
  isLoading = false;
  
  constructor(
    private authService: AuthService,
    private router: Router,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    this.authService.getAuthStatus().subscribe(status => {
      this.isAuthenticated = status.authenticated;
      if (status.authenticated && status.user) {
        this.profile = {
          ...status.user,
          full_name: status.user.full_name || `${status.user.first_name || ''} ${status.user.middle_name || ''} ${status.user.last_name || ''}`.trim() || undefined
        };
        this.loadDetailedProfile();
      }
    });
  }

  private loadDetailedProfile(): void {
    if (!this.isAuthenticated) return;
    
    this.isLoading = true;
    
    // Get the session ID and make a request to get detailed profile
    const sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
      this.isLoading = false;
      return;
    }

    // Make request to ExternalApp API to get user details
    this.http.get<any>(`${environment.apiUrl}/auth/status?session_id=${sessionId}`, {
      headers: { 'X-Session-ID': sessionId }
    }).subscribe({
      next: (response) => {
        if (response.authenticated && response.user) {
          this.profile = {
            ...this.profile,
            ...response.user,
            full_name: response.user.full_name || `${response.user.first_name || ''} ${response.user.middle_name || ''} ${response.user.last_name || ''}`.trim() || undefined
          };
        }
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading detailed profile:', error);
        this.isLoading = false;
      }
    });
  }

  login(): void {
    const returnUrl = `${window.location.origin}/profile`;
    
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

  refreshProfile(): void {
    this.loadDetailedProfile();
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        localStorage.removeItem('session_id');
        this.isAuthenticated = false;
        this.profile = null;
        this.router.navigate(['/']);
      },
      error: (error) => {
        console.error('Error during logout:', error);
        // Clear local state anyway
        localStorage.removeItem('session_id');
        this.isAuthenticated = false;
        this.profile = null;
        this.router.navigate(['/']);
      }
    });
  }

  goHome(): void {
    this.router.navigate(['/']);
  }
}