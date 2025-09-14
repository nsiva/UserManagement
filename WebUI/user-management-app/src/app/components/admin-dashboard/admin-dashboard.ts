import { Component, OnInit, HostListener, ChangeDetectorRef } from '@angular/core';
import { AuthService } from '../../services/auth';
import { RoleService } from '../../services/role.service';
import { UserService, User, UserCreate, UserUpdate, Role, RoleCreate, RoleUpdate } from '../../services/user';
import { UserProfileService } from '../../services/user-profile.service';
import { OrganizationService, Organization, OrganizationCreate, OrganizationUpdate } from '../../services/organization';
import { BusinessUnitService, BusinessUnit, BusinessUnitCreate, BusinessUnitUpdate } from '../../services/business-unit';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { AlertComponent, AlertType } from '../../shared/components/alert/alert.component';
import { AutocompleteComponent, AutocompleteOption } from '../../shared/components/autocomplete/autocomplete.component';
import { APP_NAME, PAGES } from '../../shared/constants/app-constants';
import { 
  ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN,
  hasAdminAccess, hasOrganizationAdminAccess, hasBusinessUnitAdminAccess 
} from '../../constants/roles';

@Component({
  selector: 'app-admin-dashboard',
  imports: [FormsModule, CommonModule, ReactiveFormsModule, HeaderComponent, AlertComponent, AutocompleteComponent],
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.scss']

})
export class AdminDashboardComponent implements OnInit {
  // Role constants for template access
  readonly ADMIN_ROLE = ADMIN;
  
  // Filter constants
  readonly ALL_BUSINESS_UNITS = 'all';
  
