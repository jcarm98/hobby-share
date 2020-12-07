import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { DomSanitizer, Title } from '@angular/platform-browser';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../api.service';
import { Alert } from '../alert';

@Component({
  selector: 'app-edit-project',
  templateUrl: './edit-project.component.html',
  styleUrls: ['./edit-project.component.css']
})
export class EditProjectComponent implements OnInit {

  id: number;
  username: string;

  project404: boolean;
  name: string;
  purpose: string;
  plan: string;
  skills: string[];
  status: string;

  contributors: string[];

  isOwner: boolean;
  deleteReady: boolean;


  heading = 'Edit Project';
  alert: Alert;

  res1: File;
  res1Name: string;
  res1TooBig: boolean;

  res2: File;
  res2Name: string;
  res2TooBig: boolean;

  alerts: Alert[];

  current;

  constructor(private route: ActivatedRoute,
    private api: ApiService,
    private sanitizer: DomSanitizer,
    private title: Title,
    private location: Location,
    private router: Router) { }

  setAlert(index): void {
    if (index < 0 || index >= this.alerts.length) {
      this.alert = undefined;
    }
    else {
      this.alert = this.alerts[index];
    }
  }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      if (params.id === undefined) {
        this.project404 = true;
        this.title.setTitle("HobbyShare.app | Project Not Found");
        return;
      }
      else {
        this.id = parseInt(params.id);
        if (isNaN(this.id)) {
          this.project404 = true;
          this.title.setTitle("HobbyShare.app | Project Not Found");
          return;
        }
        else {
          this.api.getProject(this.id).subscribe(res => {
            if (res === "False") {
              this.project404 = true;
              this.title.setTitle("HobbyShare.app | Project Not Found");
              return;
            }

            let response = JSON.parse(res);
            this.current = {};

            this.name = response.name;
            this.current.name = response.name;

            this.purpose = response.purpose;
            this.current.purpose = response.purpose;

            this.plan = response.plan;
            this.current.plan = response.plan;

            this.skills = JSON.parse(response.skills);
            this.current.skills = JSON.parse(response.skills);

            this.contributors = JSON.parse(response.contributors);
            this.current.contributors = JSON.parse(response.contributors);

            this.status = response.status;
            this.current.status = response.status;

            this.isOwner = response.match === "Owner";

            this.title.setTitle("HobbyShare.app | Edit " + this.name);
          });
        }
      }
    });

    this.alerts = [{
      type: 'success',
      message: 'Success!'
    }, {
      type: 'danger',
      message: 'Not logged in. Please log in to make changes to your project.',
    }, {
      type: 'danger',
      message: 'Resource 1 file is too big, max filesize is 1 MB.',
    }, {
      type: 'danger',
      message: 'Resource 2 file is too big, max filesize is 1 MB.',
    }, {
      type: 'danger',
      message: 'You are not the owner of this project, and cannot make changes to it.',
    }, {
      type: 'success',
      message: 'Success! A contributor was removed.',
    }, {
      type: 'danger',
      message: 'User not found.',
    }];
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

  updateProject(): void {
    this.api.patchProject(this.id,
      this.name !== this.current.name ? this.name : undefined,
      this.purpose !== this.current.purpose ? this.purpose : undefined,
      this.plan !== this.current.plan ? this.plan : undefined,
      this.skills !== this.current.skills ? this.skills : undefined,
      this.status !== this.current.status ? this.status : undefined,
      this.res1,
      this.res2)
      .subscribe(res => {
        if (res === "True") {
          this.setAlert(0);
          setTimeout(() => {
            this.router.navigate(['/project/' + this.id + '/']);
          }, 1000);
          return;
        }
        if (res === "No Session") {
          this.setAlert(1);
          return;
        }
        if (res === "Res1 Too Big") {
          this.setAlert(2);
          return;
        }
        if (res === "Res2 Too Big") {
          this.setAlert(3);
          return;
        }
        if (res === "False") {
          this.setAlert(4);
          return;
        }
    });
  }

  deleteProject(): void {
    if (!(this.deleteReady)) {
      this.deleteReady = true;
      return;
    }

    this.api.deleteProject(this.id)
      .subscribe(res => {
        if (res === "True") {
          this.setAlert(0);
          setTimeout(() => {
            this.router.navigate(['/user/']);
          }, 1000);
          return;
        }
        if (res === "No Session") {
          this.setAlert(1);
          return;
        }
        if (res === "False") {
          this.setAlert(4);
          return;
        }
      });
  }

  removeContrib(): void {
    if ((this.username) && this.username !== '') {
      this.api.removeContributor(this.id, this.username).subscribe(res => {
        if (res === "True") {
          this.setAlert(5);
          return;
        }
        if (res === "No Session") {
          this.setAlert(1);
          return;
        }
        if (res === "False") {
          this.setAlert(6);
          return;
        }
      });
    }
  }

}
