import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { AuthService } from './auth';
import { environment } from '../../environments/environment';
import { API_PATHS } from '../api-paths';

// Define the UserProfile interface according to your API response structure
export interface UserProfile {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class UserProfileService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient, private authService: AuthService) {}

  private getAuthHeaders(): HttpHeaders {
    const token = this.authService.getToken();
    if (!token) {
      throw new Error('No authentication token found.');
    }
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });
  }

  getCurrentUserProfile(): Observable<UserProfile> {
    const userId = this.authService.getUserId();
    if (!userId) {
      return throwError(() => new Error('No user ID found.'));
    }
    return this.http.get<any>(`${this.apiUrl}${API_PATHS.userProfile}`, { headers: this.getAuthHeaders() })
      .pipe(
        // Map the response to UserProfile
        // You can adjust the mapping if your API response structure is different
        // For example, if the API returns { id, name, email }
        // Otherwise, map fields accordingly
        // If you need to transform nested fields, do it here
        // Example below assumes direct mapping
        // If you use RxJS 7+, you can use map from 'rxjs/operators'
        // import { map } from 'rxjs/operators';
        // ...existing code...
        // Uncomment the next line if you want to use map:
        map((resp: any) => ({
          id: resp.id,
          email: resp.email,
          first_name: resp.first_name,
          last_name: resp.last_name
        } as UserProfile)),
        catchError(
            (error) => throwError(() => error))
      );
  }
}
