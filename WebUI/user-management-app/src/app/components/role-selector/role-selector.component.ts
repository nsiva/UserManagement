import { Component, OnInit, Input, Output, EventEmitter, forwardRef } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

interface RoleOption {
  value: string;
  label: string;
  description: string;
}

interface RoleCategory {
  name: string;
  description: string;
  required: boolean;
  multiple_selection: boolean;
  roles: RoleOption[];
}

interface RoleCategories {
  administrative: RoleCategory;
  functional: RoleCategory;
}

interface RoleSelection {
  administrative: string;
  functional: string[];
}

@Component({
  selector: 'app-role-selector',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './role-selector.component.html',
  styleUrls: ['./role-selector.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => RoleSelectorComponent),
      multi: true
    }
  ]
})
export class RoleSelectorComponent implements OnInit, ControlValueAccessor {
  @Input() disabled: boolean = false;
  @Input() required: boolean = true;
  @Input() disableAdministrativeRole: boolean = false; // New input to disable admin role editing
  @Output() roleChange = new EventEmitter<string[]>();

  roleCategories: RoleCategories | null = null;
  selectedAdministrative: string = '';
  selectedFunctional: string[] = [];
  loading: boolean = false;
  error: string = '';

  // ControlValueAccessor implementation
  private onChange = (value: string[]) => {};
  private onTouched = () => {};
  private pendingValue: string[] | null = null; // Store pending value until categories load

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadRoleCategories();
  }

  async loadRoleCategories(): Promise<void> {
    this.loading = true;
    this.error = '';
    
    try {
      const selfEditParam = this.disableAdministrativeRole ? '?self_edit=true' : '';
      this.roleCategories = await this.apiService.get<RoleCategories>(`/admin/role-categories${selfEditParam}`);
      console.log('RoleSelector: Categories loaded:', this.roleCategories);
      console.log('RoleSelector: disableAdministrativeRole:', this.disableAdministrativeRole);
      
      // If there's a pending value, apply it now that categories are loaded
      if (this.pendingValue) {
        console.log('RoleSelector: Applying pending value:', this.pendingValue);
        this.writeValue(this.pendingValue);
        this.pendingValue = null;
      }
    } catch (error) {
      console.error('Error loading role categories:', error);
      this.error = 'Failed to load role categories';
    } finally {
      this.loading = false;
    }
  }

  onAdministrativeChange(role: string): void {
    this.selectedAdministrative = role;
    this.emitChange();
    this.onTouched();
  }

  onFunctionalChange(role: string, checked: boolean): void {
    if (checked) {
      if (!this.selectedFunctional.includes(role)) {
        this.selectedFunctional.push(role);
      }
    } else {
      this.selectedFunctional = this.selectedFunctional.filter(r => r !== role);
    }
    this.emitChange();
    this.onTouched();
  }

  private emitChange(): void {
    const allRoles = this.getCombinedRoles();
    this.onChange(allRoles);
    this.roleChange.emit(allRoles);
  }

  private getCombinedRoles(): string[] {
    const roles: string[] = [];
    
    if (this.selectedAdministrative) {
      roles.push(this.selectedAdministrative);
    }
    
    roles.push(...this.selectedFunctional);
    
    return roles;
  }

  isFunctionalRoleSelected(role: string): boolean {
    return this.selectedFunctional.includes(role);
  }

  // ControlValueAccessor implementation
  writeValue(roles: string[]): void {
    console.log('RoleSelector writeValue called:', { 
      roles, 
      hasCategories: !!this.roleCategories,
      disableAdministrativeRole: this.disableAdministrativeRole,
      timestamp: new Date().toISOString()
    });
    
    if (!roles || roles.length === 0) {
      console.log('RoleSelector: Empty or null roles, clearing selections');
      this.selectedAdministrative = '';
      this.selectedFunctional = [];
      return;
    }

    // If categories aren't loaded yet, store the value for later
    if (!this.roleCategories) {
      this.pendingValue = roles;
      console.log('RoleSelector: Categories not loaded, storing pending value:', roles);
      return;
    }

    // Separate administrative and functional roles
    const adminRoles = this.roleCategories.administrative.roles.map(r => r.value);
    const functionalRoles = this.roleCategories.functional.roles.map(r => r.value);

    const foundAdminRole = roles.find(role => adminRoles.includes(role)) || '';
    const foundFunctionalRoles = roles.filter(role => functionalRoles.includes(role));

    console.log('RoleSelector: Role separation:', { 
      inputRoles: roles,
      availableAdminRoles: adminRoles,
      availableFunctionalRoles: functionalRoles,
      foundAdminRole,
      foundFunctionalRoles,
      disableAdministrativeRole: this.disableAdministrativeRole
    });

    this.selectedAdministrative = foundAdminRole;
    this.selectedFunctional = foundFunctionalRoles;
    
    console.log('RoleSelector writeValue complete:', { 
      selectedAdministrative: this.selectedAdministrative, 
      selectedFunctional: this.selectedFunctional,
      disableAdministrativeRole: this.disableAdministrativeRole,
      timestamp: new Date().toISOString()
    });
  }

  registerOnChange(fn: (value: string[]) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  // Validation methods
  isValid(): boolean {
    return !!this.selectedAdministrative; // Administrative role is required
  }

  getValidationError(): string {
    if (!this.selectedAdministrative) {
      return 'Administrative level is required';
    }
    return '';
  }

  // Helper methods for template
  getRoleLabel(roleValue: string): string {
    if (!this.roleCategories) return roleValue;
    
    // Check administrative roles
    const adminRole = this.roleCategories.administrative.roles.find(r => r.value === roleValue);
    if (adminRole) return adminRole.label;
    
    // Check functional roles
    const functionalRole = this.roleCategories.functional.roles.find(r => r.value === roleValue);
    if (functionalRole) return functionalRole.label;
    
    return roleValue;
  }

  getAdministrativeLabel(): string {
    return this.getRoleLabel(this.selectedAdministrative);
  }
}