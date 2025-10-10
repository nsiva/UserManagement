import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface User {
  id: string;
  email: string;
  roles: string[];
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
    this.http.get<AuthStatus>(`${this.apiUrl}/auth/status`, {
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
   * Logout user
   */
  logout(): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/logout`, {}, {
      headers: this.getAuthHeaders()
    });
  }

  /**
   * Get authorization headers (simplified for demo)
   */
  private getAuthHeaders(): { [key: string]: string } {
    const sessionId = localStorage.getItem('session_id');
    return sessionId ? { 'X-Session-ID': sessionId } : {};
  }

  /**
   * Set session (called when returning from User Management)
   */
  setSession(sessionId: string, user: User): void {
    localStorage.setItem('session_id', sessionId);
    this.authStatusSubject.next({
      authenticated: true,
      user: user
    });
  }

  /**
   * Clear session
   */
  clearSession(): void {
    localStorage.removeItem('session_id');
    this.authStatusSubject.next({ authenticated: false });
  }

  /**
   * Handle return from User Management authentication
   * In a real app, this would validate tokens/signatures
   */
  handleAuthReturn(queryParams: any): void {
    // In a real implementation, you would:
    // 1. Validate the return parameters
    // 2. Exchange for tokens if needed
    // 3. Set up the session
    
    // For this demo, we'll simulate success
    const mockUser: User = {
      id: 'user_123',
      email: 'user@example.com',
      roles: ['user'],
      authenticated_at: new Date().toISOString()
    };
    
    const sessionId = `session_${Date.now()}`;
    this.setSession(sessionId, mockUser);
    
    console.log('Authentication return handled successfully');
  }
}