  // Header configuration
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: PAGES.ADMIN_DASHBOARD,
    showUserMenu: true
  };

  activeTab: 'users' | 'organizations' | 'business-units' = 'users';

  // User Management
  users: User[] = [];
  filteredUsers: User[] = [];
  selectedUserOrganizationId: string = '';
  selectedUserBusinessUnitId: string = '';
  filteredUserBusinessUnits: BusinessUnit[] = [];
  // Firm admin specific properties
  selectedFirmAdminBusinessUnitId: string = '';
  firmAdminBusinessUnits: BusinessUnit[] = [];
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
  organizationOptions: AutocompleteOption[] = [];
  userOrganizationOptions: AutocompleteOption[] = [];

  // Business Units Management
  businessUnits: BusinessUnit[] = [];
  filteredBusinessUnits: BusinessUnit[] = [];
  userBusinessUnitOptions: AutocompleteOption[] = [];
  firmAdminBusinessUnitOptions: AutocompleteOption[] = [];
  selectedOrganizationId: string = '';

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
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
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

    // Check for query parameters to restore state when returning from edit operations
    this.restoreStateFromQueryParams();

    // Set default tab to the first available tab based on the new order: Organizations -> Business Units -> Users
    // Only set default if no state was restored from query parameters
    if (!this.route.snapshot.queryParams['tab']) {
      this.setFirstActiveTab();
    }

    // Initialize filtered arrays
    this.filteredBusinessUnits = [];
    this.filteredUsers = [];
    this.filteredUserBusinessUnits = [];
    this.firmAdminBusinessUnits = [];
  }

  // --- General UI ---
  selectTab(tab: 'users' | 'organizations' | 'business-units'): void {
    this.activeTab = tab;
    this.alertMessage = null;
    this.resetForms();
    if (tab === 'users') {
      // Preserve filters when switching to users tab - DO NOT reset selections
      this.loadUsers();
      
      // Apply existing filters if they exist
      if (this.hasFullAdminAccess() && this.selectedUserOrganizationId) {
        this.loadBusinessUnitsForUserFilter();
      } else if (this.isFirmAdmin() && this.firmAdminBusinessUnits.length === 0) {
        this.loadFirmAdminBusinessUnits();
      } else {
        this.filterUsers();
      }
    } else if (tab === 'organizations') {
      this.loadOrganizations();
    } else if (tab === 'business-units') {
      // Preserve organization filter when switching to business units tab - DO NOT reset selections
      this.loadBusinessUnits();
      
      // Apply existing organization filter if it exists
      if (this.selectedOrganizationId) {
        this.filterBusinessUnits();
      }
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
        this.filterUsers(); // Apply current filters
        
        // Load organizations for admin/super_user to populate dropdown
        if (this.hasFullAdminAccess() && this.organizations.length === 0) {
          this.loadOrganizations();
        }
        
        // Load business units for firm_admin to populate dropdown
        if (this.isFirmAdmin() && this.firmAdminBusinessUnits.length === 0) {
          this.loadFirmAdminBusinessUnits();
        }
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
    // Preserve current state when navigating to edit user
    const queryParams: any = {
      returnTo: '/admin',
      tab: this.activeTab
    };
    
    // For admin/super_user, preserve both organization and business unit selections
    if (this.hasFullAdminAccess()) {
      if (this.selectedUserOrganizationId) {
        queryParams.orgId = this.selectedUserOrganizationId;
      }
      if (this.selectedUserBusinessUnitId) {
        queryParams.buId = this.selectedUserBusinessUnitId;
      }
    }
    // For firm_admin, preserve business unit selection
    else if (this.isFirmAdmin()) {
      if (this.selectedFirmAdminBusinessUnitId) {
        queryParams.buId = this.selectedFirmAdminBusinessUnitId;
      }
    }
    
    this.router.navigate(['/admin/edit-user', user.id], { 
      queryParams 
    });
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
    // Reset to the first available tab when navigating to admin
    this.setFirstActiveTab();
  }

  private setFirstActiveTab(): void {
    // Set the first available tab based on the order: Organizations -> Business Units -> Users
    if (this.roleService.hasOrganizationAccess()) {
      this.setActiveTab('organizations');
    } else if (this.roleService.hasBusinessUnitAccess()) {
      this.setActiveTab('business-units');
    } else {
      this.setActiveTab('users');
    }
  }

  private restoreStateFromQueryParams(): void {
    const queryParams = this.route.snapshot.queryParams;
    
    // Restore tab
    if (queryParams['tab']) {
      this.activeTab = queryParams['tab'] as 'users' | 'organizations' | 'business-units';
    }
    
    // Restore selected organization for business units tab
    if (queryParams['orgId'] && this.hasFullAdminAccess()) {
      this.selectedOrganizationId = queryParams['orgId'];
      // Synchronize organization selection across tabs
      this.selectedUserOrganizationId = queryParams['orgId'];
      
      // If restoring for users tab, also restore user-specific selections
      if (this.activeTab === 'users') {
        // Load organizations and business units for user filtering
        this.loadOrganizationsAndRestoreState(queryParams['buId']);
        
        // Also ensure users are loaded and filtered after restoration
        setTimeout(() => {
          if (!this.users.length) {
            this.loadUsers();
          } else {
            this.filterUsers();
          }
        }, 200);
      } else {
        // Load organizations and business units to restore the filtered state for business-units tab
        this.loadOrganizationsAndRestoreState();
      }
    }
    
    // Restore business unit selection for firm_admin users
    if (queryParams['buId'] && this.isFirmAdmin()) {
      this.selectedFirmAdminBusinessUnitId = queryParams['buId'];
      
      // Load business units for firm_admin
      this.loadFirmAdminBusinessUnits();
      
      // Also ensure users are loaded and filtered for firm_admin after restoration
      if (this.activeTab === 'users') {
        setTimeout(() => {
          if (!this.users.length) {
            this.loadUsers();
          } else {
            this.filterUsers();
          }
        }, 200);
      }
    }
    
    // Clear query parameters after restoring state to keep URL clean
    if (Object.keys(queryParams).length > 0) {
      this.router.navigate([], { 
        relativeTo: this.route, 
        queryParams: {},
        replaceUrl: true 
      });
    }
  }

  navigateToCreateUser(): void {
    // Preserve current state when navigating to create user
    const queryParams: any = {
      returnTo: '/admin',
      tab: this.activeTab
    };
    
    // For admin/super_user, preserve both organization and business unit selections if on users tab
    if (this.activeTab === 'users' && this.hasFullAdminAccess()) {
      if (this.selectedUserOrganizationId) {
        queryParams.orgId = this.selectedUserOrganizationId;
      }
      if (this.selectedUserBusinessUnitId) {
        queryParams.buId = this.selectedUserBusinessUnitId;
      }
    }
    // For firm_admin, preserve business unit selection if on users tab
    else if (this.activeTab === 'users' && this.isFirmAdmin()) {
      if (this.selectedFirmAdminBusinessUnitId) {
        queryParams.buId = this.selectedFirmAdminBusinessUnitId;
      }
    }
    
    this.router.navigate(['/admin/create-user'], { 
      queryParams 
    });
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
    if (tab === 'users') {
      // Preserve filters when switching to users tab - DO NOT reset selections
      this.loadUsers();
      
      // Apply existing filters if they exist
      if (this.hasFullAdminAccess() && this.selectedUserOrganizationId) {
        this.loadBusinessUnitsForUserFilter();
      } else if (this.isFirmAdmin() && this.firmAdminBusinessUnits.length === 0) {
        this.loadFirmAdminBusinessUnits();
      } else {
        this.filterUsers();
      }
    } else if (tab === 'organizations') {
      this.loadOrganizations();
    } else if (tab === 'business-units') {
      // Preserve organization filter when switching to business units tab - DO NOT reset selections
      this.loadBusinessUnits();
      
      // Apply existing organization filter if it exists
      if (this.selectedOrganizationId) {
        this.filterBusinessUnits();
      }
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

  isFirmAdmin(): boolean {
    // Check if user is a firm_admin (but not admin or super_user)
    const userRoles = this.authService.getUserRoles();
    return userRoles.includes(ORGANIZATION_ADMIN) && !this.hasFullAdminAccess();
  }

  isGroupAdmin(): boolean {
    // Check if user is a group_admin (but not firm_admin, admin, or super_user)
    const userRoles = this.authService.getUserRoles();
    return userRoles.includes(BUSINESS_UNIT_ADMIN) && 
           !userRoles.includes(ORGANIZATION_ADMIN) && 
           !this.hasFullAdminAccess();
  }

  shouldShowUsersTable(): boolean {
    // Admin/super_user: show when both organization and business unit are selected
    if (this.hasFullAdminAccess()) {
      return !!(this.selectedUserOrganizationId && this.selectedUserBusinessUnitId);
    }
    // Firm_admin: show when business unit is selected
    else if (this.isFirmAdmin()) {
      return !!this.selectedFirmAdminBusinessUnitId;
    }
    // Group_admin: always show (no filtering needed)
    else {
      return true;
    }
  }

  hasOrganizationAccess(): boolean {
    // Organizations only accessible to admin and super_user
    return this.roleService.hasOrganizationAccess();
  }

  hasBusinessUnitAccess(): boolean {
    // Business units accessible to admin, super_user, and firm_admin only (not group_admin)
    return this.roleService.hasBusinessUnitAccess();
  }

  // --- User Edit Permission ---
  canEditUser(user: any): boolean {
    // Check if current user can edit the target user based on role hierarchy
    // Pass the user's email to check if they're editing themselves
    return this.roleService.canEditUser(user.roles, user.email);
  }

  // --- Organizations Management ---
  loadOrganizations(): void {
    this.organizationService.getOrganizations().subscribe({
      next: (data) => {
        this.organizations = data;
        this.updateOrganizationOptions();
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load organizations.');
        console.error('Error loading organizations:', err);
      }
    });
  }

  loadOrganizationsAndRestoreState(businessUnitId?: string): void {
    console.log('AdminDashboard: Loading organizations and restoring state...');
    console.log('AdminDashboard: Target org ID to restore:', this.selectedOrganizationId);
    console.log('AdminDashboard: Target user org ID to restore:', this.selectedUserOrganizationId);
    console.log('AdminDashboard: Target business unit ID to restore:', businessUnitId);
    
    this.organizationService.getOrganizations().subscribe({
      next: (data) => {
        this.organizations = data;
        this.updateOrganizationOptions();
        
        console.log('AdminDashboard: Organizations loaded, total options:', this.organizationOptions.length);
        console.log('AdminDashboard: User org options:', this.userOrganizationOptions.length);
        
        // Debug: Check if target organization exists in options
        const orgExists = this.organizationOptions.find(opt => opt.id === this.selectedOrganizationId);
        const userOrgExists = this.userOrganizationOptions.find(opt => opt.id === this.selectedUserOrganizationId);
        console.log('AdminDashboard: Target org exists in options:', !!orgExists, orgExists?.label);
        console.log('AdminDashboard: Target user org exists in options:', !!userOrgExists, userOrgExists?.label);
        
        // Force change detection and trigger autocomplete updates
        setTimeout(() => {
          console.log('AdminDashboard: Forcing change detection and triggering autocomplete updates');
          this.cdr.detectChanges();
          
          // Manually trigger the autocomplete change handlers to ensure proper state
          if (this.activeTab === 'business-units' && this.selectedOrganizationId) {
            console.log('AdminDashboard: Triggering organization autocomplete change for business-units tab');
            // Don't call the handler directly as it would cause an infinite loop
            // Instead, just ensure the filter is applied
            this.filterBusinessUnits();
          } else if (this.activeTab === 'users' && this.selectedUserOrganizationId) {
            console.log('AdminDashboard: Triggering user organization autocomplete change for users tab');
            this.filterUsers();
          }
        }, 100);
        
        // After organizations are loaded and options updated, load business units
        this.loadBusinessUnitsAndRestoreState(businessUnitId);
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load organizations.');
        console.error('Error loading organizations:', err);
      }
    });
  }

  loadBusinessUnitsAndRestoreState(businessUnitId?: string): void {
    console.log('AdminDashboard: Loading business units and restoring state...');
    console.log('AdminDashboard: Current selected org ID:', this.selectedOrganizationId);
    console.log('AdminDashboard: Current selected user org ID:', this.selectedUserOrganizationId);
    
    if (this.activeTab === 'users') {
      // For users tab, load business units for user filtering
      this.loadBusinessUnitsForUserFilterAndRestore(businessUnitId);
    } else {
      // For business units tab, load all business units
      this.businessUnitService.getBusinessUnits().subscribe({
        next: (response) => {
          this.businessUnits = response.business_units;
          this.filterBusinessUnits();
          console.log('AdminDashboard: Business units loaded and filtered for restoration');
          
          // Debug: Log current selections
          console.log('AdminDashboard: Business Units tab - Organization options:', this.organizationOptions.length);
          console.log('AdminDashboard: Business Units tab - Selected organization ID:', this.selectedOrganizationId);
        },
        error: (err: HttpErrorResponse) => {
          this.showError(err.error.detail || 'Failed to load business units.');
          console.error('Error loading business units:', err);
        }
      });
    }
  }

  loadBusinessUnitsForUserFilterAndRestore(businessUnitId?: string): void {
    this.businessUnitService.getBusinessUnits(this.selectedUserOrganizationId).subscribe({
      next: (response) => {
        this.filteredUserBusinessUnits = response.business_units;
        this.updateUserBusinessUnitOptions();
        
        // Restore business unit selection if available
        if (businessUnitId) {
          // Use setTimeout to ensure options are loaded before setting the value
          setTimeout(() => {
            this.selectedUserBusinessUnitId = businessUnitId;
            console.log('AdminDashboard: Restored user business unit selection:', businessUnitId);
            console.log('AdminDashboard: Available business unit options:', this.userBusinessUnitOptions.length);
            
            // Force change detection to ensure autocomplete updates
            this.cdr.detectChanges();
            
            // Apply filters after restoration
            this.filterUsers();
          }, 100);
        } else {
          // Apply filters even when no business unit to restore
          this.filterUsers();
        }
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load business units for user filter.');
        console.error('Error loading business units for user filter:', err);
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
        this.filterBusinessUnits(); // Apply current organization filter
        
        // Load organizations for admin/super_user to populate dropdown
        if (this.hasFullAdminAccess() && this.organizations.length === 0) {
          this.loadOrganizations();
        }
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load business units.');
        console.error('Error loading business units:', err);
      }
    });
  }

  navigateToCreateBusinessUnit(): void {
    // Preserve current state when navigating to create business unit
    const queryParams: any = {
      returnTo: '/admin',
      tab: this.activeTab
    };
    
    // For admin/super_user, preserve the selected organization
    if (this.hasFullAdminAccess() && this.selectedOrganizationId) {
      queryParams.orgId = this.selectedOrganizationId;
    }
    
    this.router.navigate(['/admin/create-business-unit'], { 
      queryParams 
    });
  }

  navigateToEditBusinessUnit(businessUnit: BusinessUnit): void {
    // Preserve current state when navigating to edit business unit
    const queryParams: any = {
      returnTo: '/admin',
      tab: this.activeTab
    };
    
    // For admin/super_user, preserve the selected organization
    if (this.hasFullAdminAccess() && this.selectedOrganizationId) {
      queryParams.orgId = this.selectedOrganizationId;
    }
    
    this.router.navigate(['/admin/edit-business-unit', businessUnit.id], { 
      queryParams 
    });
  }

  // --- User Filtering ---
  onUserOrganizationFilterChange(): void {
    // Reset business unit selection when organization changes
    this.selectedUserBusinessUnitId = '';
    this.filteredUserBusinessUnits = [];
    
    // When admin/super_user changes organization in Users tab,
    // also update the business units organization filter for consistency
    if (this.hasFullAdminAccess()) {
      this.selectedOrganizationId = this.selectedUserOrganizationId;
      this.filteredBusinessUnits = [];
    }
    
    // Load business units for the selected organization
    if (this.selectedUserOrganizationId) {
      this.loadBusinessUnitsForUserFilter();
    } else {
      this.filterUsers();
    }
  }

  onUserBusinessUnitFilterChange(): void {
    this.filterUsers();
  }

  loadBusinessUnitsForUserFilter(): void {
    // Load business units for the selected organization
    this.businessUnitService.getBusinessUnits().subscribe({
      next: (response) => {
        // Filter business units by selected organization
        this.filteredUserBusinessUnits = response.business_units.filter(
          unit => unit.organization_id === this.selectedUserOrganizationId
        );
        this.updateUserBusinessUnitOptions();
        this.filterUsers(); // Apply user filtering
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load business units.');
        console.error('Error loading business units for user filter:', err);
      }
    });
  }

  filterUsers(): void {
    if (this.hasFullAdminAccess()) {
      // For admin/super_user: Show empty array if no business unit is selected
      if (!this.selectedUserBusinessUnitId || this.selectedUserBusinessUnitId === '') {
        this.filteredUsers = [];
      } else if (this.selectedUserBusinessUnitId === this.ALL_BUSINESS_UNITS) {
        // Show all users within the selected organization when "All Business Units" is selected
        this.filteredUsers = this.users.filter(user => {
          // Get the organization_id from business units that belong to the selected organization
          const userBusinessUnit = this.filteredUserBusinessUnits.find(unit => unit.id === user.business_unit_id);
          return userBusinessUnit && userBusinessUnit.organization_id === this.selectedUserOrganizationId;
        });
      } else {
        // Filter users by selected business unit
        this.filteredUsers = this.users.filter(
          user => user.business_unit_id === this.selectedUserBusinessUnitId
        );
      }
    } else if (this.isFirmAdmin()) {
      // For firm_admin: Show empty array if no business unit is selected
      if (!this.selectedFirmAdminBusinessUnitId || this.selectedFirmAdminBusinessUnitId === '') {
        this.filteredUsers = [];
      } else if (this.selectedFirmAdminBusinessUnitId === this.ALL_BUSINESS_UNITS) {
        // Show all users within firm_admin's organization when "All Business Units" is selected
        this.filteredUsers = this.users.filter(user => {
          // Get the organization_id from business units that belong to firm_admin's organization
          const userBusinessUnit = this.firmAdminBusinessUnits.find(unit => unit.id === user.business_unit_id);
          return !!userBusinessUnit; // If found in firm_admin's business units, it's in their organization
        });
      } else {
        // Filter users by selected business unit
        this.filteredUsers = this.users.filter(
          user => user.business_unit_id === this.selectedFirmAdminBusinessUnitId
        );
      }
    } else {
      // For other users (group_admin), show all users based on their permissions
      this.filteredUsers = [...this.users];
    }
  }

  // --- Firm Admin User Filtering ---
  onFirmAdminBusinessUnitFilterChange(): void {
    this.filterUsers();
  }

  loadFirmAdminBusinessUnits(): void {
    // Load business units for firm_admin (backend should handle organization filtering based on user)
    this.businessUnitService.getBusinessUnits().subscribe({
      next: (response) => {
        this.firmAdminBusinessUnits = response.business_units;
        this.updateFirmAdminBusinessUnitOptions();
        this.filterUsers(); // Apply user filtering
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to load business units.');
        console.error('Error loading business units for firm_admin:', err);
      }
    });
  }

  // --- Organization Filter for Business Units ---
  onOrganizationFilterChange(): void {
    // When admin/super_user changes organization in Business Units tab,
    // also update the user organization filter for consistency
    if (this.hasFullAdminAccess()) {
      this.selectedUserOrganizationId = this.selectedOrganizationId;
      // Reset business unit selection since organization changed
      this.selectedUserBusinessUnitId = '';
      this.filteredUserBusinessUnits = [];
    }
    this.filterBusinessUnits();
  }

  filterBusinessUnits(): void {
    if (!this.selectedOrganizationId || this.selectedOrganizationId === '') {
      // For admin/super_user: Show empty array if no organization is selected
      // For other roles: Show all business units (based on their permissions)
      if (this.hasFullAdminAccess()) {
        this.filteredBusinessUnits = [];
      } else {
        this.filteredBusinessUnits = [...this.businessUnits];
      }
    } else {
      // Filter business units by selected organization
      this.filteredBusinessUnits = this.businessUnits.filter(
        unit => unit.organization_id === this.selectedOrganizationId
      );
    }
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

  // --- Autocomplete Options Update Methods ---
  private updateOrganizationOptions(): void {
    this.organizationOptions = this.organizations.map(org => ({
      id: org.id,
      label: org.company_name
    }));
    
    // Update user organization options as well
    this.userOrganizationOptions = [...this.organizationOptions];
  }

  private updateUserBusinessUnitOptions(): void {
    this.userBusinessUnitOptions = [
      { id: this.ALL_BUSINESS_UNITS, label: 'All Business Units' },
      ...this.filteredUserBusinessUnits.map(unit => ({
        id: unit.id,
        label: unit.name
      }))
    ];
  }

  private updateFirmAdminBusinessUnitOptions(): void {
    this.firmAdminBusinessUnitOptions = [
      { id: this.ALL_BUSINESS_UNITS, label: 'All Business Units' },
      ...this.firmAdminBusinessUnits.map(unit => ({
        id: unit.id,
        label: unit.name
      }))
    ];
  }

  // --- Autocomplete Event Handlers ---
  onOrganizationAutocompleteChange(organizationId: string): void {
    this.selectedOrganizationId = organizationId;
    this.onOrganizationFilterChange();
  }

  onUserOrganizationAutocompleteChange(organizationId: string): void {
    this.selectedUserOrganizationId = organizationId;
    this.onUserOrganizationFilterChange();
  }

  onUserBusinessUnitAutocompleteChange(businessUnitId: string): void {
    this.selectedUserBusinessUnitId = businessUnitId;
    this.onUserBusinessUnitFilterChange();
  }

  onFirmAdminBusinessUnitAutocompleteChange(businessUnitId: string): void {
    this.selectedFirmAdminBusinessUnitId = businessUnitId;
    this.onFirmAdminBusinessUnitFilterChange();
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