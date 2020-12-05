import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { Title } from '@angular/platform-browser';
import { Alert } from '../alert';
import { Input } from '../input';

@Component({
  selector: 'app-contact',
  templateUrl: './contact.component.html',
  styleUrls: ['./contact.component.css']
})
export class ContactComponent implements OnInit {

  alert: Alert;
  heading = "Contact Us";
  subject: string;
  email: string;
  message: string;

  alerts: Alert[];
  inputs: Input[];

  constructor(private api: ApiService,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Contact Us");
    this.alerts = [{
      type: "success",
      message: "Email successfully sent.",
    }, {
      type: "danger",
      message: "Email failed to send, sorry.",
    }, {
      type: "danger",
      message: "Email address is invalid.",
    },];

    this.inputs = [{
      label: "Subject",
      id: "subject",
      value: "", valid: "", error: "",
    }, {
      label: "Email Address",
      id: "email",
      value: "", valid: "", error: "",
    }, {
      label: "Message",
      id: "message",
      value: "", valid: "", error: "",
    },];
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
        let match = input.value.match(/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/gi);
        if (match === null || this.inputs[index].value !== match[0]) {
          input.valid = "is-invalid";
          input.error = "Sorry! Email is invalid.";
        }
        break;
      case 2: break;
      default:
    }

  }

  contact(): void {
    // Validate all required inputs
    for (let i = 0; i < this.inputs.length; i++) {
      this.validate(i);
    }

    this.api.contact(this.inputs[0].value, this.inputs[1].value, this.inputs[2].value)
      .subscribe(response => {
        // Set alerts based on response
        if (response === "True") {
          this.setAlert(0, "");
          for (let i = 0; i < this.inputs.length; i++) {
            this.inputs[i].value = "";
            this.inputs[i].valid = "";
          }
          return;
        }
        if (response === "False") {
          this.setAlert(1, "");
          return;
        }
        if (response === "Bad Email") {
          this.setAlert(2, "");
          return;
        }

        // Construct missing inputs alert

        let missing = [];

        try {
          missing = JSON.parse(response);
          let message = "";
          for (let i = 0; i < missing.length; i++) {
            if (missing[i] === "subject") {
              message += "\xa0\xa0\xa0\xa0Subject\n";
            }
            else if (missing[i] === "from") {
              message += "\xa0\xa0\xa0\xa0Email Address\n";
            }
            else if (missing[i] === "message") {
              message += "\xa0\xa0\xa0\xa0Message\n";
            }
          }
          this.setAlert(3, message);
        }
        catch (e) {
          this.setAlert(-1, "");
          console.log("Something happened...");
        }

      });
  }

}
