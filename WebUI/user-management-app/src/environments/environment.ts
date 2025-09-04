declare global {
  interface Window {
    __env?: {
      apiUrl?: string;
    };
  }
}

// Function to get API URL with proper timing
function getApiUrl(): string {
  if (typeof window !== 'undefined' && window.__env?.apiUrl) {
    return window.__env.apiUrl;
  }
  return 'http://localhost:8001';
}

export const environment = {
  production: false,
  get apiUrl() {
    return getApiUrl();
  }
};
