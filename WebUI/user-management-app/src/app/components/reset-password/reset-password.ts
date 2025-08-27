import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../../services/auth';
import { environment } from '../../../environments/environment';
import { API_PATHS } from '../../api-paths';
import { catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.scss'
})
export class ResetPasswordComponent implements OnInit {
  currentPassword: string = '';
  newPassword: string = '';
  confirmPassword: string = '';
  isLoading: boolean = false;
  successMessage: string = '';
  errorMessage: string = '';

  constructor(
    private router: Router,
    private http: HttpClient,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Check if user is logged in
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/login']);
    }
  }

  navigateBack(): void {
    this.router.navigate(['/profile']);
  }

  resetPassword(): void {
    this.errorMessage = '';
    this.successMessage = '';

    // Basic validation
    if (!this.currentPassword || !this.newPassword || !this.confirmPassword) {
      this.errorMessage = 'All fields are required';
      return;
    }

    if (this.newPassword.length < 8) {
      this.errorMessage = 'New password must be at least 8 characters long';
      return;
    }

    if (this.newPassword !== this.confirmPassword) {
      this.errorMessage = 'New passwords do not match';
      return;
    }

    this.isLoading = true;

    const resetData = {
      current_password: this.currentPassword,
      new_password: this.newPassword
    };

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.post(`${environment.apiUrl}${API_PATHS.resetPassword}`, resetData, { headers })
      .pipe(
        catchError(error => {
          this.isLoading = false;
          
          if (error.status === 400) {
            this.errorMessage = 'Current password is incorrect';
          } else if (error.status === 401) {
            this.errorMessage = 'Session expired. Please log in again';
            setTimeout(() => {
              this.authService.logout();
            }, 2000);
          } else if (error.status === 404) {
            this.errorMessage = 'User not found';
          } else {
            this.errorMessage = 'An error occurred while resetting your password. Please try again.';
          }
          
          console.error('Password reset error:', error);
          return of(null);
        })
      )
      .subscribe(response => {
        this.isLoading = false;
        
        if (response) {
          this.successMessage = 'Password reset successfully! Redirecting to profile...';
          this.currentPassword = '';
          this.newPassword = '';
          this.confirmPassword = '';
          
          // Redirect to profile after 2 seconds
          setTimeout(() => {
            this.navigateBack();
          }, 2000);
        }
      });
  }
}
