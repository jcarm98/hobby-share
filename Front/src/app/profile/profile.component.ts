import { Component, OnInit } from '@angular/core';
import { DomSanitizer, Title } from '@angular/platform-browser';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.css']
})
export class ProfileComponent implements OnInit {

  constructor(private api: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private sanitizer: DomSanitizer,
    private title: Title) { }

  user404: boolean;
  owner: boolean;
  username: string;
  fname: string;
  lname: string;
  email: string;
  skills: string[];
  projects = [];
  contributing = [];
  pic: string;

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      // /user/, need to redirect
      if (params.username === undefined) {
        this.api.fetchUsername().subscribe(response => {
          // not logged in, redirect to home
          if (response === "False") {
            this.router.navigate(['/']);
            this.api.checkLogin();
          }

          // logged in, redirect to users profile
          else {
            this.router.navigate(['/user/' + response], { replaceUrl: true });
          }
        });
      }

      // /user/username/, need to fetch info and load
      else {
        this.username = params.username;
        this.api.getUser(params.username).subscribe(response => {
          // user not found, set 404 flag
          if (response === "False") {
            this.user404 = true;
            this.title.setTitle("HobbyShare.app | User Not Found");
          }
          // user found, store and display information
          else {
            this.user404 = false;
            let res = JSON.parse(response);
            this.username = res.username;
            this.fname = res.fname;
            this.lname = res.lname;
            this.email = res.email;
            this.skills = JSON.parse(res.skills);

            this.api.fetchProjects(res.projects).subscribe(projects => {
              this.projects = JSON.parse(projects);
              for (let i = 0; i < this.projects.length; i++) {
                this.projects[i] = JSON.parse(this.projects[i]);
                if (this.projects[i].res1) {
                  this.projects[i].res1 = (this.sanitizer.bypassSecurityTrustResourceUrl("data:image/png;base64, " + this.projects[i].res1) as any);
                }
              }
            });
            this.api.fetchProjects(res.contributing).subscribe(projects => {
              this.contributing = JSON.parse(projects);
              for (let i = 0; i < this.contributing.length; i++) {
                this.contributing[i] = JSON.parse(this.contributing[i]);
                if (this.contributing[i].res1) {
                  this.contributing[i].res1 = (this.sanitizer.bypassSecurityTrustResourceUrl("data:image/png;base64, " + this.contributing[i].res1) as any);
                }
              }
            });

            if (res.profilepic !== undefined) {
              this.pic = (this.sanitizer.bypassSecurityTrustResourceUrl("data:image/png;base64, " + res.profilepic) as any);
            }
            // (this.sanitizer.bypassSecurityTrustResourceUrl(item) as any).changingThisBreaksApplicationSecurity;
            // profile belongs to user, set owner flag for buttons
            this.owner = res.match === "True";

            this.title.setTitle("HobbyShare.app | " + this.username);
          }
        });
      }
    });
  }

  nav(index): void {
    this.router.navigate(['/project/' + index]);
  }

}
