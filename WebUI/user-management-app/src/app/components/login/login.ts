import { Component } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { API_PATHS } from '../../api-paths';

@Component({
  selector: 'app-login',
  imports: [FormsModule, CommonModule],
  templateUrl: './login.html',
  styleUrls: ['./login.scss']
})
export class LoginComponent {
  email = '';
  password = '';
  mfaCode = '';
  showMfaPrompt = false;
  tempUserId: string | null = null;
  message: string | null = null;
  isError = false;
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient, private router: Router) { }

  onLogin(): void {
    this.message = null;
    this.isError = false;
    this.showMfaPrompt = false;
    this.mfaCode = '';
    this.tempUserId = null;

    if (!this.email || !this.password) {
      this.message = 'Please enter both email and password.';
      this.isError = true;
      return;
    }

    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    const body = { email: this.email, password: this.password };

    const url = `${this.apiUrl}${API_PATHS.login}`;
    this.http.post<any>(url, body, { headers, observe: 'response' as 'body' })
    .subscribe({
      next: (response: any) => {
        this.message = 'Login successful! Welcome.';
        this.isError = false;
        localStorage.setItem('access_token', response.access_token);
        this.email = '';
        this.password = '';
      },
      error: (error: HttpErrorResponse) => {
        if (error.status === 402 && error.error && error.error.detail === 'MFA required. Please provide MFA code.') {
          this.router.navigate(['/mfa'], { queryParams: { emailId: this.email } });
        } else {
          this.handleError(error);
        }
      }
    });
  }

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
    const url = `${this.apiUrl}${API_PATHS.mfaVerify}`;
    this.http.post<any>(url, body, { headers })
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
