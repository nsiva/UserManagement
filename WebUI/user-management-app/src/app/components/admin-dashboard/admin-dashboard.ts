import { Component, OnInit, HostListener } from '@angular/core';
import { AuthService } from '../../services/auth';
import { RoleService } from '../../services/role.service';
import { UserService, User, UserCreate, UserUpdate, Role, RoleCreate, RoleUpdate } from '../../services/user';
import { UserProfileService } from '../../services/user-profile.service';
import { OrganizationService, Organization, OrganizationCreate, OrganizationUpdate } from '../../services/organization';
import { BusinessUnitService, BusinessUnit, BusinessUnitCreate, BusinessUnitUpdate } from '../../services/business-unit';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { AlertComponent, AlertType } from '../../shared/components/alert/alert.component';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';
import { 
  ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN,
  hasAdminAccess, hasOrganizationAdminAccess, hasBusinessUnitAdminAccess 
} from '../../constants/roles';

@Component({
  selector: 'app-admin-dashboard',
  imports: [FormsModule, CommonModule, ReactiveFormsModule, HeaderComponent, AlertComponent],
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.scss']

})
export class AdminDashboardComponent implements OnInit {
  // Role constants for template access
  readonly ADMIN_ROLE = ADMIN;
  
  // Header configuration
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.ADMIN_DASHBOARD,
    showUserMenu: true
  };

  activeTab: 'users' | 'organizations' | 'business-units' = 'users';

  // User Management
  users: User[] = [];
  userForm: FormGroup;
  isEditModeUser = false;
  selectedUserId: string | null = null;
  userRolesOptions: Role[] = []; // All available roles for assignment
  selectedUserRole: string = 'user'; // Single role for the currently selected user, default to 'user'

  // Role Management
  roles: Role[] = [];
  roleForm: FormGroup;
  isEditModeRole = false;
  selectedRoleId: string | null = null;

  // Organizations Management
  organizations: Organization[] = [];

  // Business Units Management
  businessUnits: BusinessUnit[] = [];

  // MFA Setup
  showMfaSetupModal = false;
  mfaQrCodeBase64: string | null = null;
  mfaSecret: string | null = null;
  mfaProvisioningUri: string | null = null;
  selectedUserForMfa: User | null = null;

  // Confirmation Modal
  showConfirmModal = false;
  confirmTitle = '';
  confirmMessage = '';
  confirmButtonText = '';
  confirmCallback: (() => void) | null = null;


  // Alert properties
  alertMessage: string | null = null;
  alertType: AlertType = 'info';

  constructor(
    private authService: AuthService,
    private roleService: RoleService,
    private userService: UserService,
    private userProfileService: UserProfileService,
    private organizationService: OrganizationService,
    private businessUnitService: BusinessUnitService,
    private fb: FormBuilder,
    private router: Router
  ) {
    this.userForm = this.fb.group({
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.minLength(6)]] // Password optional for update
    });

    this.roleForm = this.fb.group({
      name: ['', Validators.required]
    });

  }

  ngOnInit(): void {
    // Load users and roles for all admin privileged users
    if (this.roleService.hasAdminPrivileges()) {
      this.loadUsers();
      this.loadRoles();
    }

    // Set default tab based on access levels
    if (this.roleService.hasBusinessUnitAccess()) {
      // Users with business unit access (admin, super_user, firm_admin) default to business-units
      this.activeTab = 'business-units';
      this.loadBusinessUnits();
    } else {
      // Users without business unit access (group_admin) default to users tab
      this.activeTab = 'users';
    }
  }

  // --- General UI ---
  selectTab(tab: 'users' | 'organizations' | 'business-units'): void {
    this.activeTab = tab;
    this.alertMessage = null;
    this.resetForms();
    if (tab === 'organizations') {
      this.loadOrganizations();
    } else if (tab === 'business-units') {
      this.loadBusinessUnits();
    }
  }

  resetForms(): void {
    this.userForm.reset();
    this.isEditModeUser = false;
    this.selectedUserId = null;
    this.selectedUserRole = 'user'; // Set default role to 'user'

    this.roleForm.reset();
    this.isEditModeRole = false;
    this.selectedRoleId = null;

  }

  showError(message: string): void {
    this.alertMessage = message;
    this.alertType = 'error';
  }

  showSuccess(message: string): void {
    this.alertMessage = message;
    this.alertType = 'success';
  }

  onAlertDismissed(): void {
    this.alertMessage = null;
  }

  // --- User Management ---
  loadUsers(): void {
    this.userService.getUsers().subscribe({
      next: (data) => {
        this.users = data;
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load users.');
        console.error('Error loading users:', err);
      }
    });
  }

  loadRoles(): void {
    this.userService.getRoles().subscribe({
      next: (data) => {
        this.roles = data;
        this.userRolesOptions = data; // Populate roles for user assignment
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load roles.');
        console.error('Error loading roles:', err);
      }
    });
  }


  onUserSubmit(): void {
    if (this.userForm.invalid) {
      this.showError('Please fill in all required user fields correctly.');
      return;
    }

    const userData: UserCreate | UserUpdate = {
      first_name: this.userForm.value.firstName,
      last_name: this.userForm.value.lastName,
      email: this.userForm.value.email,
      password: this.userForm.value.password || undefined, // Only include password if provided
      roles: this.selectedUserRole ? [this.selectedUserRole] : [] // Include selected role as array
    };

    if (this.isEditModeUser && this.selectedUserId) {
      this.userService.updateUser(this.selectedUserId, userData).subscribe({
        next: () => {
          this.showSuccess('User updated successfully!');
          this.loadUsers();
          this.resetForms();
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error updating user:', err);
          
          // Handle different HTTP status codes with specific messages
          let errorMessage = 'Failed to update user.';
          
          if (err.status === 409) {
            // Conflict - typically duplicate email
            errorMessage = err.error?.detail || 'A user with this email address already exists. Please use a different email.';
          } else if (err.status === 400) {
            // Bad request - validation or constraint violations
            errorMessage = err.error?.detail || 'Invalid user data. Please check all fields and try again.';
          } else if (err.status === 404) {
            // User not found
            errorMessage = 'User not found. Please refresh the page and try again.';
          } else if (err.status === 503) {
            // Service unavailable - database connection issues
            errorMessage = err.error?.detail || 'Service is temporarily unavailable. Please try again in a few moments.';
          } else if (err.status === 500) {
            // Internal server error
            errorMessage = err.error?.detail || 'An unexpected error occurred. Please contact support if the problem persists.';
          } else if (err.error?.detail) {
            // Use backend-provided message if available
            errorMessage = err.error.detail;
          }
          
          this.showError(errorMessage);
        }
      });
    } else {
      if (!userData.password) {
        this.showError('Password is required for new users.');
        return;
      }
      this.userService.createUser(userData as UserCreate).subscribe({
        next: () => {
          this.showSuccess('User created successfully!');
          this.loadUsers();
          this.resetForms();
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error creating user:', err);
          
          // Handle different HTTP status codes with specific messages
          let errorMessage = 'Failed to create user.';
          
          if (err.status === 409) {
            // Conflict - typically duplicate email
            errorMessage = err.error?.detail || 'A user with this email address already exists. Please use a different email.';
          } else if (err.status === 400) {
            // Bad request - validation or constraint violations
            errorMessage = err.error?.detail || 'Invalid user data. Please check all fields and try again.';
          } else if (err.status === 503) {
            // Service unavailable - database connection issues
            errorMessage = err.error?.detail || 'Service is temporarily unavailable. Please try again in a few moments.';
          } else if (err.status === 500) {
            // Internal server error
            errorMessage = err.error?.detail || 'An unexpected error occurred. Please contact support if the problem persists.';
          } else if (err.error?.detail) {
            // Use backend-provided message if available
            errorMessage = err.error.detail;
          }
          
          this.showError(errorMessage);
        }
      });
    }
  }

  editUser(user: User): void {
    this.router.navigate(['/admin/edit-user', user.id]);
  }

  deleteUser(userId: string): void {
    const user = this.users.find(u => u.id === userId);
    const userName = user?.first_name && user?.last_name ? 
      `${user.first_name} ${user.last_name}` : 
      user?.email || 'this user';
    
    this.showConfirm(
      'Delete User',
      `Are you sure you want to delete ${userName}? This action cannot be undone.`,
      'Delete',
      () => {
        this.userService.deleteUser(userId).subscribe({
          next: () => {
            this.showSuccess('User deleted successfully!');
            this.loadUsers();
            this.resetForms();
          },
          error: (err: HttpErrorResponse) => {
            this.showError(err.error.detail || 'Failed to delete user.');
            console.error('Error deleting user:', err);
          }
        });
      }
    );
  }

  // --- Role Assignment for User Form ---
  onRoleRadioChange(roleName: string): void {
    this.selectedUserRole = roleName;
  }

  // --- Role Management ---
  onRoleSubmit(): void {
    if (this.roleForm.invalid) {
      this.showError('Please enter a role name.');
      return;
    }

    const roleData: RoleCreate | RoleUpdate = {
      name: this.roleForm.value.name
    };

    if (this.isEditModeRole && this.selectedRoleId) {
      this.userService.updateRole(this.selectedRoleId, roleData as RoleUpdate).subscribe({
        next: () => {
          this.showSuccess('Role updated successfully!');
          this.loadRoles();
          this.resetForms();
        },
        error: (err: HttpErrorResponse) => {
          this.showError(err.error.detail || 'Failed to update role.');
          console.error('Error updating role:', err);
        }
      });
    } else {
      this.userService.createRole(roleData as RoleCreate).subscribe({
        next: () => {
          this.showSuccess('Role created successfully!');
          this.loadRoles();
          this.resetForms();
        },
        error: (err: HttpErrorResponse) => {
          this.showError(err.error.detail || 'Failed to create role.');
          console.error('Error creating role:', err);
        }
      });
    }
  }

  editRole(role: Role): void {
    this.isEditModeRole = true;
    this.selectedRoleId = role.id;
    this.roleForm.patchValue({
      name: role.name
    });
  }

  deleteRole(roleId: string): void {
    const role = this.roles.find(r => r.id === roleId);
    const roleName = role?.name || 'this role';
    
    this.showConfirm(
      'Delete Role',
      `Are you sure you want to delete the "${roleName}" role? This will also remove it from all users and cannot be undone.`,
      'Delete',
      () => {
        this.userService.deleteRole(roleId).subscribe({
          next: () => {
            this.showSuccess('Role deleted successfully!');
            this.loadRoles();
            this.loadUsers(); // Users might have had this role, refresh
            this.resetForms();
          },
          error: (err: HttpErrorResponse) => {
            this.showError(err.error.detail || 'Failed to delete role.');
            console.error('Error deleting role:', err);
          }
        });
      }
    );
  }

  // --- MFA Setup ---
  setupMfa(user: User): void {
    this.selectedUserForMfa = user;
    this.userService.setupMfaForUser(user.email).subscribe({
      next: (response) => {
        this.mfaQrCodeBase64 = response.qr_code_base64;
        this.mfaSecret = response.secret;
        this.mfaProvisioningUri = response.provisioning_uri;
        this.showMfaSetupModal = true;
        this.showSuccess(`MFA setup initiated for ${user.email}.`);
        this.loadUsers(); // Refresh users to update MFA status
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to setup MFA.');
        console.error('Error setting up MFA:', err);
      }
    });
  }

  // --- MFA Removal ---
  removeMfa(user: User): void {
    this.showConfirm(
      'Remove MFA',
      `Are you sure you want to remove MFA for ${user.email}? This will disable two-factor authentication for this user.`,
      'Remove MFA',
      () => {
        this.userService.removeMfaForUser(user.email).subscribe({
          next: (response) => {
            this.showSuccess(`MFA removed for ${user.email}.`);
            this.loadUsers(); // Refresh users to update MFA status
          },
          error: (err: HttpErrorResponse) => {
            this.showError(err.error.detail || 'Failed to remove MFA.');
            console.error('Error removing MFA:', err);
          }
        });
      }
    );
  }

  closeMfaSetupModal(): void {
    this.showMfaSetupModal = false;
    this.mfaQrCodeBase64 = null;
    this.mfaSecret = null;
    this.mfaProvisioningUri = null;
    this.selectedUserForMfa = null;
    this.loadUsers(); // Refresh users to see if MFA secret is now set (though not displayed)
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      this.showSuccess('Secret key copied to clipboard!');
    }).catch(() => {
      this.showError('Failed to copy to clipboard.');
    });
  }

  // Header event handlers
  navigateToProfile(): void {
    this.router.navigate(['/profile']);
  }

  navigateToAdmin(): void {
    // Already on admin page, no navigation needed
  }

  navigateToCreateUser(): void {
    this.router.navigate(['/admin/create-user']);
  }

  logout(): void {
    this.authService.logout();
  }

  // --- Confirmation Modal ---
  showConfirm(title: string, message: string, buttonText: string, callback: () => void): void {
    this.confirmTitle = title;
    this.confirmMessage = message;
    this.confirmButtonText = buttonText;
    this.confirmCallback = callback;
    this.showConfirmModal = true;
  }

  closeConfirmModal(): void {
    this.showConfirmModal = false;
    this.confirmTitle = '';
    this.confirmMessage = '';
    this.confirmButtonText = '';
    this.confirmCallback = null;
  }

  confirmAction(): void {
    if (this.confirmCallback) {
      this.confirmCallback();
    }
    this.closeConfirmModal();
  }

  // --- Tab Management ---
  setActiveTab(tab: 'users' | 'organizations' | 'business-units'): void {
    this.activeTab = tab;
    if (tab === 'organizations') {
      this.loadOrganizations();
    } else if (tab === 'business-units') {
      this.loadBusinessUnits();
    }
  }

  // --- Role Checking ---
  hasAdminPrivileges(): boolean {
    return this.roleService.hasAdminPrivileges();
  }

  hasFullAdminAccess(): boolean {
    // Full admin access for user management - admin and super_user only
    return this.roleService.hasFullAdminAccess();
  }

  hasOrganizationAccess(): boolean {
    // Organizations only accessible to admin and super_user
    return this.roleService.hasOrganizationAccess();
  }

  hasBusinessUnitAccess(): boolean {
    // Business units accessible to admin, super_user, and firm_admin only (not group_admin)
    return this.roleService.hasBusinessUnitAccess();
  }

  // --- Organizations Management ---
  loadOrganizations(): void {
    this.organizationService.getOrganizations().subscribe({
      next: (data) => {
        this.organizations = data;
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load organizations.');
        console.error('Error loading organizations:', err);
      }
    });
  }

  navigateToCreateOrganization(): void {
    this.router.navigate(['/admin/create-organization']);
  }

  createOrganization(organizationData: OrganizationCreate): void {
    this.organizationService.createOrganization(organizationData).subscribe({
      next: (createdOrganization) => {
        this.showSuccess('Organization created successfully!');
        this.loadOrganizations(); // Refresh the list
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to create organization.');
        console.error('Error creating organization:', err);
      }
    });
  }

  editOrganization(org: Organization): void {
    this.router.navigate(['/admin/edit-organization', org.id]);
  }

  updateOrganization(organizationId: string, organizationData: OrganizationUpdate): void {
    this.organizationService.updateOrganization(organizationId, organizationData).subscribe({
      next: (updatedOrganization) => {
        this.showSuccess('Organization updated successfully!');
        this.loadOrganizations(); // Refresh the list
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to update organization.');
        console.error('Error updating organization:', err);
      }
    });
  }

  deleteOrganization(orgId: string): void {
    const organization = this.organizations.find(org => org.id === orgId);
    const orgName = organization?.company_name || 'this organization';
    
    this.showConfirm(
      'Delete Organization',
      `Are you sure you want to delete "${orgName}"? This action cannot be undone.`,
      'Delete',
      () => {
        this.organizationService.deleteOrganization(orgId).subscribe({
          next: () => {
            this.showSuccess('Organization deleted successfully!');
            this.loadOrganizations(); // Refresh the list
          },
          error: (err: HttpErrorResponse) => {
            this.showError(err.error.detail || 'Failed to delete organization.');
            console.error('Error deleting organization:', err);
          }
        });
      }
    );
  }

  // --- Business Units Management ---
  loadBusinessUnits(): void {
    // Backend now handles organizational filtering based on user role
    this.businessUnitService.getBusinessUnits().subscribe({
      next: (response) => {
        this.businessUnits = response.business_units;
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load business units.');
        console.error('Error loading business units:', err);
      }
    });
  }

  navigateToCreateBusinessUnit(): void {
    this.router.navigate(['/admin/create-business-unit']);
  }

  navigateToEditBusinessUnit(businessUnit: BusinessUnit): void {
    this.router.navigate(['/admin/edit-business-unit', businessUnit.id]);
  }


  deleteBusinessUnit(businessUnitId: string): void {
    const businessUnit = this.businessUnits.find(unit => unit.id === businessUnitId);
    const unitName = businessUnit?.name || 'this business unit';
    
    this.showConfirm(
      'Delete Business Unit',
      `Are you sure you want to delete "${unitName}"? This action cannot be undone and may affect child business units.`,
      'Delete',
      () => {
        this.businessUnitService.deleteBusinessUnit(businessUnitId).subscribe({
          next: () => {
            this.showSuccess('Business unit deleted successfully!');
            this.loadBusinessUnits();
          },
          error: (err: HttpErrorResponse) => {
            let errorMessage = 'Failed to delete business unit.';
            
            if (err.status === 400) {
              errorMessage = err.error?.detail || 'Cannot delete business unit that has child units. Delete or reassign child units first.';
            } else if (err.status === 404) {
              errorMessage = 'Business unit not found.';
            } else if (err.status === 403) {
              errorMessage = err.error?.detail || 'You do not have permission to delete this business unit.';
            } else if (err.error?.detail) {
              errorMessage = err.error.detail;
            }
            
            this.showError(errorMessage);
            console.error('Error deleting business unit:', err);
          }
        });
      }
    );
  }

}

@NgModule({
  imports: [
    CommonModule,
    AdminDashboardComponent
  ],
  exports: [AdminDashboardComponent]
})
export class AdminDashboardModule { }