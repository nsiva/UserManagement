export const API_PATHS = {
  mfaVerify: '/auth/mfa/verify',
  mfaSetup: '/auth/mfa/setup',
  login: '/auth/login',
  userProfile: '/profiles/me',
  resetPassword: '/auth/reset_password',
  forgotPassword: '/auth/forgot-password',
  verifyResetToken: '/auth/verify-reset-token',
  setNewPassword: '/auth/set-new-password',
  // Organization endpoints
  organizations: '/organizations',
  organizationById: (id: string) => `/organizations/${id}`,
  // Business Unit endpoints
  businessUnits: '/business-units',
  businessUnitById: (id: string) => `/business-units/${id}`,
  businessUnitHierarchy: (organizationId: string) => `/business-units/hierarchy/${organizationId}`,
  // Basic Functional Roles endpoints
  functionalRoles: '/functional-roles',
  functionalRoleById: (id: string) => `/functional-roles/${id}`,
  functionalRolesByCategory: '/functional-roles/categories',
  // Functional Roles Hierarchy endpoints
  functionalRolesHierarchy: '/functional-roles-hierarchy',
  orgFunctionalRoles: (orgId: string) => `/functional-roles-hierarchy/organizations/${orgId}/roles`,
  orgFunctionalRolesBulk: (orgId: string) => `/functional-roles-hierarchy/organizations/${orgId}/roles/bulk`,
  buFunctionalRoles: (buId: string) => `/functional-roles-hierarchy/business-units/${buId}/roles`,
  buFunctionalRolesBulk: (buId: string) => `/functional-roles-hierarchy/business-units/${buId}/roles/bulk`,
  buAvailableRoles: (buId: string) => `/functional-roles-hierarchy/business-units/${buId}/available-roles`,
  userAvailableRoles: (userId: string) => `/functional-roles-hierarchy/users/${userId}/available-roles`,
  userFunctionalRolesAssign: (userId: string) => `/functional-roles/users/${userId}/assign`,
  functionalRoleHierarchyView: '/functional-roles-hierarchy/hierarchy',
  // Add other endpoints as needed
};
