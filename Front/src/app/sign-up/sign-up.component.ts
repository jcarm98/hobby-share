import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { ApiService } from '../api.service';
import { Alert } from '../alert'
import { Input } from '../input'; 

@Component({
  selector: 'app-sign-up',
  templateUrl: './sign-up.component.html',
  styleUrls: ['./sign-up.component.css']
})

export class SignUpComponent implements OnInit {

  heading = 'Sign Up';
  alert: Alert;

  profilePic: File;
  fileName: string;
  fileTooBig: boolean;

  skills = [];

  alerts: Alert[];
  inputs: Input[];

  constructor(private api: ApiService,
    private router: Router,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Sign Up");
    this.alerts = [{
      type: 'success',
      message: 'Success! A verification email has been sent. Please verify your account before logging in.',
    }, {
      type: 'danger',
      message: 'Username is taken.',
    }, {
      type: 'danger',
      message: 'Email address is invalid.',
    }, {
      type: 'danger',
      message: 'Email address is already in use.',
    }, {
      type: 'danger',
      message: 'Profile picture exceeds maximum file size of 1 MB.',
    }, {
      type: 'danger',
      message: 'Password must be at least 12 characters long.',
    }];

    this.inputs = [{
      label: "First Name",
      id: "fname",
      value: "", valid: "", error: "",
    }, {
      label: "Last Name",
      id: "lname",
      value: "", valid: "", error: "",
    }, {
      label: "Username",
      id: "username",
      value: "", valid: "", error: "",
    }, {
      label: "Email Address",
      id: "email",
      value: "", valid: "", error: "",
    }, {
      label: "Password",
      id: "password",
      value: "", valid: "", error: "",
    }, {
      label: "Confirm Password",
      id: "passwordconf",
      value: "", valid: "", error: "",
    }];
  }

  escape(string): string {
    // $& means the whole matched string
    return string.replace(/[.* +?^ ${}() | [\]\\'"&<>:;\/]/g, '\\$&');
    //return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  setAlert(index, missing): void {
    // Construct missing alert
    let missingMessage = "Sign up request missing:\n" +
                         missing +
                         "Please add the missing information before trying again.";
    this.alerts.push({
      type: 'danger',
      message: missingMessage,
    });

    if (index < 0 || index >= this.alerts.length) {
      this.alert = undefined;
    }
    else{
      this.alert = this.alerts[index];
    }

    // Remove missing alert
    this.alerts.pop();
  }

  onFileSelect(event): void {
    if (event.target.files.length > 0) {
      // Set file to upload if below maximum file size
      const file = event.target.files[0];
      this.fileTooBig = file.size > 1048576;

      if (this.fileTooBig) {
        // Raise file too big error
        return;
      }

      // Set file if no errors
      this.profilePic = file;
      this.fileName = file.name;
    }
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
      case 1: break;
      case 2:
        this.api.checkUsername(input.value)
          .subscribe(response => {
            if (response === "False") {
              input.valid = "is-invalid";
              input.error = "Sorry! Username is taken.";
            }
          });
        break;
      case 4:
        if (input.value.length < 12) {
          input.valid = "is-invalid";
          input.error = "Sorry! Password is too short. Passwords must be a minimum of 12 characters.";
        }
        break;
      case 5:
        if (this.inputs[index].value !== this.inputs[index - 1].value) {
          input.valid = "is-invalid";
          input.error = "Sorry! Passwords must match!";
        }
        break;
      case 3:
        let match = input.value.match(/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/gi);
        if (match === null || this.inputs[index].value !== match[0]) {
          input.valid = "is-invalid";
          input.error = "Sorry! Email is invalid.";
        }
        else {
          this.api.checkEmail(input.value).subscribe(response => {
            if (response === "False") {
              input.valid = "is-invalid";
              input.error = "Sorry! Email is already in use.";
            }
            else if (response === "Bad Email") {
              input.valid = "is-invalid";
              input.error = "Sorry! Email is invalid.";
            }
          });
        }
        break;
      default:
    }
  }

  signUp(): void {
    // Validate all required inputs
    for (let i = 0; i < this.inputs.length; i++) {
      this.validate(i);
    }

    this.api.signup(this.inputs[0].value,
      this.inputs[1].value,
      this.inputs[2].value,
      this.inputs[4].value,
      this.inputs[3].value,
      this.skills,
      this.profilePic)
      .subscribe(res => {
        // Set alerts based on response
        if (res === 'True') {
          this.setAlert(0, "");
          setTimeout(() => {
            this.router.navigate(['/verify/user/']);
          }, 3000);
          return;
        }

        if (res === 'Duplicate Username') {
          this.setAlert(1, "");
          return;
        }

        if (res === 'Bad Email') {
          this.setAlert(2, "");
          return;
        }

        if (res === 'Duplicate Email') {
          this.setAlert(3, "");
          return;
        }

        if (res === 'File Too Big') {
          this.setAlert(4, "");
          return;
        }

        if (res === 'Password Short') {
          this.setAlert(5, "");
          return;
        }

        // Construct missing inputs alert

        let missing = [];

        try {
          missing = JSON.parse(res);
          let message = "";
          for (let i = 0; i < missing.length; i++) {
            if (missing[i] === "fname") {
              message += "\xa0\xa0\xa0\xa0First Name\n";
            }
            else if (missing[i] === "lname") {
              message += "\xa0\xa0\xa0\xa0Last Name\n";
            }
            else if (missing[i] === "username") {
              message += "\xa0\xa0\xa0\xa0Username\n";
            }
            else if (missing[i] === "password") {
              message += "\xa0\xa0\xa0\xa0Password\n";
            }
            else if (missing[i] === "email") {
              message += "\xa0\xa0\xa0\xa0Email\n";
            }
          }
          this.setAlert(6, message);
        }
        catch (e) {
          this.setAlert(-1, "");
          console.log("Something happened...");
        }

      });
  }

}
