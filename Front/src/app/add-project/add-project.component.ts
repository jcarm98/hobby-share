import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { ApiService } from '../api.service';
import { Alert } from '../alert'

@Component({
  selector: 'app-add-project',
  templateUrl: './add-project.component.html',
  styleUrls: ['./add-project.component.css']
})
export class AddProjectComponent implements OnInit {
  heading = 'Add Project';
  alert: Alert;

  name: string;
  purpose: string;
  plan: string;
  skills = [];

  res1: File;
  res1Name: string;
  res1TooBig: boolean;

  res2: File;
  res2Name: string;
  res2TooBig: boolean;

  alerts: Alert[];

  constructor(private api: ApiService,
    private router: Router,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Add Project");
    this.alerts = [{
      type: 'success',
      message: 'Success! Your project has been created.',
    }, {
      type: 'danger',
      message: 'Not logged in.',
    }, {
      type: 'danger',
      message: 'Resource 1 file is too big, max filesize is 1 MB.',
    }, {
      type: 'danger',
      message: 'Resource 2 file is too big, max filesize is 1 MB.',
    }];
  }

  setAlert(index, missing): void {
    // Construct missing alert
    let missingMessage = "Project is missing:\n" +
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

  onFileSelect(event, isFirst): void {
    if (event.target.files.length > 0) {
      if (isFirst) {
        const file = event.target.files[0];
        this.res1TooBig = file.size > 1048576;
        if (this.res1TooBig)
          return;
        this.res1 = file;
        this.res1Name = file.name;
      }
      else {
        const file = event.target.files[0];
        this.res2TooBig = file.size > 1048576;
        if (this.res2TooBig)
          return;
        this.res2 = file;
        this.res2Name = file.name;
      }
    }
  }

  addProject(): void {
    this.api.createProject(this.name,
      this.purpose,
      this.plan,
      this.skills,
      this.res1,
      this.res2)
      .subscribe(res => {
        if (res === "True") {
          this.setAlert(0, '');
          this.api.fetchProjectId().subscribe(response => {
            if (response === "No Session" || response === "False") {
              this.setAlert(1, '');
              return;
            }

            let id = parseInt(response);

            setTimeout(() => {
            this.router.navigate(['/project/' + id]);
            }, 1000);
          });
          return;
        }
        if (res === "No Session" || res === "False") {
          this.setAlert(1, '');
          return;
        }
        if (res === "Res1 Too Big") {
          this.setAlert(2, '');
          return;
        }
        if (res === "Res2 Too Big") {
          this.setAlert(3, '');
          return;
        }

        let missing = [];

        try {
          missing = JSON.parse(res);
          let message = "";
          for (let i = 0; i < missing.length; i++) {
            if (missing[i] === "name") {
              message += "\xa0\xa0\xa0\xa0Name\n";
            }
            else if (missing[i] === "purpose") {
              message += "\xa0\xa0\xa0\xa0Purpose\n";
            }
            else if (missing[i] === "plan") {
              message += "\xa0\xa0\xa0\xa0Plan\n";
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
