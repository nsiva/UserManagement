export interface HeaderConfig {
  title: string;
  subtitle: string;
  showUserMenu?: boolean;
  userInitials?: string;
  showAdminMenuItem?: boolean;
}

export interface HeaderAction {
  type: 'profile' | 'admin' | 'logout';
  label: string;
  icon: string;
}