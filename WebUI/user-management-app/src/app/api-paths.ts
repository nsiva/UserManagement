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
  // Add other endpoints as needed
};
