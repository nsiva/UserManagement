import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { UserService } from '../../services/user';
import { UserProfileService } from '../../services/user-profile.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-profile',
  imports: [FormsModule, CommonModule],
  templateUrl: './profile.html',
  styleUrls: ['./profile.scss']
})
export class ProfileComponent implements OnInit {
  user: any;

  constructor(
    private authService: AuthService,
    private userProfileService: UserProfileService,
    private router: Router
  ) {}

  ngOnInit(): void {
    (async () => {
      if (!this.authService.isLoggedIn()) {
        this.router.navigate(['/login']);
        return;
      }
      const userId = this.authService.getUserId();
      if (userId) {
        try {
          const user = await import('rxjs').then(rxjs => rxjs.firstValueFrom(this.userProfileService.getCurrentUserProfile()));
          this.user = user;
        } catch (error) {
          console.error('Error fetching user profile:', error);
          this.router.navigate(['/login']);
        }
      } else {
        console.error('No user ID found in authentication service.');
        this.router.navigate(['/login']);
      }
    })();
  }
}
