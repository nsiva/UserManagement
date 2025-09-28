import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { API_PATHS } from '../api-paths';

export interface FunctionalRole {
  id: string;
  name: string;
  label: string;
  description: string;
  category: string;
  permissions: string[];
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface FunctionalRoleCategory {
  category: string;
  roles: FunctionalRole[];
}

export interface FunctionalRoleCategoriesResponse {
  categories: FunctionalRoleCategory[];
  total_categories: number;
  total_roles: number;
}

@Injectable({
  providedIn: 'root'
})
export class FunctionalRolesService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders().set('Authorization', `Bearer ${token}`);
  }

  getFunctionalRoles(category?: string): Observable<FunctionalRole[]> {
    const headers = this.getAuthHeaders();
    let url = `${this.baseUrl}${API_PATHS.functionalRoles}`;
    if (category) {
      url += `?category=${encodeURIComponent(category)}`;
    }
    return this.http.get<FunctionalRole[]>(url, { headers });
  }

  getFunctionalRoleById(id: string): Observable<FunctionalRole> {
    const headers = this.getAuthHeaders();
    const url = `${this.baseUrl}${API_PATHS.functionalRoleById(id)}`;
    return this.http.get<FunctionalRole>(url, { headers });
  }

  getFunctionalRolesByCategory(): Observable<FunctionalRoleCategoriesResponse> {
    const headers = this.getAuthHeaders();
    const url = `${this.baseUrl}${API_PATHS.functionalRolesByCategory}`;
    return this.http.get<FunctionalRoleCategoriesResponse>(url, { headers });
  }
}