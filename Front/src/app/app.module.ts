import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { HttpClientXsrfModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms'; 

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { HeaderComponent } from './header/header.component';
import { FooterComponent } from './footer/footer.component';
import { HomeComponent } from './home/home.component';
import { ProfileComponent } from './profile/profile.component';
import { AboutComponent } from './about/about.component';
import { ContactComponent } from './contact/contact.component';
import { SignUpComponent } from './sign-up/sign-up.component';
import { LogInComponent } from './log-in/log-in.component';
import { SettingsComponent } from './settings/settings.component';
import { EditProjectComponent } from './edit-project/edit-project.component';
import { ProjectComponent } from './project/project.component';
import { SkillsComponent } from './skills/skills.component';
import { VerifyUserComponent } from './verify-user/verify-user.component';
import { ResetPasswordComponent } from './reset-password/reset-password.component';
import { ForgotUsernameComponent } from './forgot-username/forgot-username.component';
import { ForgotPasswordComponent } from './forgot-password/forgot-password.component';
import { AddProjectComponent } from './add-project/add-project.component';
import { ProjectButtonComponent } from './project-button/project-button.component';

@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    FooterComponent,
    HomeComponent,
    ProfileComponent,
    AboutComponent,
    ContactComponent,
    SignUpComponent,
    LogInComponent,
    SettingsComponent,
    EditProjectComponent,
    ProjectComponent,
    SkillsComponent,
    VerifyUserComponent,
    ResetPasswordComponent,
    ForgotUsernameComponent,
    ForgotPasswordComponent,
    AddProjectComponent,
    ProjectButtonComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    NgbModule,
    FormsModule,
    HttpClientModule,
    HttpClientXsrfModule.withOptions({
      cookieName: 'csrftoken',
      headerName: 'X-CSRFToken',
    })
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
