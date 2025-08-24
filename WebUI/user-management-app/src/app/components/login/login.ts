import { Component } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { API_PATHS } from '../../api-paths';
import { AuthService } from '../../services/auth';

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

  constructor(private http: HttpClient, private router: Router, private authService: AuthService) { }

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

    this.authService.login(this.email, this.password).subscribe({
      next: (response: any) => {
        this.message = 'Login successful! Welcome.';
        this.isError = false;
        this.email = '';
        this.password = '';
        
        // Redirect based on user type
        if (this.authService.isAdmin()) {
          this.router.navigate(['/admin']);
        } else {
          this.router.navigate(['/profile']);
        }
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
    this.authService.verifyMfa(this.email, this.mfaCode).subscribe({
      next: (response: any) => {
        this.message = 'MFA verification successful! You are now logged in.';
        this.isError = false;
        this.showMfaPrompt = false;
        this.email = '';
        this.password = '';
        this.mfaCode = '';
        this.tempUserId = null;
        
        // Redirect based on user type
        if (this.authService.isAdmin()) {
          this.router.navigate(['/admin']);
        } else {
          this.router.navigate(['/profile']);
        }
      },
      error: (error: HttpErrorResponse) => {
        console.error('MFA verification error:', error);
        this.handleError(error);
      }
    });
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
