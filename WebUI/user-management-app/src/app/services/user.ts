import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth';
import { environment } from '../../environments/environment';

// Re-declare interfaces from models.py for Angular
export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  roles: string[];
}

export interface UserCreate {
  email: string;
  password?: string; // Password is required for create, but optional for update
  first_name?: string;
  last_name?: string;
  roles?: string[];
}

export interface UserUpdate {
  email?: string;
  password?: string;
  first_name?: string;
  last_name?: string;
  roles?: string[];
}

export interface Role {
  id: string;
  name: string;
}

export interface RoleCreate {
  name: string;
}

export interface RoleUpdate {
  name: string;
}

export interface UserRoleAssignment {
  user_id: string;
  role_names: string[];
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private apiUrl = environment.apiUrl + '/admin'; // Your FastAPI admin endpoint

  constructor(private http: HttpClient, private authService: AuthService) { }

  private getAuthHeaders(): HttpHeaders {
    const token = this.authService.getToken();
    if (!token) {
      console.error('No authentication token found');
      throw new Error('No authentication token found.');
    }
    
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json'
    });
  }

  // --- User Management ---
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.apiUrl}/users`, { headers: this.getAuthHeaders() });
  }

  getUser(userId: string): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/users/${userId}`, { headers: this.getAuthHeaders() });
  }

  createUser(userData: UserCreate): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/users`, userData, { headers: this.getAuthHeaders() });
  }

  updateUser(userId: string, userData: UserUpdate): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/users/${userId}`, userData, { headers: this.getAuthHeaders() });
  }

  deleteUser(userId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/users/${userId}`, { headers: this.getAuthHeaders() });
  }

  // --- Role Management ---
  getRoles(): Observable<Role[]> {
    return this.http.get<Role[]>(`${this.apiUrl}/roles`, { headers: this.getAuthHeaders() });
  }

  createRole(roleData: RoleCreate): Observable<Role> {
    return this.http.post<Role>(`${this.apiUrl}/roles`, roleData, { headers: this.getAuthHeaders() });
  }

  updateRole(roleId: string, roleData: RoleUpdate): Observable<Role> {
    return this.http.put<Role>(`${this.apiUrl}/roles/${roleId}`, roleData, { headers: this.getAuthHeaders() });
  }

  deleteRole(roleId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/roles/${roleId}`, { headers: this.getAuthHeaders() });
  }

  // --- User Role Assignment ---
  assignUserRoles(userId: string, roleNames: string[]): Observable<any> {
    const assignmentData: UserRoleAssignment = { user_id: userId, role_names: roleNames };
    return this.http.post(`${this.apiUrl}/users/${userId}/roles`, assignmentData, { headers: this.getAuthHeaders() });
  }

  // --- MFA Setup (Admin triggered for a user) ---
  setupMfaForUser(email: string): Observable<{ qr_code_base64: string, secret: string, provisioning_uri: string }> {
    // Note: This is an admin-triggered MFA setup. The backend endpoint is protected.
    return this.http.post<{ qr_code_base64: string, secret: string, provisioning_uri: string }>(
      environment.apiUrl + `/auth/mfa/setup?email=${email}`, {}, { headers: this.getAuthHeaders() }
    );
  }
}