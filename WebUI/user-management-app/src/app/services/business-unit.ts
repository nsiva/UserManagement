import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

export interface BusinessUnit {
  id: string;
  name: string;
  description?: string;
  code?: string;
  organization_id: string;
  parent_unit_id?: string;
  manager_id?: string;
  location?: string;
  country?: string;
  region?: string;
  email?: string;
  phone_number?: string;
  is_active: boolean;
  created_at: string;
  created_by?: string;
  updated_at?: string;
  updated_by?: string;
  
  // Extended fields from joins
  organization_name?: string;
  parent_name?: string;
  manager_name?: string;
}

export interface BusinessUnitCreate {
  name: string;
  description?: string;
  code?: string;
  organization_id: string;
  parent_unit_id?: string;
  manager_id?: string;
  location?: string;
  country?: string;
  region?: string;
  email?: string;
  phone_number?: string;
  is_active?: boolean;
}

export interface BusinessUnitUpdate {
  name?: string;
  description?: string;
  code?: string;
  parent_unit_id?: string;
  manager_id?: string;
  location?: string;
  country?: string;
  region?: string;
  email?: string;
  phone_number?: string;
  is_active?: boolean;
}

export interface BusinessUnitListResponse {
  business_units: BusinessUnit[];
  total_count: number;
  organization_id?: string;
  organization_name?: string;
}

export interface BusinessUnitHierarchy extends BusinessUnit {
  children?: BusinessUnitHierarchy[];
}

@Injectable({
  providedIn: 'root'
})
export class BusinessUnitService {
  private baseUrl = `${environment.apiUrl}/business-units`;

  constructor(private http: HttpClient, private authService: AuthService) {}

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

  /**
   * Get all business units, optionally filtered by organization
   */
  getBusinessUnits(organizationId?: string): Observable<BusinessUnitListResponse> {
    let params = new HttpParams();
    if (organizationId) {
      params = params.set('organization_id', organizationId);
    }
    return this.http.get<BusinessUnitListResponse>(this.baseUrl, { 
      headers: this.getAuthHeaders(),
      params 
    });
  }

  /**
   * Get business unit by ID
   */
  getBusinessUnitById(id: string): Observable<BusinessUnit> {
    return this.http.get<BusinessUnit>(`${this.baseUrl}/${id}`, { 
      headers: this.getAuthHeaders() 
    });
  }

  /**
   * Get business unit hierarchy for an organization
   */
  getBusinessUnitHierarchy(organizationId: string, parentId?: string): Observable<BusinessUnitHierarchy[]> {
    let params = new HttpParams();
    if (parentId) {
      params = params.set('parent_id', parentId);
    }
    return this.http.get<BusinessUnitHierarchy[]>(`${this.baseUrl}/hierarchy/${organizationId}`, { 
      headers: this.getAuthHeaders(),
      params 
    });
  }

  /**
   * Create a new business unit
   */
  createBusinessUnit(businessUnit: BusinessUnitCreate): Observable<BusinessUnit> {
    return this.http.post<BusinessUnit>(this.baseUrl, businessUnit, { 
      headers: this.getAuthHeaders() 
    });
  }

  /**
   * Update an existing business unit
   */
  updateBusinessUnit(id: string, businessUnit: BusinessUnitUpdate): Observable<BusinessUnit> {
    return this.http.put<BusinessUnit>(`${this.baseUrl}/${id}`, businessUnit, { 
      headers: this.getAuthHeaders() 
    });
  }

  /**
   * Delete a business unit
   */
  deleteBusinessUnit(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`, { 
      headers: this.getAuthHeaders() 
    });
  }
}