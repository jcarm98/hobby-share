import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { SignUpComponent } from './sign-up/sign-up.component';
import { VerifyUserComponent } from './verify-user/verify-user.component';
import { LogInComponent } from './log-in/log-in.component';
import { ProfileComponent } from './profile/profile.component';
import { AboutComponent } from './about/about.component';
import { ContactComponent } from './contact/contact.component';
import { ForgotUsernameComponent } from './forgot-username/forgot-username.component';
import { ForgotPasswordComponent } from './forgot-password/forgot-password.component';
import { ResetPasswordComponent } from './reset-password/reset-password.component';
import { SettingsComponent } from './settings/settings.component';
import { AddProjectComponent } from './add-project/add-project.component';
import { ProjectComponent } from './project/project.component';
import { EditProjectComponent } from './edit-project/edit-project.component';

import { HomeComponent } from './home/home.component';

const routes: Routes = [
  { path: '', pathMatch: 'full', component: HomeComponent },
  //{ path: '', redirectTo: '/', pathMatch: 'full' },
  { path: 'sign-up', component: SignUpComponent },
  { path: 'verify/user', component: VerifyUserComponent },
  { path: 'log-in', component: LogInComponent },
  { path: 'about', component: AboutComponent },
  { path: 'contact', component: ContactComponent },
  { path: 'forgot/username', component: ForgotUsernameComponent },
  { path: 'forgot/password', component: ForgotPasswordComponent },
  { path: 'reset/password', component: ResetPasswordComponent },
  { path: 'settings', component: SettingsComponent },
  { path: 'project/add', component: AddProjectComponent },
  { path: 'project/:id', component: ProjectComponent },
  { path: 'project/:id/edit', component: EditProjectComponent },
  { path: 'user', component: ProfileComponent },
  { path: 'user/:username', component: ProfileComponent },
  { path: '**', redirectTo: '/'},
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
