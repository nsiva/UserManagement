import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Generic GET method
   */
  get<T>(endpoint: string): Promise<T> {
    const headers = this.getHeaders();
    return this.http.get<T>(`${this.baseUrl}${endpoint}`, { headers }).toPromise() as Promise<T>;
  }

  /**
   * Generic POST method
   */
  post<T>(endpoint: string, data: any): Promise<T> {
    const headers = this.getHeaders();
    return this.http.post<T>(`${this.baseUrl}${endpoint}`, data, { headers }).toPromise() as Promise<T>;
  }

  /**
   * Generic PUT method
   */
  put<T>(endpoint: string, data: any): Promise<T> {
    const headers = this.getHeaders();
    return this.http.put<T>(`${this.baseUrl}${endpoint}`, data, { headers }).toPromise() as Promise<T>;
  }

  /**
   * Generic DELETE method
   */
  delete<T>(endpoint: string): Promise<T> {
    const headers = this.getHeaders();
    return this.http.delete<T>(`${this.baseUrl}${endpoint}`, { headers }).toPromise() as Promise<T>;
  }

  /**
   * Get authorization headers
   */
  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    let headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }

    return headers;
  }
}