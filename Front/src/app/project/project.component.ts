import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { DomSanitizer, Title } from '@angular/platform-browser';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { Alert } from '../alert';

@Component({
  selector: 'app-project',
  templateUrl: './project.component.html',
  styleUrls: ['./project.component.css']
})
export class ProjectComponent implements OnInit {

  id: number;
  username: string;
  alert: Alert;
  alerts: Alert[];

  project404: boolean;
  name: string;
  purpose: string;
  plan: string;
  skills: string[];
  status: string;

  date_created: string;
  last_updated: string;

  owner: string;
  contributors: string[];

  res1: string;
  res2: string;

  isOwner: boolean;
  isContributor: boolean;

  constructor(private route: ActivatedRoute,
    private api: ApiService,
    private sanitizer: DomSanitizer,
    private title: Title,
    private location: Location) { }

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
            this.name = response.name;
            this.purpose = response.purpose;
            this.plan = response.plan;
            this.skills = JSON.parse(response.skills);
            this.owner = response.owner;
            this.contributors = JSON.parse(response.contributors);

            this.date_created = response.date_created;
            this.last_updated = response.last_updated;
            this.status = response.status;
            if (response.res1 !== undefined) {
              this.res1 = (this.sanitizer.bypassSecurityTrustResourceUrl("data:image/png;base64, " + response.res1) as any);
            }
            if (response.res2 !== undefined) {
              this.res2 = (this.sanitizer.bypassSecurityTrustResourceUrl("data:image/png;base64, " + response.res2) as any);
            }

            this.isOwner = response.match === "Owner";
            this.isContributor = response.match === "Contributor";

            this.title.setTitle("HobbyShare.app | " + this.name);
          });
        }
      }
    });

    this.alerts = [{
      type: 'success',
      message: 'An invitation has been sent.',
    }, {
      type: 'danger',
      message: 'Not logged in.',
    }, {
      type: 'danger',
      message: 'User not found.',
    }, {
      type: 'success',
      message: 'A request to join has been sent.',
    }, {
      type: 'danger',
      message: 'Unknown error.',
    }];
  }

  setAlert(index): void {
    if (index < 0 || index > this.alerts.length) {
      this.alert = undefined;
    }
    else {
      this.alert = this.alerts[index];
    }
  }

  invite(): void {
    this.api.invite(this.username, this.id)
      .subscribe(res => {
      if (res === "True") {
        this.setAlert(0);
        return;
      }
      if (res === "False") {
        this.setAlert(2);
        return;
      }
      if (res === "No Session") {
        this.setAlert(1);
        return;
      }
    });
  }

  join(): void {
    this.api.join(this.id)
      .subscribe(res => {
        if (res === "True") {
          this.setAlert(3);
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

  leave(): void {
    this.api.leave(this.id)
      .subscribe(res => {
        if (res === "True") {
          window.location.href = window.location.href;
        }
    });
  }
}
