import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth';
import { environment } from '../../environments/environment';
import { API_PATHS } from '../api-paths';

// Re-declare interfaces from models.py for Angular
export interface User {
  id: string;
  email: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  roles: string[];
  mfa_enabled: boolean;
  
  // Business Unit Information
  business_unit_id?: string;
  business_unit_name?: string;
  business_unit_code?: string;
  business_unit_location?: string;
  
  // Organization Information
  organization_id?: string;
  organization_name?: string;
  organization_city?: string;
  organization_country?: string;
  
  // Additional Information
  business_unit_manager_name?: string;
  parent_business_unit_name?: string;
}

export interface UserFunctionalRole {
  functional_role_id: string;
  functional_role_name: string;
  functional_role_label: string;
  functional_role_category: string;
  source: 'direct' | 'business_unit' | 'organization';
  source_name?: string;
  assigned_at: string;
}

export interface UserRolesResponse {
  user_id: string;
  email: string;
  organizational_roles: string[];
  functional_roles: UserFunctionalRole[];
  organization_name?: string;
  business_unit_name?: string;
}

export interface UserCreate {
  email: string;
  password?: string; // Made optional to support different password setup methods
  password_option?: string; // Options: "generate_now", "send_link"
  first_name?: string;
  last_name?: string;
  roles?: string[];
  business_unit_id?: string; // Optional for backward compatibility - will be required once UI is updated
}

export interface UserUpdate {
  email?: string;
  password?: string;
  send_password_reset?: boolean; // Send password reset email if true
  first_name?: string;
  last_name?: string;
  roles?: string[];
  business_unit_id?: string; // Optional for user updates
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
    console.log('UserService: getUser called for userId:', userId, '- using endpoint: /admin/users/' + userId);
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

  // --- MFA Removal (Admin triggered for a user) ---
  removeMfaForUser(email: string): Observable<{ message: string }> {
    // Note: This is an admin-triggered MFA removal. The backend endpoint is protected.
    return this.http.delete<{ message: string }>(
      environment.apiUrl + `/auth/mfa/remove?email=${email}`, { headers: this.getAuthHeaders() }
    );
  }

  // --- Self Profile Management ---
  getMyProfile(): Observable<User> {
    console.log('UserService: getMyProfile called - using endpoint: /profiles/me/full');
    return this.http.get<User>(environment.apiUrl + '/profiles/me/full', { headers: this.getAuthHeaders() });
  }

  updateMyProfile(profileData: { first_name?: string, last_name?: string }): Observable<User> {
    return this.http.put<User>(environment.apiUrl + '/profiles/me', profileData, { headers: this.getAuthHeaders() });
  }

  // --- Current User Roles ---
  getMyRoles(): Observable<UserRolesResponse> {
    console.log('UserService: getMyRoles called - using endpoint:', API_PATHS.userRoles);
    return this.http.get<UserRolesResponse>(environment.apiUrl + API_PATHS.userRoles, { headers: this.getAuthHeaders() });
  }
}