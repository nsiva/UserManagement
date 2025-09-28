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
  // Note: Functional roles are now handled by the FunctionalRolesManagerComponent in the tabs
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

  // Functional roles are now handled by the EntityTabsComponent

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
    
    // Functional roles are handled separately by EntityTabsComponent
    return roles;
  }

  // Functional role selection is handled by EntityTabsComponent

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
      return;
    }

    // If categories aren't loaded yet, store the value for later
    if (!this.roleCategories) {
      this.pendingValue = roles;
      console.log('RoleSelector: Categories not loaded, storing pending value:', roles);
      return;
    }

    // Only handle administrative roles - functional roles are managed by EntityTabsComponent
    const adminRoles = this.roleCategories.administrative.roles.map(r => r.value);
    const foundAdminRole = roles.find(role => adminRoles.includes(role)) || '';

    console.log('RoleSelector: Admin role extraction:', { 
      inputRoles: roles,
      availableAdminRoles: adminRoles,
      foundAdminRole,
      disableAdministrativeRole: this.disableAdministrativeRole
    });

    this.selectedAdministrative = foundAdminRole;
    
    console.log('RoleSelector writeValue complete:', { 
      selectedAdministrative: this.selectedAdministrative,
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
    
    // Only check administrative roles (functional roles handled by EntityTabsComponent)
    const adminRole = this.roleCategories.administrative.roles.find(r => r.value === roleValue);
    if (adminRole) return adminRole.label;
    
    return roleValue;
  }

  getAdministrativeLabel(): string {
    return this.getRoleLabel(this.selectedAdministrative);
  }
}