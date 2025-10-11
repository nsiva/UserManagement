import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface User {
  id: string;
  email: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  full_name?: string;
  roles: string[];
  is_admin: boolean;
  authenticated_at?: string;
}

export interface AuthStatus {
  authenticated: boolean;
  user?: User;
  login_url?: string;
}

export interface LoginResponse {
  success: boolean;
  login_url: string;
  message: string;
  state?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;
  private authStatusSubject = new BehaviorSubject<AuthStatus>({ authenticated: false });
  public authStatus$ = this.authStatusSubject.asObservable();

  constructor(private http: HttpClient) {
    this.checkAuthStatus();
  }

  /**
   * Initiate login by getting redirect URL to User Management
   */
  initiateLogin(returnUrl?: string): Observable<LoginResponse> {
    const body = returnUrl ? { return_url: returnUrl } : {};
    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/login`, body);
  }

  /**
   * Check current authentication status
   */
  checkAuthStatus(): void {
    const sessionId = this.getSessionId();
    const url = sessionId 
      ? `${this.apiUrl}/auth/status?session_id=${sessionId}`
      : `${this.apiUrl}/auth/status`;
      
    this.http.get<AuthStatus>(url, {
      headers: this.getAuthHeaders()
    }).subscribe({
      next: (status) => {
        this.authStatusSubject.next(status);
      },
      error: (error) => {
        console.error('Error checking auth status:', error);
        this.authStatusSubject.next({ authenticated: false });
      }
    });
  }

  /**
   * Get current authentication status as observable
   */
  getAuthStatus(): Observable<AuthStatus> {
    return this.authStatus$;
  }

  /**
   * Get current user if authenticated
   */
  getCurrentUser(): User | null {
    const status = this.authStatusSubject.value;
    return status.authenticated ? status.user || null : null;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.authStatusSubject.value.authenticated;
  }

  /**
   * Logout user from both ExternalApp and User Management
   */
  logout(): Observable<any> {
    const sessionId = this.getSessionId();
    
    // Call ExternalApp logout first
    const externalAppLogout = this.http.post(`${this.apiUrl}/auth/logout`, {}, {
      headers: this.getAuthHeaders()
    });

    // Also call User Management logout API if we have a session
    if (sessionId) {
      const userManagementLogout = this.http.post('http://localhost:8001/auth/logout', {}, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
          'Content-Type': 'application/json'
        }
      });

      // Return combined observable - we don't care if User Management logout fails
      return externalAppLogout.pipe(
        tap(() => {
          // Try to logout from User Management but don't fail if it doesn't work
          userManagementLogout.subscribe({
            next: () => console.log('Successfully logged out from User Management'),
            error: (error) => console.warn('User Management logout failed (this is OK):', error)
          });
        })
      );
    }

    return externalAppLogout;
  }

  /**
   * Get session ID from localStorage
   */
  private getSessionId(): string | null {
    return localStorage.getItem('session_id');
  }

  /**
   * Get authorization headers (simplified for demo)
   */
  private getAuthHeaders(): { [key: string]: string } {
    const sessionId = this.getSessionId();
    return sessionId ? { 'X-Session-ID': sessionId } : {};
  }

  /**
   * Set session (called when returning from OAuth flow)
   */
  setSession(sessionId: string, user?: User): void {
    localStorage.setItem('session_id', sessionId);
    if (user) {
      this.authStatusSubject.next({
        authenticated: true,
        user: user
      });
    } else {
      // Re-check auth status to get user info
      this.checkAuthStatus();
    }
  }

  /**
   * Clear session
   */
  clearSession(): void {
    localStorage.removeItem('session_id');
    this.authStatusSubject.next({ authenticated: false });
  }

  /**
   * Handle return from OAuth authentication flow
   */
  handleOAuthReturn(queryParams: URLSearchParams): void {
    const sessionId = queryParams.get('session_id');
    const authSuccess = queryParams.get('auth_success');
    const error = queryParams.get('error');
    
    if (error) {
      console.error('OAuth error:', error);
      this.authStatusSubject.next({ 
        authenticated: false 
      });
      return;
    }
    
    if (sessionId && authSuccess === 'true') {
      console.log('OAuth authentication successful, session ID:', sessionId);
      this.setSession(sessionId);
    } else {
      console.warn('Invalid OAuth return parameters');
      this.authStatusSubject.next({ 
        authenticated: false 
      });
    }
  }

  /**
   * Handle return from User Management authentication (legacy)
   */
  handleAuthReturn(queryParams: any): void {
    // Legacy method for backward compatibility
    console.log('Legacy auth return detected');
    
    // Try to extract session info from query params
    if (queryParams.get) {
      // It's URLSearchParams
      this.handleOAuthReturn(queryParams);
    } else {
      // It's an object, convert to URLSearchParams
      const params = new URLSearchParams();
      Object.keys(queryParams).forEach(key => {
        if (queryParams[key]) {
          params.set(key, queryParams[key]);
        }
      });
      this.handleOAuthReturn(params);
    }
  }
}