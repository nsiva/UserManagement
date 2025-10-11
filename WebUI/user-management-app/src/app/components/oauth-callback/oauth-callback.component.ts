import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { APP_NAME } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-oauth-callback',
  imports: [CommonModule, HeaderComponent],
  templateUrl: './oauth-callback.component.html',
  styleUrls: ['./oauth-callback.component.scss']
})
export class OAuthCallbackComponent implements OnInit {
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: 'OAuth Callback',
    showUserMenu: false
  };

  message = 'Processing OAuth callback...';
  isError = false;

  constructor(
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const code = params['code'];
      const state = params['state'];
      const error = params['error'];

      if (error) {
        this.isError = true;
        this.message = `OAuth Error: ${error}`;
        console.error('OAuth error:', error);
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 3000);
        return;
      }

      if (code) {
        this.message = `Authorization successful! Code received: ${code.substring(0, 10)}...`;
        
        // Here you would typically send the code to your backend
        // For now, just display success and redirect
        setTimeout(() => {
          this.router.navigate(['/login'], { 
            queryParams: { 
              oauth_success: 'true',
              message: 'OAuth authorization completed successfully' 
            }
          });
        }, 2000);
      } else {
        this.isError = true;
        this.message = 'No authorization code received';
        
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 3000);
      }
    });
  }

  // Header event handlers (not used but required by template)
  onProfileClick(): void {}
  onAdminClick(): void {}
  onLogoutClick(): void {}
}