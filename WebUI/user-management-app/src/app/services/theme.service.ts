import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export enum Theme {
  LIGHT = 'light',
  DARK = 'dark',
  HIGH_CONTRAST = 'high-contrast'
}

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_KEY = 'user-theme';
  private currentThemeSubject: BehaviorSubject<Theme>;
  public currentTheme$: any;

  constructor() {
    const initialTheme = this.getInitialTheme();
    this.currentThemeSubject = new BehaviorSubject<Theme>(initialTheme);
    this.currentTheme$ = this.currentThemeSubject.asObservable();
    this.loadTheme();
  }

  private getInitialTheme(): Theme {
    const savedTheme = localStorage.getItem(this.THEME_KEY) as Theme;
    if (savedTheme && Object.values(Theme).includes(savedTheme)) {
      return savedTheme;
    }
    return Theme.LIGHT;
  }

  private loadTheme(): void {
    const savedTheme = localStorage.getItem(this.THEME_KEY) as Theme;
    if (savedTheme && Object.values(Theme).includes(savedTheme)) {
      this.setTheme(savedTheme);
    } else {
      this.setTheme(Theme.LIGHT);
    }
  }

  setTheme(theme: Theme): void {
    this.currentThemeSubject.next(theme);
    localStorage.setItem(this.THEME_KEY, theme);
    
    // Remove all theme classes
    document.body.classList.remove('theme-light', 'theme-dark', 'theme-high-contrast');
    
    // Add current theme class
    document.body.classList.add(`theme-${theme}`);
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