import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(private authService: AuthService, private router: Router) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {

    const requiredRoles = route.data['roles'] as Array<string>;

    if (this.authService.isLoggedIn()) {
      if (requiredRoles && requiredRoles.length > 0) {
        // Check if user has any of the required roles
        const userRoles = this.authService.getUserRoles();
        const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));

        if (hasRequiredRole) {
          return true;
        } else {
          // User is logged in but doesn't have required role
          this.router.navigate(['/login']); // Or an unauthorized page
          return false;
        }
      }
      // If no specific roles are required, just being logged in is enough
      return true;
    } else {
      // Not logged in
      this.router.navigate(['/login']);
      return false;
    }
  }
}