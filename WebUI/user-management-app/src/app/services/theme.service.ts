import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';

export enum Theme {
  LIGHT = 'light',
  DARK = 'dark',
  HIGH_CONTRAST = 'high-contrast',
  CUSTOM = 'custom' // For external CSS
}

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_KEY = 'user-theme';
  private readonly CUSTOM_THEME_URL_KEY = 'custom-theme-url';
  private currentThemeSubject: BehaviorSubject<Theme>;
  public currentTheme$: any;
  private externalStyleElement?: HTMLLinkElement;

  constructor() {
    const initialTheme = this.getInitialTheme();
    this.currentThemeSubject = new BehaviorSubject<Theme>(initialTheme);
    this.currentTheme$ = this.currentThemeSubject.asObservable();
    this.loadTheme();
  }

  private getInitialTheme(): Theme {
    // 1. First check URL parameters for external CSS
    const externalStyleUrl = this.getExternalStyleUrlFromURL();
    if (externalStyleUrl) {
      return Theme.CUSTOM;
    }
    
    // 2. Check URL parameters for theme name
    const urlTheme = this.getThemeFromURL();
    if (urlTheme) {
      return urlTheme;
    }
    
    // 3. Check if we have a saved custom theme URL
    const savedCustomUrl = localStorage.getItem(this.CUSTOM_THEME_URL_KEY);
    if (savedCustomUrl) {
      return Theme.CUSTOM;
    }
    
    // 4. Then check localStorage for standard themes
    const savedTheme = localStorage.getItem(this.THEME_KEY) as Theme;
    if (savedTheme && Object.values(Theme).includes(savedTheme)) {
      return savedTheme;
    }
    
    // 5. Default to light theme
    return Theme.LIGHT;
  }

  private getExternalStyleUrlFromURL(): string | null {
    const urlParams = new URLSearchParams(window.location.search);
    // Support multiple parameter names for flexibility
    return urlParams.get('styleUrl') || 
           urlParams.get('themeUrl') || 
           urlParams.get('cssUrl') ||
           null;
  }

  private getThemeFromURL(): Theme | null {
    // Check both 'theme' and 'userTheme' query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const themeParam = urlParams.get('theme') || urlParams.get('userTheme');
    
    if (themeParam) {
      const normalizedTheme = themeParam.toLowerCase();
      
      // Map various theme names to our Theme enum
      switch (normalizedTheme) {
        case 'dark':
        case 'theme-dark':
          return Theme.DARK;
        case 'high-contrast':
        case 'contrast':
        case 'theme-high-contrast':
          return Theme.HIGH_CONTRAST;
        case 'light':
        case 'theme-light':
          return Theme.LIGHT;
        default:
          console.warn(`Unknown theme parameter: ${themeParam}`);
          return null;
      }
    }
    
    return null;
  }

  private loadTheme(): void {
    // Check for external style URL first (highest priority)
    const externalStyleUrl = this.getExternalStyleUrlFromURL();
    
    if (externalStyleUrl) {
      this.loadExternalStylesheet(externalStyleUrl);
      return;
    }
    
    // Check for saved custom theme URL
    const savedCustomUrl = localStorage.getItem(this.CUSTOM_THEME_URL_KEY);
    if (savedCustomUrl && this.currentThemeSubject.value === Theme.CUSTOM) {
      this.loadExternalStylesheet(savedCustomUrl);
      return;
    }
    
    // Check for URL theme parameter
    const urlTheme = this.getThemeFromURL();
    if (urlTheme) {
      this.setTheme(urlTheme);
      return;
    }
    
    // Fall back to saved theme
    const savedTheme = localStorage.getItem(this.THEME_KEY) as Theme;
    if (savedTheme && Object.values(Theme).includes(savedTheme)) {
      this.setTheme(savedTheme);
    } else {
      this.setTheme(Theme.LIGHT);
    }
  }

  /**
   * Load an external CSS stylesheet from a URL
   * This allows external applications to provide their own theme CSS
   */
  loadExternalStylesheet(url: string): void {
    // Remove any existing external stylesheet
    this.removeExternalStylesheet();
    
    // Validate URL (basic security check)
    if (!this.isValidUrl(url)) {
      console.error('Invalid stylesheet URL:', url);
      this.setTheme(Theme.LIGHT); // Fall back to light theme
      return;
    }
    
    // Create and append the link element
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = url;
    link.id = 'external-theme-stylesheet';
    
    // Handle load success
    link.onload = () => {
      console.log('External stylesheet loaded successfully:', url);
      this.currentThemeSubject.next(Theme.CUSTOM);
      localStorage.setItem(this.THEME_KEY, Theme.CUSTOM);
      localStorage.setItem(this.CUSTOM_THEME_URL_KEY, url);
    };
    
    // Handle load error
    link.onerror = () => {
      console.error('Failed to load external stylesheet:', url);
      this.removeExternalStylesheet();
      this.setTheme(Theme.LIGHT); // Fall back to light theme
    };
    
    // Append to document head
    document.head.appendChild(link);
    this.externalStyleElement = link;
    
    // Also clear any theme classes since external CSS will handle styling
    document.documentElement.classList.remove('dark', 'high-contrast');
  }

  /**
   * Remove the external stylesheet if it exists
   */
  private removeExternalStylesheet(): void {
    if (this.externalStyleElement && this.externalStyleElement.parentNode) {
      this.externalStyleElement.parentNode.removeChild(this.externalStyleElement);
      this.externalStyleElement = undefined;
    }
    
    // Also remove by ID in case it was added elsewhere
    const existingLink = document.getElementById('external-theme-stylesheet');
    if (existingLink && existingLink.parentNode) {
      existingLink.parentNode.removeChild(existingLink);
    }
  }

  /**
   * Validate that the URL is well-formed
   * For production, you may want to add whitelist checking
   */
  private isValidUrl(url: string): boolean {
    try {
      const urlObj = new URL(url);
      // Only allow http and https protocols
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  }

  setTheme(theme: Theme): void {
    // If switching away from custom theme, remove external stylesheet
    if (this.currentThemeSubject.value === Theme.CUSTOM && theme !== Theme.CUSTOM) {
      this.removeExternalStylesheet();
      localStorage.removeItem(this.CUSTOM_THEME_URL_KEY);
    }
    
    this.currentThemeSubject.next(theme);
    localStorage.setItem(this.THEME_KEY, theme);
    
    // Don't apply classes if using custom external theme
    if (theme === Theme.CUSTOM) {
      return;
    }
    
    // Remove all theme classes from document root (html element for Tailwind)
    const htmlElement = document.documentElement;
    htmlElement.classList.remove('dark', 'high-contrast');
    
    // Add current theme class using Tailwind's convention
    if (theme === Theme.DARK) {
      htmlElement.classList.add('dark');
    } else if (theme === Theme.HIGH_CONTRAST) {
      htmlElement.classList.add('high-contrast');
    }
    // Light theme is default, no class needed
  }

  /**
   * Programmatically load an external stylesheet by URL
   * Can be called by components or external integrations
   */
  setCustomThemeUrl(url: string): void {
    this.loadExternalStylesheet(url);
  }

  getCurrentTheme(): Theme {
    return this.currentThemeSubject.value;
  }

  getThemeOptions(): { value: Theme; label: string }[] {
    return [
      { value: Theme.LIGHT, label: 'Light' },
      { value: Theme.DARK, label: 'Dark' },
      { value: Theme.HIGH_CONTRAST, label: 'High Contrast' }
    ];
  }
}