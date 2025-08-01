import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';
import { environment } from '../../../environments/environment';
import { API_PATHS } from '../../api-paths';

@Component({
  selector: 'app-mfa',
  imports: [FormsModule, CommonModule],
  templateUrl: './mfa.html',
  styleUrls: ['./mfa.scss']
})
export class MfaComponent {
  mfaCode = '';
  emailId: string | null = null;
  message: string | null = null;
  isError = false;
  private apiUrl = environment.apiUrl;

  constructor(
    private route: ActivatedRoute,
    private http: HttpClient,
    private router: Router,
    private authService: AuthService
  ) {
    this.route.queryParams.subscribe(params => {
      this.emailId = params['emailId'] || null;
    });
  }

  onSubmitMfa(): void {
    this.message = null;
    this.isError = false;
    if (!this.mfaCode ) {
      this.message = 'Please enter the MFA code.';
      this.isError = true;
      return;
    }
    if (!this.emailId) {
      this.message = 'Email Id is required for MFA verification.';
      this.isError = true;
      return;
    }
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    const body = { email: this.emailId, mfa_code: this.mfaCode };
    const url = `${this.apiUrl}${API_PATHS.mfaVerify}`;
    this.http.post<any>(url, body, { headers })
      .subscribe(
        response => {
          this.message = 'MFA verification successful! You are now logged in.';
          this.isError = false;
          this.authService.setSession(response);
          this.router.navigate(['/profile']);
        },
        (error: HttpErrorResponse) => {
          this.isError = true;
          this.message = error.error?.detail || 'MFA verification failed. Please try again.';
        }
      );
  }
}