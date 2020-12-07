import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { ApiService } from '../api.service';
import { Alert } from '../alert';

@Component({
  selector: 'app-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.css']
})
export class ForgotPasswordComponent implements OnInit {

  heading = "Forgot Password?";

  username: string;
  alert: Alert;

  constructor(private api: ApiService,
    private router: Router,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Forgot Password");
  }

  setAlert(index): void {
    if (index === 0)
      this.alert = {
        type: "success",
        message: "You will receieve an email shortly if your username matches a HobbyShare.app account."
      };
    else {
      this.alert = undefined;
    }
  }

  forgotPassword(): void {
    if (this.username === undefined || this.username === "")
      return;

    this.api.forgotPassword(this.username).subscribe(response => {
      if (response === "True") {
        this.setAlert(0);
        setTimeout(() => {
          this.router.navigate(['/reset/password/']);
        }, 3000);
        return
      }
    });
  }

}
