import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../services/auth';
import { UserService, User, UserCreate, UserUpdate, Role, RoleCreate, RoleUpdate } from '../../services/user';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-admin-dashboard',
  imports: [FormsModule,CommonModule, ReactiveFormsModule],
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.scss']

})
export class AdminDashboardComponent implements OnInit {
  activeTab: 'users' | 'roles' = 'users';

  // User Management
  users: User[] = [];
  userForm: FormGroup;
  isEditModeUser = false;
  selectedUserId: string | null = null;
  userRolesOptions: Role[] = []; // All available roles for assignment
  selectedUserRoles: string[] = []; // Roles for the currently selected user

  // Role Management
  roles: Role[] = [];
  roleForm: FormGroup;
  isEditModeRole = false;
  selectedRoleId: string | null = null;

  // MFA Setup
  showMfaSetupModal = false;
  mfaQrCodeBase64: string | null = null;
  mfaSecret: string | null = null;
  mfaProvisioningUri: string | null = null;
  selectedUserForMfa: User | null = null;


  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(
    private authService: AuthService,
    private userService: UserService,
    private fb: FormBuilder
  ) {
    this.userForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.minLength(6)]], // Password optional for update
      is_admin: [false]
    });

    this.roleForm = this.fb.group({
      name: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.loadUsers();
    this.loadRoles();
  }

  // --- General UI ---
  selectTab(tab: 'users' | 'roles'): void {
    this.activeTab = tab;
    this.errorMessage = null;
    this.successMessage = null;
    this.resetForms();
  }

  resetForms(): void {
    this.userForm.reset({ is_admin: false });
    this.isEditModeUser = false;
    this.selectedUserId = null;
    this.selectedUserRoles = [];

    this.roleForm.reset();
    this.isEditModeRole = false;
    this.selectedRoleId = null;
  }

  showError(message: string): void {
    this.errorMessage = message;
    this.successMessage = null;
  }

  showSuccess(message: string): void {
    this.successMessage = message;
    this.errorMessage = null;
  }

  // --- User Management ---
  loadUsers(): void {
    this.userService.getUsers().subscribe({
      next: (data) => {
        this.users = data;
        this.errorMessage = null;
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
        this.errorMessage = null;
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
      email: this.userForm.value.email,
      is_admin: this.userForm.value.is_admin,
      password: this.userForm.value.password || undefined, // Only include password if provided
      roles: this.selectedUserRoles // Include selected roles
    };

    if (this.isEditModeUser && this.selectedUserId) {
      this.userService.updateUser(this.selectedUserId, userData).subscribe({
        next: () => {
          this.showSuccess('User updated successfully!');
          this.loadUsers();
          this.resetForms();
        },
        error: (err: HttpErrorResponse) => {
          this.showError(err.error.detail || 'Failed to update user.');
          console.error('Error updating user:', err);
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
          this.showError(err.error.detail || 'Failed to create user.');
          console.error('Error creating user:', err);
        }
      });
    }
  }

  editUser(user: User): void {
    this.isEditModeUser = true;
    this.selectedUserId = user.id;
    this.userForm.patchValue({
      email: user.email,
      is_admin: user.is_admin,
      password: '' // Don't pre-fill password for security
    });
    this.selectedUserRoles = [...user.roles]; // Clone roles for editing
  }

  deleteUser(userId: string): void {
    if (confirm('Are you sure you want to delete this user?')) {
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
  }

  // --- Role Assignment for User Form ---
  onRoleCheckboxChange(roleName: string, event: Event): void {
    const isChecked = (event.target as HTMLInputElement).checked;
    if (isChecked) {
      this.selectedUserRoles.push(roleName);
    } else {
      this.selectedUserRoles = this.selectedUserRoles.filter(name => name !== roleName);
    }
  }

  isRoleSelected(roleName: string): boolean {
    return this.selectedUserRoles.includes(roleName);
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
    if (confirm('Are you sure you want to delete this role? This will also remove it from all users.')) {
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
      },
      error: (err: HttpErrorResponse) => {
        this.showError(err.error.detail || 'Failed to setup MFA.');
        console.error('Error setting up MFA:', err);
      }
    });
  }

  closeMfaSetupModal(): void {
    this.showMfaSetupModal = false;
    this.mfaQrCodeBase64 = null;
    this.mfaSecret = null;
    this.mfaProvisioningUri = null;
    this.selectedUserForMfa = null;
    this.loadUsers(); // Refresh users to see if MFA secret is now set (though not displayed)
  }

  logout(): void {
    this.authService.logout();
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