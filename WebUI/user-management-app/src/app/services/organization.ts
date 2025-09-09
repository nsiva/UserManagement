import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth';
import { environment } from '../../environments/environment';
import { API_PATHS } from '../api-paths';

// Organization interfaces matching the API models
export interface Organization {
  id: string;
  company_name: string;
  address_1?: string;
  address_2?: string;
  city_town?: string;
  state?: string;
  zip?: string;
  country?: string;
  email?: string;
  phone_number?: string;
  created_at: string;
  updated_at?: string;
}

export interface OrganizationCreate {
  company_name: string;
  address_1?: string;
  address_2?: string;
  city_town?: string;
  state?: string;
  zip?: string;
  country?: string;
  email?: string;
  phone_number?: string;
}

export interface OrganizationUpdate {
  company_name?: string;
  address_1?: string;
  address_2?: string;
  city_town?: string;
  state?: string;
  zip?: string;
  country?: string;
  email?: string;
  phone_number?: string;
}

@Injectable({
  providedIn: 'root'
})
export class OrganizationService {
  private apiUrl = environment.apiUrl; // Base API URL

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

  // --- Organization Management ---
  getOrganizations(): Observable<Organization[]> {
    return this.http.get<Organization[]>(`${this.apiUrl}${API_PATHS.organizations}`, { headers: this.getAuthHeaders() });
  }

  getOrganization(organizationId: string): Observable<Organization> {
    return this.http.get<Organization>(`${this.apiUrl}${API_PATHS.organizationById(organizationId)}`, { headers: this.getAuthHeaders() });
  }

  createOrganization(organizationData: OrganizationCreate): Observable<Organization> {
    return this.http.post<Organization>(`${this.apiUrl}${API_PATHS.organizations}`, organizationData, { headers: this.getAuthHeaders() });
  }

  updateOrganization(organizationId: string, organizationData: OrganizationUpdate): Observable<Organization> {
    return this.http.put<Organization>(`${this.apiUrl}${API_PATHS.organizationById(organizationId)}`, organizationData, { headers: this.getAuthHeaders() });
  }

  deleteOrganization(organizationId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}${API_PATHS.organizationById(organizationId)}`, { headers: this.getAuthHeaders() });
  }
}