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
}