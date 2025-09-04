import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PasswordRequirements } from '../../services/password-validation.service';

@Component({
  selector: 'app-password-requirements',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './password-requirements.component.html',
  styleUrl: './password-requirements.component.scss'
})
export class PasswordRequirementsComponent {
  @Input() passwordRequirements: PasswordRequirements = {
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecialChar: false
  };
}