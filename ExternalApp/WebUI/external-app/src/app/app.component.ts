import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './components/header/header.component';
import { TailwindThemeService } from './services/tailwind-theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent],
  template: `
    <app-header></app-header>
    <main>
      <router-outlet></router-outlet>
    </main>
  `,
  styles: [`
    main {
      min-height: calc(100vh - 80px);
      padding-top: 20px;
    }
  `]
})
export class AppComponent implements OnInit {
  title = 'ExternalApp - User Management Integration Demo';
  
  constructor(private themeService: TailwindThemeService) {}
  
  ngOnInit(): void {
    // Initialize theme service to ensure theme is applied correctly
    // This will read from localStorage and apply the stored theme
    console.log('App component initialized, current theme:', this.themeService.currentTheme);
  }
}