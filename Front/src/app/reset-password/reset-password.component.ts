import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { ApiService } from '../api.service';
import { Alert } from '../alert';
import { Input } from '../input';

@Component({
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.css']
})
export class ResetPasswordComponent implements OnInit {

  heading = "Reset Password";
  alert: Alert;
  alerts: Alert[];
  inputs: Input[];

  constructor(private api: ApiService,
    private router: Router,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Reset Password");
    this.alerts = [{
      type: "success",
      message: "Your password has been reset. You will receive a verification email shortly."
    }, {
      type: "danger",
      message: "Token invalid."
    }, {
      type: "warning",
      message: "Your password has been reset. Email failed to send."
    }, {
      type: "danger",
      message: "Your new password must be a minimum of 12 characters long."
    }];

    this.inputs = [{
      label: "Token",
      id: "token",
      value: "", valid: "", error: ""
    }, {
      label: "New Password",
      id: "password",
      value: "", valid: "", error: ""
    }, {
      label: "Confirm Password",
      id: "passwordconf",
      value: "", valid: "", error: ""
    }];
  }

  setAlert(index, missing): void {
    // Construct missing alert
    let missingMessage = "Missing:\n" +
      missing +
      "Please add the missing information before trying again.";
    this.alerts.push({
      type: 'danger',
      message: missingMessage,
    });

    if (index < 0 || index >= this.alerts.length) {
      this.alert = undefined;
    }
    else {
      this.alert = this.alerts[index];
    }

    // Remove missing alert
    this.alerts.pop();
  }

  validate(index): void {
    let input = this.inputs[index];

    // Required inputs must not be empty
    if (input.value === undefined || input.value === "") {
      input.valid = "is-invalid";
      input.error = "Required field.";
      return;
    }

    // Assume input is valid at this point
    input.valid = "is-valid";
    input.error = "";

    // Set unique error messages for inputs
    switch (index) {
      case 0: break;
      case 1:
        if (input.value.length < 12) {
          input.valid = "is-invalid";
          input.error = "Sorry! Password is too short. Passwords must be a minimum of 12 characters.";
        }
        break;
      case 2:
        if (this.inputs[index].value !== this.inputs[index - 1].value) {
          input.valid = "is-invalid";
          input.error = "Sorry! Passwords must match!";
        }
        break;
      default:
    }
  }

  resetPassword(): void {
    // Validate all required inputs
    for (let i = 0; i < this.inputs.length; i++) {
      this.validate(i);
    }

    this.api.resetPassword(this.inputs[0].value, this.inputs[1].value).subscribe(response => {
      // Set alerts based on response
      if (response === 'True') {
        this.setAlert(0, "");
        setTimeout(() => {
          this.router.navigate(['/log-in/']);
        }, 3000);
        return;
      }

      if (response === 'False') {
        this.setAlert(1, "");
        return;
      }

      if (response === 'Fail') {
        this.setAlert(2, "");
        return;
      }

      if (response === 'Password Short') {
        this.setAlert(3, "");
        return;
      }

      // Construct missing inputs alert

      let missing = [];

      try {
        missing = JSON.parse(response);
        let message = "";
        for (let i = 0; i < missing.length; i++) {
          if (missing[i] === "token") {
            message += "\xa0\xa0\xa0\xa0Token\n";
          }
          else if (missing[i] === "password") {
            message += "\xa0\xa0\xa0\xa0Password\n";
          }
        }
        this.setAlert(4, message);
      }
      catch (e) {
        this.setAlert(-1, "");
        console.log("Something happened...");
      }



    });
  }

}
