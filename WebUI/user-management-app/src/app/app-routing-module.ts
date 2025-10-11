import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard';
import { UserFormComponent } from './components/user-form/user-form';
import { CreateOrganizationComponent } from './components/create-organization/create-organization';
import { CreateBusinessUnitComponent } from './components/create-business-unit/create-business-unit';
import { AuthGuard } from './guards/auth-guard';
import { MfaComponent } from './components/mfa/mfa';
import { ProfileComponent } from './components/profile/profile';
import { ResetPasswordComponent } from './components/reset-password/reset-password';
import { ForgotPasswordComponent } from './components/forgot-password/forgot-password';
import { SetNewPasswordComponent } from './components/set-new-password/set-new-password';
import { SetMfaComponent } from './components/set-mfa/set-mfa';
import { FunctionalRolesHierarchyViewComponent } from './components/functional-roles-hierarchy-view/functional-roles-hierarchy-view';
import { OAuthCallbackComponent } from './components/oauth-callback/oauth-callback.component';


export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'admin', component: AdminDashboardComponent, canActivate: [AuthGuard], data: { roles: ['admin', 'firm_admin', 'group_admin', 'super_user'] } },
  { path: 'admin/create-user', component: UserFormComponent, canActivate: [AuthGuard], data: { roles: ['admin', 'firm_admin', 'group_admin', 'super_user'] } },
  { path: 'admin/edit-user/:id', component: UserFormComponent, canActivate: [AuthGuard], data: { roles: ['admin', 'firm_admin', 'group_admin', 'super_user'] } },
  { path: 'admin/create-organization', component: CreateOrganizationComponent, canActivate: [AuthGuard], data: { roles: ['admin', 'firm_admin', 'group_admin', 'super_user'] } },
  { path: 'admin/edit-organization/:id', component: CreateOrganizationComponent, canActivate: [AuthGuard], data: { roles: ['admin', 'firm_admin', 'group_admin', 'super_user'] } },
  { path: 'admin/create-business-unit', component: CreateBusinessUnitComponent, canActivate: [AuthGuard], data: { roles: ['admin', 'firm_admin', 'group_admin', 'super_user'] } },
  { path: 'admin/edit-business-unit/:id', component: CreateBusinessUnitComponent, canActivate: [AuthGuard], data: { roles: ['admin', 'firm_admin', 'group_admin', 'super_user'] } },
  { path: 'admin/roles-hierarchy', component: FunctionalRolesHierarchyViewComponent, canActivate: [AuthGuard], data: { roles: ['admin', 'firm_admin', 'super_user'] } },
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'profile', component: ProfileComponent, canActivate: [AuthGuard] },
  { path: 'set-mfa', component: SetMfaComponent, canActivate: [AuthGuard] },
  { path: 'reset-password', component: ResetPasswordComponent, canActivate: [AuthGuard] },
  { path: 'forgot-password', component: ForgotPasswordComponent },
  { path: 'set-new-password', component: SetNewPasswordComponent },
  { path: 'mfa', component: MfaComponent },
  { path: 'oauth/callback', component: OAuthCallbackComponent },
  { path: '**', redirectTo: '/login' } // Redirect any unknown paths to login
];


@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }