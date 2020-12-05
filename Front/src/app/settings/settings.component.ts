import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { DomSanitizer, Title } from '@angular/platform-browser';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../api.service';
import { Alert } from '../alert'
import { Input } from '../input'; 

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {

  constructor(private api: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private sanitizer: DomSanitizer,
    private title: Title,
    private location: Location) { }

  alert: Alert;

  profilePic: File;
  fileName: string;
  fileTooBig: boolean;

  hasPic: boolean;
  deleteReady: boolean;

  alerts: Alert[];
  inputs: Input[];
  skills: string[];

  current;

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Settings");
    this.alerts = [{
      type: 'success',
      message: 'Success!',
    }, {
      type: 'danger',
      message: 'Not logged in. Please log in to make changes to your account.',
    }, {
      type: 'danger',
      message: 'Password missing.',
    }, {
      type: 'danger',
      message: 'Password incorrect.',
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
      label: "New Password",
      id: "newpassword",
      value: "", valid: "", error: "",
    }, {
      label: "Confirm New Password",
      id: "newpasswordconf",
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

    this.api.getSelf().subscribe(res => {
      if (res === "No Session") {
        // set not logged in alert
        return;
      }
      else if (res === "False") {
        // set login not valid alert
        return;
      }

      let response = JSON.parse(res);

      this.current = {};

      this.inputs[0].value = response.fname;
      this.current.fname = response.fname;

      this.inputs[1].value = response.lname;
      this.current.lname = response.lname;

      this.inputs[2].value = response.username;
      this.current.username = response.username;

      this.inputs[3].value = response.email;
      this.current.email = response.email;

      this.skills = JSON.parse(response.skills);
      this.current.skills = JSON.parse(response.skills);

      this.hasPic = response.profilepic !== undefined;

    });

  }


  setAlert(index, missing): void {
    // Construct missing alert
    let missingMessage = "There were some errors, and some information may not have changed:\n" +
      missing +
      "Please fix the errors to change your account information.";
    this.alerts.push({
      type: 'warning',
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
    if ((input.value === undefined || input.value === "") && (index === 6 || index === 7)) {
      input.valid = "is-invalid";
      input.error = "Required field.";
      return;
    }

    if (input.value === "") {
      input.valid = "";
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
        if (input.valid !== "" && input.value != this.current.username) {
          this.api.checkUsername(input.value)
            .subscribe(response => {
              if (response === "False") {
                input.valid = "is-invalid";
                input.error = "Sorry! Username is taken.";
              }
            });
        }
        break;
      case 4:
        if (input.value.length < 12) {
          input.valid = "is-invalid";
          input.error = "Sorry! Password is too short. Passwords must be a minimum of 12 characters.";
        }
        break;
      case 7:
      case 5:
        if (this.inputs[index].value !== this.inputs[index - 1].value) {
          input.valid = "is-invalid";
          input.error = "Sorry! Passwords must match!";
        }
        break;
      case 3:
        if (input.valid !== "" && input.value !== this.current.email) {
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
        }
        break;
      default:
    }
  }

  confirm(): void {
    // Validate all required inputs
    for (let i = 0; i < this.inputs.length; i++) {
      this.validate(i);
    }

    this.api.patchUser(
      this.inputs[0].value !== this.current.fname ? this.inputs[0].value : undefined,
      this.inputs[1].value !== this.current.lname ? this.inputs[1].value : undefined,
      this.inputs[2].value !== this.current.username ? this.inputs[2].value : undefined,
      this.inputs[3].value !== this.current.email ? this.inputs[3].value : undefined,
      this.inputs[6].valid === "is-valid" && this.inputs[7].valid === "is-valid" ? this.inputs[6].value : undefined,
      this.inputs[4].valid === "is-valid" && this.inputs[5].valid === "is-valid" ? this.inputs[4].value : undefined,
      this.profilePic !== undefined ? this.profilePic : undefined,
      JSON.stringify(this.skills) !== JSON.stringify(this.current.skills) ? this.skills : undefined).subscribe(res => {
        // A okay
        if (res === "True") {
          this.setAlert(0, "");
          setTimeout(() => {
            this.router.navigate(['/user/']);
          }, 1000);
          return;
        }
        // Not logged in
        if (res === 'No Session') {
          this.setAlert(1, "");
          return;
        }
        // Password missing
        if (res === 'Missing') {
          this.setAlert(2, "");
          return;
        }
        // Password wrong
        if (res === 'False') {
          this.setAlert(3, "");
          return;
        }

        try {
          // Error array
          let errors = JSON.parse(res);
          let message = "";
          for (let i = 0; i < errors.length; i++) {
            if (errors[i] === "Duplicate Username") {
              message += "\xa0\xa0\xa0\xa0Username is taken\n";
            }
            if (errors[i] === "Password Short") {
              message += "\xa0\xa0\xa0\xa0New password is too short\n";
            }
            if (errors[i] === "Bad Email") {
              message += "\xa0\xa0\xa0\xa0Email is invalid\n";
            }
            if (errors[i] === "Duplicate Email") {
              message += "\xa0\xa0\xa0\xa0Email is taken\n";
            }
            if (errors[i] === "File Too Big") {
              message += "\xa0\xa0\xa0\xa0Profile picture is too big\n";
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

  delete(): void {
    if (this.deleteReady !== true) {
      this.deleteReady = true;
      return;
    }

    this.validate(6);
    this.validate(7);

    this.api.deleteUser(this.inputs[6].valid === "is-valid" && this.inputs[7].valid === "is-valid" ? this.inputs[6].value : undefined)
      .subscribe(res => {
        if (res === "True") {
          this.setAlert(0, "");
          return;
        }
        else if (res === "No Session") {
          this.setAlert(1, "");
          return;
        }
        else if (res === "Missing") {
          this.setAlert(2, "");
          return;
        }
        else if (res === "False") {
          this.setAlert(3, "");
          return;
        }

    });

  }

}
