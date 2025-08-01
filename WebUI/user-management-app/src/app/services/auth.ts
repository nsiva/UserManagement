import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { Router } from '@angular/router';

interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  is_admin: boolean;
  roles: string[];
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8001/auth'; // Your FastAPI auth endpoint
  private tokenKey = 'access_token';
  private userRolesKey = 'user_roles';
  private isAdminKey = 'is_admin';
  private userIdKey = 'user_id';
  private userEmailKey = 'user_email';

  private loggedIn = new BehaviorSubject<boolean>(this.hasToken());
  isLoggedIn$ = this.loggedIn.asObservable(); // Observable to track login status

  constructor(private http: HttpClient, private router: Router) { }

  private hasToken(): boolean {
    return !!localStorage.getItem(this.tokenKey);
  }

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/login`, { email, password }).pipe(
      tap(response => {
        // MFA required, don't store token yet
        // The backend will return 402 if MFA is needed.
        // We'll handle that in the component.
        this.setSession(response);
      }),
      catchError(error => {
        // Handle specific MFA required error (e.g., status 402) in component
        throw error;
      })
    );
  }

  verifyMfa(email: string, mfaCode: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/mfa/verify`, { email, mfa_code: mfaCode }).pipe(
      tap(response => {
        this.setSession(response);
      })
    );
  }

  setSession(authResult: LoginResponse): void {
    localStorage.setItem(this.tokenKey, authResult.access_token);
    localStorage.setItem(this.userRolesKey, JSON.stringify(authResult.roles));
    localStorage.setItem(this.isAdminKey, authResult.is_admin.toString());
    localStorage.setItem(this.userIdKey, authResult.user_id);
    localStorage.setItem(this.userEmailKey, authResult.email);
    this.loggedIn.next(true);
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userRolesKey);
    localStorage.removeItem(this.isAdminKey);
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
    return localStorage.getItem(this.isAdminKey) === 'true';
  }

  isLoggedIn(): boolean {
    return this.hasToken();
  }
}