import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth';
import { environment } from '../../environments/environment';
import { API_PATHS } from '../api-paths';

// Interface definitions matching the backend models
export interface FunctionalRole {
  id: string;
  name: string;
  label: string;
  description?: string;
  category: string;
  permissions: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrganizationFunctionalRole {
  id: string;
  organization_id: string;
  functional_role_id: string;
  is_enabled: boolean;
  notes?: string;
  assigned_at: string;
  assigned_by?: string;
}

export interface BusinessUnitFunctionalRole {
  id: string;
  business_unit_id: string;
  functional_role_id: string;
  is_enabled: boolean;
  notes?: string;
  assigned_at: string;
  assigned_by?: string;
}

export interface AvailableFunctionalRole {
  functional_role_id: string;
  name: string;
  label: string;
  description?: string;
  category: string;
  is_currently_enabled?: boolean;
  is_currently_assigned?: boolean;
  business_unit_name?: string;
}

export interface AvailableFunctionalRolesResponse {
  roles: AvailableFunctionalRole[];
  total_count: number;
  context: 'business_unit' | 'user';
}

export interface OrganizationFunctionalRoleCreate {
  organization_id: string;
  functional_role_id: string;
  is_enabled: boolean;
  notes?: string;
}

export interface BusinessUnitFunctionalRoleCreate {
  business_unit_id: string;
  functional_role_id: string;
  is_enabled: boolean;
  notes?: string;
}

export interface BulkOrganizationFunctionalRoleAssignment {
  organization_id: string;
  functional_role_names: string[];
  is_enabled: boolean;
  notes?: string;
}

export interface BulkBusinessUnitFunctionalRoleAssignment {
  business_unit_id: string;
  functional_role_names: string[];
  is_enabled: boolean;
  notes?: string;
}

export interface BulkUserFunctionalRoleAssignment {
  user_id: string;
  functional_role_names: string[];
  replace_existing?: boolean;
  notes?: string;
}

export interface FunctionalRoleHierarchyItem {
  organization_id: string;
  organization_name: string;
  business_unit_id?: string;
  business_unit_name?: string;
  functional_role_id: string;
  functional_role_name: string;
  functional_role_label: string;
  functional_role_category: string;
  enabled_at_org?: boolean;
  enabled_at_bu?: boolean;
  users_with_role: number;
}

export interface FunctionalRoleHierarchyResponse {
  hierarchy: FunctionalRoleHierarchyItem[];
  total_organizations: number;
  total_business_units: number;
  total_roles: number;
}

@Injectable({
  providedIn: 'root'
})
export class FunctionalRolesHierarchyService {
  private apiUrl = environment.apiUrl;

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

  // --- Organization Level Methods ---

  getOrganizationFunctionalRoles(organizationId: string): Observable<OrganizationFunctionalRole[]> {
    return this.http.get<OrganizationFunctionalRole[]>(
      `${this.apiUrl}${API_PATHS.orgFunctionalRoles(organizationId)}`,
      { headers: this.getAuthHeaders() }
    );
  }

  assignFunctionalRoleToOrganization(
    organizationId: string, 
    assignment: OrganizationFunctionalRoleCreate
  ): Observable<OrganizationFunctionalRole> {
    return this.http.post<OrganizationFunctionalRole>(
      `${this.apiUrl}${API_PATHS.orgFunctionalRoles(organizationId)}`,
      assignment,
      { headers: this.getAuthHeaders() }
    );
  }

  bulkAssignFunctionalRolesToOrganization(
    organizationId: string,
    assignment: BulkOrganizationFunctionalRoleAssignment
  ): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}${API_PATHS.orgFunctionalRolesBulk(organizationId)}`,
      assignment,
      { headers: this.getAuthHeaders() }
    );
  }

  // --- Business Unit Level Methods ---

  getBusinessUnitFunctionalRoles(businessUnitId: string): Observable<BusinessUnitFunctionalRole[]> {
    return this.http.get<BusinessUnitFunctionalRole[]>(
      `${this.apiUrl}${API_PATHS.buFunctionalRoles(businessUnitId)}`,
      { headers: this.getAuthHeaders() }
    );
  }

  getAvailableFunctionalRolesForBusinessUnit(businessUnitId: string): Observable<AvailableFunctionalRolesResponse> {
    return this.http.get<AvailableFunctionalRolesResponse>(
      `${this.apiUrl}${API_PATHS.buAvailableRoles(businessUnitId)}`,
      { headers: this.getAuthHeaders() }
    );
  }

  assignFunctionalRoleToBusinessUnit(
    businessUnitId: string,
    assignment: BusinessUnitFunctionalRoleCreate
  ): Observable<BusinessUnitFunctionalRole> {
    return this.http.post<BusinessUnitFunctionalRole>(
      `${this.apiUrl}${API_PATHS.buFunctionalRoles(businessUnitId)}`,
      assignment,
      { headers: this.getAuthHeaders() }
    );
  }

  bulkAssignFunctionalRolesToBusinessUnit(
    businessUnitId: string,
    assignment: BulkBusinessUnitFunctionalRoleAssignment
  ): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}${API_PATHS.buFunctionalRolesBulk(businessUnitId)}`,
      assignment,
      { headers: this.getAuthHeaders() }
    );
  }

  // --- User Level Methods ---

  getAvailableFunctionalRolesForUser(userId: string): Observable<AvailableFunctionalRolesResponse> {
    return this.http.get<AvailableFunctionalRolesResponse>(
      `${this.apiUrl}${API_PATHS.userAvailableRoles(userId)}`,
      { headers: this.getAuthHeaders() }
    );
  }

  bulkAssignFunctionalRolesToUser(
    userId: string,
    assignment: BulkUserFunctionalRoleAssignment
  ): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}${API_PATHS.userFunctionalRolesAssign(userId)}`,
      assignment,
      { headers: this.getAuthHeaders() }
    );
  }

  // --- Hierarchy Overview Methods ---

  getFunctionalRoleHierarchy(organizationId?: string): Observable<FunctionalRoleHierarchyResponse> {
    let url = `${this.apiUrl}${API_PATHS.functionalRoleHierarchyView}`;
    if (organizationId) {
      url += `?organization_id=${organizationId}`;
    }
    
    return this.http.get<FunctionalRoleHierarchyResponse>(
      url,
      { headers: this.getAuthHeaders() }
    );
  }
}