import { Injectable } from '@angular/core';
import { AuthService } from './auth';
import { ROLES } from '../shared/constants/app-constants';
import { ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN } from '../constants/roles';

@Injectable({
  providedIn: 'root'
})
export class RoleService {

  constructor(private authService: AuthService) {}

  /**
   * Check if the current user has admin privileges
   * @returns true if user has any admin role, false otherwise
   */
  hasAdminPrivileges(): boolean {
    const userRoles = this.authService.getUserRoles();
    return userRoles.some(role => (ROLES.ADMIN_ROLES as readonly string[]).includes(role));
  }

  /**
   * Check if the current user has a specific role
   * @param role The role to check for
   * @returns true if user has the specified role, false otherwise
   */
  hasRole(role: string): boolean {
    const userRoles = this.authService.getUserRoles();
    return userRoles.includes(role);
  }

  /**
   * Check if the current user has any of the specified roles
   * @param roles Array of roles to check for
   * @returns true if user has any of the specified roles, false otherwise
   */
  hasAnyRole(roles: string[]): boolean {
    const userRoles = this.authService.getUserRoles();
    return userRoles.some(role => roles.includes(role));
  }

  /**
   * Check if user has organization management access (admin, super_user only)
   * @returns true if user can manage organizations, false otherwise
   */
  hasOrganizationAccess(): boolean {
    const userRoles = this.authService.getUserRoles();
    return userRoles.some(role => [ADMIN, SUPER_USER].includes(role));
  }

  /**
   * Check if user has full admin access (admin, super_user only)
   * @returns true if user has full admin privileges, false otherwise
   */
  hasFullAdminAccess(): boolean {
    const userRoles = this.authService.getUserRoles();
    return userRoles.some(role => [ADMIN, SUPER_USER].includes(role));
  }

  /**
   * Check if user has business unit access (admin, super_user, firm_admin only)
   * @returns true if user can manage business units, false otherwise
   */
  hasBusinessUnitAccess(): boolean {
    const userRoles = this.authService.getUserRoles();
    return userRoles.some(role => [ADMIN, SUPER_USER, ORGANIZATION_ADMIN].includes(role));
  }

  /**
   * Get all roles for the current user
   * @returns Array of user roles
   */
  getCurrentUserRoles(): string[] {
    return this.authService.getUserRoles();
  }

  /**
   * Get roles that the current user can assign to others
   * Based on role hierarchy restrictions:
   * - group_admin: cannot assign super_user, admin, firm_admin, group_admin
   * - firm_admin: cannot assign super_user, admin, firm_admin
   * - admin: cannot assign super_user
   * - super_user: can assign any role
   * @param allRoles Array of all available roles
   * @returns Array of roles that current user can assign
   */
  getAssignableRoles(allRoles: any[]): any[] {
    const userRoles = this.getCurrentUserRoles();
    
    // Super user can assign any role
    if (userRoles.includes(SUPER_USER)) {
      return allRoles;
    }
    
    // Admin cannot assign super_user
    if (userRoles.includes(ADMIN)) {
      return allRoles.filter(role => role.name !== SUPER_USER);
    }
    
    // Firm admin cannot assign super_user, admin, firm_admin
    if (userRoles.includes(ORGANIZATION_ADMIN)) {
      return allRoles.filter(role => 
        ![SUPER_USER, ADMIN, ORGANIZATION_ADMIN].includes(role.name)
      );
    }
    
    // Group admin cannot assign super_user, admin, firm_admin, group_admin
    if (userRoles.includes(BUSINESS_UNIT_ADMIN)) {
      return allRoles.filter(role => 
        ![SUPER_USER, ADMIN, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN].includes(role.name)
      );
    }
    
    // Default: no assignable roles for other users
    return [];
  }

  /**
   * Get roles that the current user can assign to a specific user
   * If the target user is the current user, they cannot change their own role
   * @param allRoles Array of all available roles
   * @param targetUserEmail Email of the user being edited
   * @param currentUserEmail Email of the current user
   * @returns Array of roles that current user can assign to the target user
   */
  getAssignableRolesForUser(allRoles: any[], targetUserEmail: string, currentUserEmail: string): any[] {
    // If user is editing themselves, return empty array (cannot change own role)
    if (targetUserEmail === currentUserEmail) {
      return [];
    }
    
    // Otherwise, use normal role filtering
    return this.getAssignableRoles(allRoles);
  }

  /**
   * Check if the current user is editing their own profile
   * @param targetUserEmail Email of the user being edited
   * @param currentUserEmail Email of the current user
   * @returns true if user is editing themselves
   */
  isEditingSelf(targetUserEmail: string, currentUserEmail: string): boolean {
    return targetUserEmail === currentUserEmail;
  }

  /**
   * Check if the current user can edit another user based on role hierarchy
   * group_admin cannot edit users with roles: firm_admin, admin, super_user
   * All users can edit their own profile (first name, last name only)
   * @param targetUserRoles Roles of the user being edited
   * @param targetUserEmail Email of the user being edited (optional, for self-edit check)
   * @returns true if current user can edit the target user
   */
  canEditUser(targetUserRoles: string[], targetUserEmail?: string): boolean {
    const userRoles = this.getCurrentUserRoles();
    
    // Check if user is editing themselves - always allowed for profile updates
    if (targetUserEmail) {
      const currentUserEmail = this.authService.getUserEmail();
      if (targetUserEmail === currentUserEmail) {
        return true; // Users can always edit their own profile
      }
    }
    
    // Super user can edit anyone
    if (userRoles.includes(SUPER_USER)) {
      return true;
    }
    
    // Admin can edit anyone except super_user
    if (userRoles.includes(ADMIN)) {
      return !targetUserRoles.includes(SUPER_USER);
    }
    
    // Firm admin can edit users except super_user, admin, firm_admin
    if (userRoles.includes(ORGANIZATION_ADMIN)) {
      const restrictedRoles = [SUPER_USER, ADMIN, ORGANIZATION_ADMIN];
      return !targetUserRoles.some(role => restrictedRoles.includes(role));
    }
    
    // Group admin can only edit users with lower roles (user, viewer, editor, etc.)
    // Cannot edit firm_admin, admin, super_user, group_admin
    if (userRoles.includes(BUSINESS_UNIT_ADMIN)) {
      const restrictedRoles = [SUPER_USER, ADMIN, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN];
      return !targetUserRoles.some(role => restrictedRoles.includes(role));
    }
    
    // Default: no edit permission
    return false;
  }
}