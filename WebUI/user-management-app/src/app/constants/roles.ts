/**
 * Role constants for the User Management Frontend.
 * 
 * This module defines all role constants used throughout the application
 * to avoid hardcoded strings and ensure consistency with the backend API.
 */

// Role Constants
export const ADMIN = 'admin';
export const ORGANIZATION_ADMIN = 'firm_admin';
export const BUSINESS_UNIT_ADMIN = 'group_admin';
export const SUPER_USER = 'super_user';

// Role Groups for easier permission checking
export const ADMIN_ROLES = [ADMIN, SUPER_USER];
export const ORGANIZATIONAL_ROLES = [ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN];
export const ALL_ADMIN_ROLES = [ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN];

// Permission checking utilities
export function hasAdminAccess(userRoles: string[]): boolean {
  return userRoles.some(role => ADMIN_ROLES.includes(role));
}

export function hasOrganizationalAccess(userRoles: string[]): boolean {
  return userRoles.some(role => ORGANIZATIONAL_ROLES.includes(role));
}

export function hasAnyAdminAccess(userRoles: string[]): boolean {
  return userRoles.some(role => ALL_ADMIN_ROLES.includes(role));
}

export function hasOrganizationAdminAccess(userRoles: string[]): boolean {
  return userRoles.includes(ORGANIZATION_ADMIN);
}

export function hasBusinessUnitAdminAccess(userRoles: string[]): boolean {
  return userRoles.includes(BUSINESS_UNIT_ADMIN);
}