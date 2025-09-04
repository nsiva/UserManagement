import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export type AlertType = 'error' | 'success' | 'warning' | 'info';

@Component({
  selector: 'app-alert',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './alert.component.html',
  styleUrls: ['./alert.component.scss']
})
export class AlertComponent {
  @Input() message: string | null = null;
  @Input() type: AlertType = 'info';
  @Input() dismissible: boolean = true;
  @Output() dismissed = new EventEmitter<void>();

  get alertClasses(): string {
    const baseClasses = 'px-4 py-3 rounded relative mb-4';
    switch (this.type) {
      case 'error':
        return `${baseClasses} bg-red-100 border border-red-400 text-red-700`;
      case 'success':
        return `${baseClasses} bg-green-100 border border-green-400 text-green-700`;
      case 'warning':
        return `${baseClasses} bg-yellow-100 border border-yellow-400 text-yellow-700`;
      case 'info':
        return `${baseClasses} bg-blue-100 border border-blue-400 text-blue-700`;
      default:
        return baseClasses;
    }
  }

  get strongText(): string {
    switch (this.type) {
      case 'error':
        return 'Error! ';
      case 'success':
        return 'Success!';
      case 'warning':
        return 'Warning! ';
      case 'info':
        return 'Info! ';
      default:
        return '';
    }
  }

  get iconColor(): string {
    switch (this.type) {
      case 'error':
        return 'text-red-500';
      case 'success':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'info':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  }

  onDismiss(): void {
    this.dismissed.emit();
  }
}