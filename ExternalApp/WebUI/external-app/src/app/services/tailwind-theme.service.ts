import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type TailwindTheme = 'light' | 'dark';

export interface TailwindThemeConfig {
  name: TailwindTheme;
  displayName: string;
  icon: string;
  description: string;
  bodyClass: string;
}

@Injectable({
  providedIn: 'root'
})
export class TailwindThemeService {
  private readonly THEME_KEY = 'external-app-tailwind-theme';
  private readonly DEFAULT_THEME: TailwindTheme = 'light';
  
  private themeSubject = new BehaviorSubject<TailwindTheme>(this.getStoredTheme());
  
  // Available theme configurations
  public readonly themes: TailwindThemeConfig[] = [
    {
      name: 'light',
      displayName: 'Light Theme',
      icon: '☀️',
      description: 'Light green theme with bright backgrounds',
      bodyClass: ''
    },
    {
      name: 'dark',
      displayName: 'Dark Theme',
      icon: '🌙',
      description: 'Dark green theme with rich dark backgrounds',
      bodyClass: 'dark'
    }
  ];

  constructor() {
    // Apply the stored theme on service initialization
    this.applyTheme(this.themeSubject.value);
    
    // Listen to system theme changes
    this.listenToSystemThemeChanges();
  }

  /**
   * Get the current theme as an Observable
   */
  get currentTheme$(): Observable<TailwindTheme> {
    return this.themeSubject.asObservable();
  }

  /**
   * Get the current theme value
   */
  get currentTheme(): TailwindTheme {
    return this.themeSubject.value;
  }

  /**
   * Get theme configuration by name
   */
  getThemeConfig(theme: TailwindTheme): TailwindThemeConfig | undefined {
    return this.themes.find(t => t.name === theme);
  }

  /**
   * Set the current theme
   */
  setTheme(theme: TailwindTheme): void {
    if (this.themeSubject.value !== theme) {
      this.themeSubject.next(theme);
      this.applyTheme(theme);
      this.storeTheme(theme);
      console.log(`Tailwind theme changed to: ${theme}`);
    }
  }

  /**
   * Toggle between light and dark themes
   */
  toggleTheme(): void {
    const currentTheme = this.themeSubject.value;
    const newTheme: TailwindTheme = currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }

  /**
   * Check if the current theme is dark
   */
  isDarkTheme(): boolean {
    return this.themeSubject.value === 'dark';
  }

  /**
   * Check if the current theme is light
   */
  isLightTheme(): boolean {
    return this.themeSubject.value === 'light';
  }

  /**
   * Get the stored theme from localStorage
   */
  private getStoredTheme(): TailwindTheme {
    try {
      const stored = localStorage.getItem(this.THEME_KEY);
      if (stored && this.isValidTheme(stored)) {
        return stored as TailwindTheme;
      }
    } catch (error) {
      console.warn('Error reading theme from localStorage:', error);
    }
    
    // Fall back to system preference or default
    return this.getSystemTheme();
  }

  /**
   * Store the theme in localStorage
   */
  private storeTheme(theme: TailwindTheme): void {
    try {
      localStorage.setItem(this.THEME_KEY, theme);
    } catch (error) {
      console.warn('Error storing theme to localStorage:', error);
    }
  }

  /**
   * Apply the theme by setting the appropriate class on document element
   */
  private applyTheme(theme: TailwindTheme): void {
    const themeConfig = this.getThemeConfig(theme);
    
    if (!themeConfig) {
      console.warn(`Unknown theme: ${theme}`);
      return;
    }

    // Remove all theme classes
    document.documentElement.classList.remove('dark');
    document.body.classList.remove('dark');
    
    // Add the new theme class if it's dark mode
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.body.classList.add('dark');
    }
    
    // Update meta theme-color for mobile browsers
    this.updateMetaThemeColor(theme);
    
    // Dispatch custom event for other parts of the app
    this.dispatchThemeChangeEvent(theme);
  }

  /**
   * Update meta theme-color for mobile browsers
   */
  private updateMetaThemeColor(theme: TailwindTheme): void {
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    const color = theme === 'dark' ? '#064e3b' : '#f0fdf4';
    
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', color);
    } else {
      // Create meta tag if it doesn't exist
      const meta = document.createElement('meta');
      meta.name = 'theme-color';
      meta.content = color;
      document.head.appendChild(meta);
    }
  }

  /**
   * Dispatch a custom theme change event
   */
  private dispatchThemeChangeEvent(theme: TailwindTheme): void {
    const event = new CustomEvent('tailwindThemeChanged', { 
      detail: { theme, config: this.getThemeConfig(theme) }
    });
    window.dispatchEvent(event);
  }

  /**
   * Get system theme preference
   */
  private getSystemTheme(): TailwindTheme {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      return prefersDark ? 'dark' : 'light';
    }
    return this.DEFAULT_THEME;
  }

  /**
   * Listen to system theme changes
   */
  private listenToSystemThemeChanges(): void {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      // Only auto-switch if user hasn't manually set a preference
      const hasStoredPreference = localStorage.getItem(this.THEME_KEY);
      
      if (!hasStoredPreference) {
        mediaQuery.addEventListener('change', (e) => {
          const systemTheme: TailwindTheme = e.matches ? 'dark' : 'light';
          this.setTheme(systemTheme);
        });
      }
    }
  }

  /**
   * Check if a theme name is valid
   */
  private isValidTheme(theme: string): boolean {
    return this.themes.some(t => t.name === theme);
  }

  /**
   * Reset theme to system preference
   */
  resetToSystemTheme(): void {
    localStorage.removeItem(this.THEME_KEY);
    const systemTheme = this.getSystemTheme();
    this.setTheme(systemTheme);
  }

  /**
   * Check if user prefers reduced motion
   */
  prefersReducedMotion(): boolean {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  }

  /**
   * Get theme statistics for analytics
   */
  getThemeStats(): { 
    currentTheme: TailwindTheme; 
    isSystemTheme: boolean; 
    prefersReducedMotion: boolean;
    appliedClasses: string[];
  } {
    const storedTheme = localStorage.getItem(this.THEME_KEY);
    const systemTheme = this.getSystemTheme();
    
    return {
      currentTheme: this.currentTheme,
      isSystemTheme: !storedTheme || this.currentTheme === systemTheme,
      prefersReducedMotion: this.prefersReducedMotion(),
      appliedClasses: Array.from(document.documentElement.classList)
    };
  }
}