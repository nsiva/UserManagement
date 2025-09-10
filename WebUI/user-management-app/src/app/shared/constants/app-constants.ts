export const APP_CONSTANTS = {
  APP_NAME: 'User Management Application',
  
  // Page titles/subtitles
  PAGES: {
    LOGIN: 'Login',
    FORGOT_PASSWORD: 'Forgot Password',
    RESET_PASSWORD: 'Reset Password',
    SET_NEW_PASSWORD: 'Set New Password',
    MFA: 'Multi-Factor Authentication',
    SET_MFA: 'Setup Multi-Factor Authentication',
    PROFILE: 'Profile',
    ADMIN_DASHBOARD: 'Admin Dashboard',
    USER_FORM: 'User Management'
  },
  
  // Common messages
  MESSAGES: {
    SESSION_EXPIRED: 'Session expired. Please log in again.',
    UNAUTHORIZED: 'You are not authorized to access this resource.',
    SERVER_ERROR: 'Server error. Please try again later.',
    NETWORK_ERROR: 'Network error. Please check your connection.',
    LOADING: 'Loading...',
    SAVING: 'Saving...',
    SUCCESS: 'Operation completed successfully!'
  },
  
  // API related constants
  API: {
    TIMEOUT: 30000, // 30 seconds
    RETRY_ATTEMPTS: 3
  },
  
  // Role definitions
  ROLES: {
    ADMIN_ROLES: ['admin', 'firm_admin', 'group_admin', 'super_user']
  }
} as const;

// Export individual constants for convenience
export const { APP_NAME, PAGES, MESSAGES, API, ROLES } = APP_CONSTANTS;