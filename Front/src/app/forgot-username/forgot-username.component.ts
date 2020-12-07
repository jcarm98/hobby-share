import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { ApiService } from '../api.service';
import { Alert } from '../alert';

@Component({
  selector: 'app-forgot-username',
  templateUrl: './forgot-username.component.html',
  styleUrls: ['./forgot-username.component.css']
})
export class ForgotUsernameComponent implements OnInit {

  heading = "Forgot Username?";

  email: string;
  alert: Alert;

  constructor(private api: ApiService,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Forgot Username");
  }

  setAlert(index): void {
    if (index === 0)
      this.alert = {
        type: "success",
        message: "You will receieve an email shortly if your email address matches a HobbyShare.app account."
      };
    else {
      this.alert = undefined;
    }
  }

  forgotUsername(): void {
    if (this.email === undefined || this.email === "")
      return;

    this.api.forgotUsername(this.email).subscribe(response => {
      if (response === "True") {
        this.setAlert(0);
      }
    });
  }

}
