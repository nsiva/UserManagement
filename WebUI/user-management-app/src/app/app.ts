import { Component } from '@angular/core';
import { environment } from '../environments/environment';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-root', // The HTML tag to use this component
  imports: [
    FormsModule,
    CommonModule,
    RouterModule
  ],
  templateUrl: './app.html', // Link to the component's HTML template
  styleUrls: ['./app.scss'] // Link to the component's CSS (though Tailwind is used globally)
})
export class App {
  title = 'User Management'; // Title for the application

  // Login form data
  email = '';
  password = '';

  // API response messages
  message: string | null = null;
  isError = false;

  // MFA fields
  showMfaPrompt = false;
  mfaCode = '';
  tempUserId: string | null = null;

  // Base URL for your FastAPI backend
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { } // Inject HttpClient for making API calls

  /**
   * Handles the login form submission.
   * Sends user credentials to the FastAPI backend.
   */
  onLogin(): void {
    this.message = null; // Clear previous messages
    this.isError = false;
    this.showMfaPrompt = false;
    this.mfaCode = '';
    this.tempUserId = null;

    // Basic validation
    if (!this.email || !this.password) {
      this.message = 'Please enter both email and password.';
      this.isError = true;
      return;
    }

    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    const body = { email: this.email, password: this.password };

    this.http.post<any>(`${this.apiUrl}/auth/login`, body, { headers, observe: 'response' as 'body' })
      .pipe(
        catchError((error: HttpErrorResponse) => {
          // Handle 402 for MFA required
          if (error.status === 402 && error.error && error.error.detail === 'MFA required. Please provide MFA code.') {
            this.showMfaPrompt = true;
            this.tempUserId = error.error.user_id || null;
            this.message = 'MFA required. Please enter your MFA code.';
            return [];
          }
          return this.handleError(error);
        })
      )
      .subscribe((response: any) => {
        if (!response) return;
        // Successful login
        console.log('Login successful:', response);
        this.message = 'Login successful! Welcome.';
        this.isError = false;
        localStorage.setItem('access_token', response.access_token);
        this.email = '';
        this.password = '';
      });
  }

  /**
   * Handles MFA code submission after 402 response.
   */
  onSubmitMfa(): void {
    this.message = null;
    this.isError = false;
    if (!this.mfaCode || !this.tempUserId) {
      this.message = 'Please enter the MFA code.';
      this.isError = true;
      return;
    }
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    const body = { user_id: this.tempUserId, mfa_code: this.mfaCode };
    this.http.post<any>(`${this.apiUrl}/auth/mfa/verify`, body, { headers })
      .pipe(
        catchError(this.handleError)
      )
      .subscribe(
        response => {
          this.message = 'MFA verification successful! You are now logged in.';
          this.isError = false;
          localStorage.setItem('access_token', response.access_token);
          this.showMfaPrompt = false;
          this.email = '';
          this.password = '';
          this.mfaCode = '';
          this.tempUserId = null;
        },
        error => {
          console.error('MFA verification error:', error);
        }
      );
  }

  /**
   * Centralized error handling for HTTP requests.
   * @param error The HttpErrorResponse object.
   * @returns An observable that re-throws the error.
   */
  private handleError = (error: HttpErrorResponse) => {
    this.isError = true;
    if (error.error instanceof ErrorEvent) {
      this.message = `An error occurred: ${error.error.message}`;
    } else {
      console.error(
        `Backend returned code ${error.status}, ` +
        `body was: ${JSON.stringify(error.error)}`);
      if (error.error && error.error.detail) {
        this.message = `Error: ${error.error.detail}`;
      } else {
        this.message = `An unknown error occurred. Status: ${error.status}`;
      }
    }
    return throwError(() => new Error(this.message || 'Something bad happened; please try again later.'));
  };
}
