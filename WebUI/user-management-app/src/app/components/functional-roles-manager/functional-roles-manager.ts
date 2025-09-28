import { Component, Input, Output, EventEmitter, OnInit, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { 
  FunctionalRolesHierarchyService, 
  AvailableFunctionalRole,
  BulkOrganizationFunctionalRoleAssignment,
  BulkBusinessUnitFunctionalRoleAssignment,
  BulkUserFunctionalRoleAssignment,
  OrganizationFunctionalRole,
  BusinessUnitFunctionalRole 
} from '../../services/functional-roles-hierarchy';
import { FunctionalRolesService, FunctionalRole } from '../../services/functional-roles';
import { AlertComponent, AlertType } from '../../shared/components/alert/alert.component';

export type FunctionalRoleContext = 'organization' | 'business_unit' | 'user';

@Component({
  selector: 'app-functional-roles-manager',
  standalone: true,
  imports: [CommonModule, FormsModule, AlertComponent],
  templateUrl: './functional-roles-manager.html',
  styleUrl: './functional-roles-manager.scss'
})
export class FunctionalRolesManagerComponent implements OnInit, OnChanges {
  @Input() context: FunctionalRoleContext = 'organization';
  @Input() organizationId: string | null = null;
  @Input() businessUnitId: string | null = null;
  @Input() userId: string | null = null;
  @Input() readonly: boolean = false;
  @Output() rolesChanged = new EventEmitter<any>();

  availableRoles: AvailableFunctionalRole[] = [];
  currentRoles: (OrganizationFunctionalRole | BusinessUnitFunctionalRole)[] = [];
  isLoading = false;
  isSubmitting = false;

  // Alert properties
  alertMessage: string | null = null;
  alertType: AlertType = 'info';

  // Form state
  selectedRoleIds: string[] = [];

  constructor(
    private functionalRolesService: FunctionalRolesHierarchyService,
    private basicFunctionalRolesService: FunctionalRolesService
  ) {}

  ngOnInit() {
    this.loadData();
  }

  ngOnChanges() {
    this.loadData();
  }

  loadData() {
    if (this.context === 'organization') {
      if (this.organizationId) {
        this.loadOrganizationRoles();
      } else {
        // In create mode for organization, show all available functional roles
        this.loadAllFunctionalRoles();
      }
    } else if (this.context === 'business_unit') {
      if (this.businessUnitId) {
        this.loadBusinessUnitRoles();
      } else {
        // In create mode for business unit, show placeholder or limited roles
        this.loadCreateModeBusinessUnitRoles();
      }
    } else if (this.context === 'user' && this.userId) {
      this.loadUserAvailableRoles();
    }
  }

  private loadOrganizationRoles() {
    if (!this.organizationId) return;

    this.isLoading = true;
    
    // Load both current organization roles and all available functional roles
    forkJoin({
      currentRoles: this.functionalRolesService.getOrganizationFunctionalRoles(this.organizationId),
      allRoles: this.basicFunctionalRolesService.getFunctionalRoles()
    }).subscribe({
      next: (results) => {
        this.currentRoles = results.currentRoles;
        
        // Convert FunctionalRole to AvailableFunctionalRole format for all roles
        this.availableRoles = results.allRoles.map(role => ({
          functional_role_id: role.id,
          name: role.name,
          label: role.label,
          description: role.description,
          category: role.category,
          permissions: role.permissions,
          is_currently_assigned: false, // Will be updated based on currentRoles
          is_currently_enabled: false, // Will be updated based on currentRoles
          assigned_at: null,
          expires_at: null
        }));
        
        // Update the enabled status based on currentRoles
        const enabledRoleIds = new Set(this.currentRoles.map(role => role.functional_role_id));
        this.availableRoles.forEach(role => {
          if (enabledRoleIds.has(role.functional_role_id)) {
            role.is_currently_enabled = true;
            role.is_currently_assigned = true;
          }
        });
        
        this.updateSelectedRoles();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading organization roles:', error);
        this.showError('Failed to load organization roles');
        this.isLoading = false;
      }
    });
  }

  private loadBusinessUnitRoles() {
    if (!this.businessUnitId) return;

    this.isLoading = true;

    // Load available roles for this business unit (includes org-enabled roles with BU-specific overrides)
    this.functionalRolesService.getAvailableFunctionalRolesForBusinessUnit(this.businessUnitId).subscribe({
      next: (response) => {
        // For business units, availableRoles contains all org-enabled roles
        // with the proper enabled/disabled state based on BU-specific settings
        this.availableRoles = response.roles;
        this.currentRoles = []; // Business units use availableRoles as the source of truth
        this.updateSelectedRoles();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading available roles:', error);
        this.showError('Failed to load available roles');
        this.isLoading = false;
      }
    });
  }

  private loadUserAvailableRoles() {
    if (!this.userId) return;

    this.isLoading = true;

    this.functionalRolesService.getAvailableFunctionalRolesForUser(this.userId).subscribe({
      next: (response) => {
        this.availableRoles = response.roles;
        this.updateSelectedRoles();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading user available roles:', error);
        this.showError('Failed to load available roles for user');
        this.isLoading = false;
      }
    });
  }

  private loadAllFunctionalRoles() {
    this.isLoading = true;
    this.basicFunctionalRolesService.getFunctionalRoles().subscribe({
      next: (functionalRoles) => {
        // Convert FunctionalRole to AvailableFunctionalRole format
        this.availableRoles = functionalRoles.map(role => ({
          functional_role_id: role.id,
          name: role.name,
          label: role.label,
          description: role.description,
          category: role.category,
          permissions: role.permissions,
          is_currently_assigned: false, // For organization level, we'll check this separately
          is_currently_enabled: false, // For organization level, we'll check this separately
          assigned_at: null,
          expires_at: null
        }));
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading functional roles:', error);
        this.showError('Failed to load functional roles');
        this.availableRoles = [];
        this.isLoading = false;
      }
    });
  }

  private loadCreateModeBusinessUnitRoles() {
    // In business unit create mode, we can't show specific roles until we know the organization
    // Show an informational message instead
    this.isLoading = false;
    this.availableRoles = [];
    this.showInfo('Select an organization first to see available functional roles for this business unit.');
  }

  private updateSelectedRoles() {
    this.selectedRoleIds = [];
    
    // Update selectedRoleIds based on current assignments
    if (this.context === 'organization') {
      // For organizations, check both currentRoles and availableRoles for enabled status
      const enabledFromCurrent = this.currentRoles
        .filter(role => (role as any).is_enabled || (role as any).is_currently_enabled)
        .map(role => role.functional_role_id);
      
      const enabledFromAvailable = this.availableRoles
        .filter(role => role.is_currently_enabled || role.is_currently_assigned)
        .map(role => role.functional_role_id);
      
      // Combine both sources and remove duplicates
      this.selectedRoleIds = [...new Set([...enabledFromCurrent, ...enabledFromAvailable])];
    } else if (this.context === 'business_unit') {
      // For business units, use availableRoles which contains the correct state
      this.selectedRoleIds = this.availableRoles
        .filter(role => role.is_currently_enabled || role.is_currently_assigned)
        .map(role => role.functional_role_id);
    } else if (this.context === 'user') {
      this.selectedRoleIds = this.availableRoles
        .filter(role => role.is_currently_assigned)
        .map(role => role.functional_role_id);
    }
  }

  onRoleToggle(roleId: string, checked: boolean) {
    if (this.readonly) return;

    if (checked) {
      if (!this.selectedRoleIds.includes(roleId)) {
        this.selectedRoleIds.push(roleId);
      }
    } else {
      this.selectedRoleIds = this.selectedRoleIds.filter(id => id !== roleId);
    }
  }

  saveChanges() {
    if (this.readonly || this.isSubmitting) return;

    this.isSubmitting = true;
    this.alertMessage = null;

    if (this.context === 'organization' && this.organizationId) {
      this.saveOrganizationRoles();
    } else if (this.context === 'business_unit' && this.businessUnitId) {
      this.saveBusinessUnitRoles();
    } else if (this.context === 'user' && this.userId) {
      this.saveUserRoles();
    }
  }

  private saveOrganizationRoles() {
    if (!this.organizationId) return;

    // Get role names from selected IDs
    const selectedRoleNames = this.availableRoles
      .filter(role => this.selectedRoleIds.includes(role.functional_role_id))
      .map(role => role.name);

    const assignment: BulkOrganizationFunctionalRoleAssignment = {
      organization_id: this.organizationId,
      functional_role_names: selectedRoleNames,
      is_enabled: true,
      notes: 'Updated via role manager'
    };

    this.functionalRolesService.bulkAssignFunctionalRolesToOrganization(
      this.organizationId, 
      assignment
    ).subscribe({
      next: (response) => {
        this.showSuccess('Organization functional roles updated successfully');
        this.rolesChanged.emit({ context: 'organization', roles: selectedRoleNames });
        this.loadOrganizationRoles(); // Refresh the data
        this.isSubmitting = false;
      },
      error: (error) => {
        console.error('Error saving organization roles:', error);
        this.showError('Failed to update organization roles');
        this.isSubmitting = false;
      }
    });
  }

  private saveBusinessUnitRoles() {
    if (!this.businessUnitId) return;

    // Get role names from selected IDs
    const selectedRoleNames = this.availableRoles
      .filter(role => this.selectedRoleIds.includes(role.functional_role_id))
      .map(role => role.name);

    const assignment: BulkBusinessUnitFunctionalRoleAssignment = {
      business_unit_id: this.businessUnitId,
      functional_role_names: selectedRoleNames,
      is_enabled: true,
      notes: 'Updated via role manager'
    };

    this.functionalRolesService.bulkAssignFunctionalRolesToBusinessUnit(
      this.businessUnitId,
      assignment
    ).subscribe({
      next: (response) => {
        this.showSuccess('Business unit functional roles updated successfully');
        this.rolesChanged.emit({ context: 'business_unit', roles: selectedRoleNames });
        this.loadBusinessUnitRoles(); // Refresh the data
        this.isSubmitting = false;
      },
      error: (error) => {
        console.error('Error saving business unit roles:', error);
        let errorMessage = 'Failed to update business unit roles';
        if (error.error?.detail?.includes('organization level')) {
          errorMessage = 'Some roles must be enabled at organization level first';
        }
        this.showError(errorMessage);
        this.isSubmitting = false;
      }
    });
  }

  private saveUserRoles() {
    if (!this.userId) return;

    // Get role names from selected IDs
    const selectedRoleNames = this.availableRoles
      .filter(role => this.selectedRoleIds.includes(role.functional_role_id))
      .map(role => role.name);

    const assignment: BulkUserFunctionalRoleAssignment = {
      user_id: this.userId,
      functional_role_names: selectedRoleNames,
      replace_existing: true,
      notes: 'Updated via role manager'
    };

    this.functionalRolesService.bulkAssignFunctionalRolesToUser(
      this.userId,
      assignment
    ).subscribe({
      next: (response) => {
        this.showSuccess('User functional roles updated successfully');
        this.rolesChanged.emit({ context: 'user', roles: selectedRoleNames });
        this.loadUserAvailableRoles(); // Refresh the data
        this.isSubmitting = false;
      },
      error: (error) => {
        console.error('Error saving user roles:', error);
        let errorMessage = 'Failed to update user roles';
        if (error.error?.detail?.includes('business unit')) {
          errorMessage = 'Some roles are not available for this user\'s business unit';
        }
        this.showError(errorMessage);
        this.isSubmitting = false;
      }
    });
  }

  getRolesByCategory(): { [category: string]: AvailableFunctionalRole[] } {
    const rolesByCategory: { [category: string]: AvailableFunctionalRole[] } = {};
    
    this.availableRoles.forEach(role => {
      if (!rolesByCategory[role.category]) {
        rolesByCategory[role.category] = [];
      }
      rolesByCategory[role.category].push(role);
    });

    return rolesByCategory;
  }

  getCategories(): string[] {
    const categories = new Set(this.availableRoles.map(role => role.category));
    return Array.from(categories).sort();
  }

  isRoleSelected(roleId: string): boolean {
    return this.selectedRoleIds.includes(roleId);
  }

  getContextTitle(): string {
    switch (this.context) {
      case 'organization':
        return 'Organization Functional Roles';
      case 'business_unit':
        return 'Business Unit Functional Roles';
      case 'user':
        return 'Available User Functional Roles';
      default:
        return 'Functional Roles';
    }
  }

  getContextDescription(): string {
    switch (this.context) {
      case 'organization':
        return 'Enable functional roles at the organization level. These roles can then be enabled for specific business units.';
      case 'business_unit':
        return 'Enable functional roles for this business unit. Only roles enabled at the organization level are available.';
      case 'user':
        return 'These functional roles are available for assignment to users based on their business unit assignments.';
      default:
        return '';
    }
  }

  showError(message: string): void {
    this.alertMessage = message;
    this.alertType = 'error';
  }

  showSuccess(message: string): void {
    this.alertMessage = message;
    this.alertType = 'success';
  }

  showInfo(message: string): void {
    this.alertMessage = message;
    this.alertType = 'info';
  }

  onAlertDismissed(): void {
    this.alertMessage = null;
  }
}