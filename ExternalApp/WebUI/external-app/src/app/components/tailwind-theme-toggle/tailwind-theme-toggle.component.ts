import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TailwindThemeService, TailwindTheme, TailwindThemeConfig } from '../../services/tailwind-theme.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-tailwind-theme-toggle',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="flex items-center gap-4">
      <!-- Simple Toggle Button -->
      <div class="relative inline-block">
        <button 
          (click)="toggleTheme()"
          [title]="getToggleTitle()"
          class="flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-300 ease-in-out
                 bg-green-light-100 hover:bg-green-light-200 dark:bg-green-dark-200 dark:hover:bg-green-dark-300
                 border border-green-light-300 dark:border-green-dark-400
                 text-green-light-800 dark:text-green-dark-800
                 hover:shadow-lg hover:scale-105 transform
                 focus:outline-none focus:ring-2 focus:ring-green-light-500 dark:focus:ring-green-dark-500"
          type="button">
          
          <!-- Theme Icon -->
          <span class="text-lg transition-transform duration-300" 
                [class.rotate-180]="currentTheme === 'dark'">
            {{ getCurrentThemeIcon() }}
          </span>
          
          <!-- Toggle Switch -->
          <div class="relative w-12 h-6 rounded-full transition-colors duration-300
                      bg-green-light-300 dark:bg-green-dark-400">
            <div class="absolute top-0.5 left-0.5 w-5 h-5 rounded-full transition-transform duration-300 shadow-md
                        bg-white dark:bg-green-dark-100
                        transform" 
                 [class.translate-x-6]="currentTheme === 'dark'">
            </div>
          </div>
          
          <!-- Theme Label -->
          <span class="text-sm font-medium hidden sm:inline">
            {{ getCurrentThemeName() }}
          </span>
        </button>
        
        <!-- Tooltip for mobile -->
        <div class="sm:hidden absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 
                    px-2 py-1 text-xs rounded bg-gray-800 text-white opacity-0 pointer-events-none
                    transition-opacity duration-300 whitespace-nowrap z-50"
             [class.opacity-100]="showTooltip">
          {{ getToggleTitle() }}
        </div>
      </div>

      <!-- Theme Selector Dropdown -->
      <div class="relative inline-block">
        <select 
          [(ngModel)]="selectedThemeUrl"
          (change)="onThemeUrlChange()"
          class="px-3 py-2 rounded-lg border transition-all duration-300
                 bg-green-light-100 hover:bg-green-light-200 dark:bg-green-dark-200 dark:hover:bg-green-dark-300
                 border-green-light-300 dark:border-green-dark-400
                 text-green-light-800 dark:text-green-dark-800
                 focus:outline-none focus:ring-2 focus:ring-green-light-500 dark:focus:ring-green-dark-500
                 cursor-pointer">
          <option value="">Select Theme</option>
          <option *ngFor="let theme of themeOptions" [value]="theme.url">
            {{ theme.name }}
          </option>
        </select>
      </div>
    </div>
  `,
  styles: [`
    /* Animation classes */
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(-10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    .animate-slide-in {
      animation: slideIn 0.3s ease-out;
    }
    
    /* Custom focus styles for better accessibility */
    button:focus-visible {
      outline: 2px solid rgb(34 197 94);
      outline-offset: 2px;
    }
  `]
})
export class TailwindThemeToggleComponent implements OnInit, OnDestroy {
  currentTheme: TailwindTheme = 'light';
  showTooltip = false;
  selectedThemeUrl = '';
  
  themeOptions = [
    { name: 'Orange', url: 'http://localhost:4202/assets/PRODUCTION_ORANGE_THEME.css' },
    { name: 'Green', url: 'http://localhost:4202/assets/PRODUCTION_GREEN_THEME.css' },
    { name: 'Blue', url: 'http://localhost:4202/assets/PRODUCTION_BLUE_THEME.css' },
    { name: 'Dark', url: 'http://localhost:4202/assets/PRODUCTION_DARK_THEME.css' },
    { name: 'Purple', url: 'http://localhost:4202/assets/PRODUCTION_PURPLE_THEME.css' }
  ];
  
  private destroy$ = new Subject<void>();

  constructor(public themeService: TailwindThemeService) {}

  ngOnInit(): void {
    // Subscribe to theme changes
    this.themeService.currentTheme$
      .pipe(takeUntil(this.destroy$))
      .subscribe(theme => {
        this.currentTheme = theme;
      });

    // Subscribe to selected theme URL changes
    this.themeService.selectedThemeUrl$
      .pipe(takeUntil(this.destroy$))
      .subscribe(url => {
        this.selectedThemeUrl = url;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  getCurrentThemeIcon(): string {
    const config = this.themeService.getThemeConfig(this.currentTheme);
    return config?.icon || '☀️';
  }

  getCurrentThemeName(): string {
    const config = this.themeService.getThemeConfig(this.currentTheme);
    return config?.displayName || 'Light';
  }

  getToggleTitle(): string {
    const nextTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    const nextConfig = this.themeService.getThemeConfig(nextTheme);
    return `Switch to ${nextConfig?.displayName || 'Theme'}`;
  }

  onMouseEnter(): void {
    this.showTooltip = true;
  }

  onMouseLeave(): void {
    this.showTooltip = false;
  }

  onThemeUrlChange(): void {
    if (this.selectedThemeUrl) {
      this.themeService.setSelectedThemeUrl(this.selectedThemeUrl);
    }
  }
}