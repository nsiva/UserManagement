import { Injectable } from '@angular/core';
import { AuthService } from './auth';
import { ROLES } from '../shared/constants/app-constants';

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
    return userRoles.some(role => ['admin', 'super_user'].includes(role));
  }

  /**
   * Check if user has full admin access (admin, super_user only)
   * @returns true if user has full admin privileges, false otherwise
   */
  hasFullAdminAccess(): boolean {
    const userRoles = this.authService.getUserRoles();
    return userRoles.some(role => ['admin', 'super_user'].includes(role));
  }

  /**
   * Check if user has business unit access (admin, super_user, firm_admin only)
   * @returns true if user can manage business units, false otherwise
   */
  hasBusinessUnitAccess(): boolean {
    const userRoles = this.authService.getUserRoles();
    return userRoles.some(role => ['admin', 'super_user', 'firm_admin'].includes(role));
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
    if (userRoles.includes('super_user')) {
      return allRoles;
    }
    
    // Admin cannot assign super_user
    if (userRoles.includes('admin')) {
      return allRoles.filter(role => role.name !== 'super_user');
    }
    
    // Firm admin cannot assign super_user, admin, firm_admin
    if (userRoles.includes('firm_admin')) {
      return allRoles.filter(role => 
        !['super_user', 'admin', 'firm_admin'].includes(role.name)
      );
    }
    
    // Group admin cannot assign super_user, admin, firm_admin, group_admin
    if (userRoles.includes('group_admin')) {
      return allRoles.filter(role => 
        !['super_user', 'admin', 'firm_admin', 'group_admin'].includes(role.name)
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
   * @param targetUserRoles Roles of the user being edited
   * @returns true if current user can edit the target user
   */
  canEditUser(targetUserRoles: string[]): boolean {
    const userRoles = this.getCurrentUserRoles();
    
    // Super user can edit anyone
    if (userRoles.includes('super_user')) {
      return true;
    }
    
    // Admin can edit anyone except super_user
    if (userRoles.includes('admin')) {
      return !targetUserRoles.includes('super_user');
    }
    
    // Firm admin can edit users except super_user, admin, firm_admin
    if (userRoles.includes('firm_admin')) {
      const restrictedRoles = ['super_user', 'admin', 'firm_admin'];
      return !targetUserRoles.some(role => restrictedRoles.includes(role));
    }
    
    // Group admin can only edit users with lower roles (user, viewer, editor, etc.)
    // Cannot edit firm_admin, admin, super_user
    if (userRoles.includes('group_admin')) {
      const restrictedRoles = ['super_user', 'admin', 'firm_admin', 'group_admin'];
      return !targetUserRoles.some(role => restrictedRoles.includes(role));
    }
    
    // Default: no edit permission
    return false;
  }
}