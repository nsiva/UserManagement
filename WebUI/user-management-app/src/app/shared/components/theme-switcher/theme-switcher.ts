import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { ThemeService, Theme } from '../../../services/theme.service';

@Component({
  selector: 'app-theme-switcher',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './theme-switcher.html',
  styleUrl: './theme-switcher.scss'
})
export class ThemeSwitcher implements OnInit, OnDestroy {
  currentTheme: Theme;
  themeOptions: { value: Theme; label: string }[] = [];
  private themeSubscription?: Subscription;

  constructor(private themeService: ThemeService) {
    this.themeOptions = this.themeService.getThemeOptions();
    this.currentTheme = this.themeService.getCurrentTheme();
  }

  ngOnInit(): void {
    this.themeSubscription = this.themeService.currentTheme$.subscribe(
      (theme: Theme) => this.currentTheme = theme
    );
  }

  ngOnDestroy(): void {
    this.themeSubscription?.unsubscribe();
  }

  onThemeChange(theme: Theme): void {
    this.themeService.setTheme(theme);
  }
}
