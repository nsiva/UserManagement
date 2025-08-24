import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard';
import { UserFormComponent } from './components/user-form/user-form';
import { AuthGuard } from './guards/auth-guard';
import { MfaComponent } from './components/mfa/mfa';
import { ProfileComponent } from './components/profile/profile';


export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'admin', component: AdminDashboardComponent, canActivate: [AuthGuard], data: { roles: ['admin'] } },
  { path: 'admin/create-user', component: UserFormComponent, canActivate: [AuthGuard], data: { roles: ['admin'] } },
  { path: 'admin/edit-user/:id', component: UserFormComponent, canActivate: [AuthGuard], data: { roles: ['admin'] } },
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'profile', component: ProfileComponent, canActivate: [AuthGuard] },
  { path: 'mfa', component: MfaComponent },
  { path: '**', redirectTo: '/login' } // Redirect any unknown paths to login
];


@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }