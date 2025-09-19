import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RoleSelectorComponent } from '../components/role-selector/role-selector.component';

@Component({
  selector: 'app-role-selector-example',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RoleSelectorComponent],
  template: `
    <div class="max-w-2xl mx-auto p-6">
      <h2 class="text-2xl font-bold mb-6">User Role Assignment</h2>
      
      <form [formGroup]="userForm" (ngSubmit)="onSubmit()">
        
        <!-- User Basic Info -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Email Address *
          </label>
          <input 
            type="email"
            formControlName="email"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="user@example.com">
          <div *ngIf="userForm.get('email')?.errors?.['required'] && userForm.get('email')?.touched" 
               class="mt-1 text-sm text-red-600">
            Email is required
          </div>
        </div>

        <!-- Role Selection Component -->
        <div class="mb-6">
          <app-role-selector
            formControlName="roles"
            [required]="true"
            (roleChange)="onRolesChange($event)">
          </app-role-selector>
          
          <!-- Form validation errors -->
          <div *ngIf="userForm.get('roles')?.errors?.['required'] && userForm.get('roles')?.touched" 
               class="mt-2 text-sm text-red-600">
            At least one role must be selected
          </div>
        </div>

        <!-- Submit Button -->
        <div class="flex justify-end space-x-3">
          <button 
            type="button"
            (click)="resetForm()"
            class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            Reset
          </button>
          
          <button 
            type="submit"
            [disabled]="userForm.invalid"
            class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed">
            Create User
          </button>
        </div>
      </form>

      <!-- Form Value Display (for debugging) -->
      <div class="mt-8 p-4 bg-gray-50 rounded-lg">
        <h3 class="text-lg font-medium mb-2">Form Value:</h3>
        <pre class="text-sm">{{ userForm.value | json }}</pre>
        
        <h3 class="text-lg font-medium mb-2 mt-4">Selected Roles:</h3>
        <div class="space-y-2">
          <div *ngFor="let role of selectedRoles" class="flex items-center space-x-2">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">{{ role }}</span>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .form-group {
      @apply mb-6;
    }
    
    label {
      @apply block text-sm font-medium text-gray-700 mb-2;
    }
    
    input {
      @apply mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm;
      @apply focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm;
    }
  `]
})
export class RoleSelectorExampleComponent {
  userForm: FormGroup;
  selectedRoles: string[] = [];

  constructor(private fb: FormBuilder) {
    this.userForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      roles: [[], Validators.required] // Array of role strings
    });
  }

  onRolesChange(roles: string[]): void {
    this.selectedRoles = roles;
    console.log('Roles changed:', roles);
  }

  onSubmit(): void {
    if (this.userForm.valid) {
      const formData = this.userForm.value;
      console.log('Form submitted:', formData);
      
      // Here you would call your API service
      // this.apiService.createUser(formData).subscribe(...);
      
      alert('User creation form submitted! Check console for details.');
    } else {
      console.log('Form is invalid');
      Object.keys(this.userForm.controls).forEach(key => {
        const control = this.userForm.get(key);
        if (control?.invalid) {
          control.markAsTouched();
        }
      });
    }
  }

  resetForm(): void {
    this.userForm.reset();
    this.selectedRoles = [];
  }

  // Example of setting predefined roles (useful for edit mode)
  loadExistingUser(): void {
    // Simulate loading a user with existing roles
    const existingUserRoles = ['firm_admin', 'fleet_manager', 'accountant'];
    
    this.userForm.patchValue({
      email: 'manager@example.com',
      roles: existingUserRoles
    });
    
    this.selectedRoles = existingUserRoles;
  }
}