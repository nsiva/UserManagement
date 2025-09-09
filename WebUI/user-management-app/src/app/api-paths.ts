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
  // Add other endpoints as needed
};
