import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { environment } from '../../environments/environment';
import { API_PATHS } from '../api-paths';

interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  is_admin: boolean;
  roles: string[];
}

interface ForgotPasswordResponse {
  message: string;
}

interface VerifyResetTokenResponse {
  valid: boolean;
  email?: string;
}

interface SetNewPasswordResponse {
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;
  private tokenKey = 'access_token';
  private userRolesKey = 'user_roles';
  private userIdKey = 'user_id';
  private userEmailKey = 'user_email';

  private loggedIn = new BehaviorSubject<boolean>(this.hasToken());
  isLoggedIn$ = this.loggedIn.asObservable(); // Observable to track login status

  constructor(private http: HttpClient, private router: Router) { }

  private hasToken(): boolean {
    return !!localStorage.getItem(this.tokenKey);
  }

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}${API_PATHS.login}`, { email, password }).pipe(
      tap(response => {
        // Only set session if MFA is not required
        if (!(response as any).mfa_required && !(response as any).requires_mfa) {
          this.setSession(response);
        }
        // If MFA is required, we'll set session after MFA verification
      }),
      catchError(error => {
        // Handle specific MFA required error (e.g., status 402) in component
        throw error;
      })
    );
  }

  verifyMfa(email: string, mfaCode: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}${API_PATHS.mfaVerify}`, { email, mfa_code: mfaCode }).pipe(
      tap(response => {
        this.setSession(response);
      })
    );
  }

  setSession(authResult: LoginResponse): void {
    localStorage.setItem(this.tokenKey, authResult.access_token);
    localStorage.setItem(this.userRolesKey, JSON.stringify(authResult.roles));
    localStorage.setItem(this.userIdKey, authResult.user_id);
    localStorage.setItem(this.userEmailKey, authResult.email);
    this.loggedIn.next(true);
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userRolesKey);
    localStorage.removeItem(this.userIdKey);
    localStorage.removeItem(this.userEmailKey);
    this.loggedIn.next(false);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  getUserId(): string | null {
    return localStorage.getItem(this.userIdKey);
  }

  getUserEmail(): string | null {
    return localStorage.getItem(this.userEmailKey);
  }

  getUserRoles(): string[] {
    const roles = localStorage.getItem(this.userRolesKey);
    return roles ? JSON.parse(roles) : [];
  }

  isAdmin(): boolean {
    const roles = this.getUserRoles();
    return roles.includes('admin');
  }

  isLoggedIn(): boolean {
    return this.hasToken();
  }

  // Forgot Password Methods
  forgotPassword(email: string): Observable<ForgotPasswordResponse> {
    return this.http.post<ForgotPasswordResponse>(`${this.apiUrl}${API_PATHS.forgotPassword}`, { email });
  }

  verifyResetToken(token: string): Observable<VerifyResetTokenResponse> {
    return this.http.get<VerifyResetTokenResponse>(`${this.apiUrl}${API_PATHS.verifyResetToken}/${token}`);
  }

  setNewPassword(token: string, newPassword: string): Observable<SetNewPasswordResponse> {
    return this.http.post<SetNewPasswordResponse>(`${this.apiUrl}${API_PATHS.setNewPassword}`, {
      token,
      new_password: newPassword
    });
  }
}