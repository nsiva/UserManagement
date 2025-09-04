import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

declare global {
  interface Window {
    __env?: {
      apiUrl?: string;
    };
  }
}

@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  private config = {
    apiUrl: environment.apiUrl,
    ...window.__env // Override with runtime config if available
  };

  get apiUrl(): string {
    return this.config.apiUrl;
  }

  // Allow setting API URL at runtime
  setApiUrl(url: string): void {
    this.config.apiUrl = url;
  }
}