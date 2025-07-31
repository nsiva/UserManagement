import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-mfa-setup-modal',
   imports: [FormsModule,CommonModule],
 
  templateUrl: './mfa-setup-modal.html',
  styleUrls: ['./mfa-setup-modal.scss']
})
export class MfaSetupModalComponent {
  @Input() qrCodeBase64: string | null = null;
  @Input() secret: string | null = null;
  @Input() provisioningUri: string | null = null;
  @Output() close = new EventEmitter<void>();

  constructor() { }

  onClose(): void {
    this.close.emit();
  }
}