import { Component, EventEmitter, Input, Output, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../../../services/auth';
import { environment } from '../../../../environments/environment';

type MfaMethod = 'totp' | 'email';
type SetupStep = 'method-selection' | 'totp-setup' | 'email-setup' | 'success';

interface TotpSetupResponse {
  qr_code_base64: string;
  secret: string;
  provisioning_uri: string;
}

interface EmailOtpResponse {
  message: string;
  expires_at: string;
}

interface EmailOtpVerifyResponse {
  message: string;
  mfa_enabled: boolean;
}

@Component({
  selector: 'app-enhanced-mfa-setup-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './enhanced-mfa-setup-modal.component.html',
  styleUrls: ['./enhanced-mfa-setup-modal.component.scss']
})
export class EnhancedMfaSetupModalComponent implements OnInit, OnDestroy {
  @Input() userEmail: string = '';
  @Input() show: boolean = false;
  @Output() closed = new EventEmitter<void>();
  @Output() setupComplete = new EventEmitter<{ method: MfaMethod; userEmail: string }>();

  // Component state
  currentStep: SetupStep = 'method-selection';
  selectedMethod: MfaMethod | null = null;
  isLoading = false;
  errorMessage: string | null = null;

  // TOTP-related properties
  totpQrCodeBase64: string | null = null;
  totpSecret: string | null = null;
  totpProvisioningUri: string | null = null;

  // Email OTP-related properties
  emailOtpSent = false;
  enteredOtp = '';
  otpError: string | null = null;
  resendCooldown = 0;
  private resendTimer: any = null;

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.resetComponent();
  }

  ngOnDestroy(): void {
    if (this.resendTimer) {
      clearInterval(this.resendTimer);
    }
  }

  private resetComponent(): void {
    this.currentStep = 'method-selection';
    this.selectedMethod = null;
    this.isLoading = false;
    this.errorMessage = null;
    this.totpQrCodeBase64 = null;
    this.totpSecret = null;
    this.totpProvisioningUri = null;
    this.emailOtpSent = false;
    this.enteredOtp = '';
    this.otpError = null;
    this.resendCooldown = 0;
    if (this.resendTimer) {
      clearInterval(this.resendTimer);
      this.resendTimer = null;
    }
  }

  private getAuthHeaders(): HttpHeaders {
    const token = this.authService.getToken();
    if (!token) {
      throw new Error('No authentication token found.');
    }
    
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json'
    });
  }

  selectMfaMethod(method: MfaMethod): void {
    this.selectedMethod = method;
    this.errorMessage = null;
  }

  async proceedWithMethod(): Promise<void> {
    if (!this.selectedMethod) return;

    this.isLoading = true;
    this.errorMessage = null;

    try {
      if (this.selectedMethod === 'totp') {
        await this.setupTotpMethod();
      } else if (this.selectedMethod === 'email') {
        this.currentStep = 'email-setup';
      }
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : 'An error occurred during setup';
    } finally {
      this.isLoading = false;
    }
  }

  private async setupTotpMethod(): Promise<void> {
    try {
      const response = await this.http.post<TotpSetupResponse>(
        `${environment.apiUrl}/auth/mfa/setup?email=${encodeURIComponent(this.userEmail)}`,
        {},
        { headers: this.getAuthHeaders() }
      ).toPromise();

      if (response) {
        this.totpQrCodeBase64 = response.qr_code_base64;
        this.totpSecret = response.secret;
        this.totpProvisioningUri = response.provisioning_uri;
        this.currentStep = 'totp-setup';
      }
    } catch (error: any) {
      throw new Error(error.error?.detail || 'Failed to setup TOTP authentication');
    }
  }

  async sendEmailOtp(): Promise<void> {
    this.isLoading = true;
    this.errorMessage = null;

    try {
      const response = await this.http.post<EmailOtpResponse>(
        `${environment.apiUrl}/auth/mfa/email/setup`,
        { email: this.userEmail },
        { headers: this.getAuthHeaders() }
      ).toPromise();

      if (response) {
        this.emailOtpSent = true;
        this.startResendCooldown();
      }
    } catch (error: any) {
      this.errorMessage = error.error?.detail || 'Failed to send verification email';
    } finally {
      this.isLoading = false;
    }
  }

  async resendEmailOtp(): Promise<void> {
    if (this.resendCooldown > 0) return;
    await this.sendEmailOtp();
  }

  private startResendCooldown(): void {
    this.resendCooldown = 60; // 60 seconds cooldown
    this.resendTimer = setInterval(() => {
      this.resendCooldown--;
      if (this.resendCooldown <= 0) {
        clearInterval(this.resendTimer);
        this.resendTimer = null;
      }
    }, 1000);
  }

  onOtpInput(event: any): void {
    const value = event.target.value.replace(/\D/g, ''); // Only allow digits
    this.enteredOtp = value;
    this.otpError = null;
  }

  isValidOtp(): boolean {
    return this.enteredOtp.length === 6 && /^\d{6}$/.test(this.enteredOtp);
  }

  async verifyEmailOtp(): Promise<void> {
    if (!this.isValidOtp()) {
      this.otpError = 'Please enter a valid 6-digit code';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.otpError = null;

    try {
      const response = await this.http.post<EmailOtpVerifyResponse>(
        `${environment.apiUrl}/auth/mfa/email/verify`,
        { 
          email: this.userEmail,
          otp: this.enteredOtp
        },
        { headers: this.getAuthHeaders() }
      ).toPromise();

      if (response?.mfa_enabled) {
        this.currentStep = 'success';
        this.setupComplete.emit({ method: 'email', userEmail: this.userEmail });
      }
    } catch (error: any) {
      this.otpError = error.error?.detail || 'Invalid verification code';
    } finally {
      this.isLoading = false;
    }
  }

  completeTotpSetup(): void {
    this.currentStep = 'success';
    this.setupComplete.emit({ method: 'totp', userEmail: this.userEmail });
  }

  goBackToMethodSelection(): void {
    this.currentStep = 'method-selection';
    this.selectedMethod = null;
    this.emailOtpSent = false;
    this.enteredOtp = '';
    this.otpError = null;
    this.errorMessage = null;
    if (this.resendTimer) {
      clearInterval(this.resendTimer);
      this.resendTimer = null;
    }
    this.resendCooldown = 0;
  }

  async copyToClipboard(text: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
  }

  onClose(): void {
    this.resetComponent();
    this.closed.emit();
  }
}