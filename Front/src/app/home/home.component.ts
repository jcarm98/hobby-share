import { Component, OnInit } from '@angular/core';
import { DomSanitizer, Title } from '@angular/platform-browser';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {

  heading = "HobbyShare.app";
  projects = [];

  constructor(private api: ApiService,
    private sanitizer: DomSanitizer,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Home");
    this.api.recent().subscribe(res => {
      this.api.fetchProjects(res).subscribe(projects => {

        this.projects = JSON.parse(projects);
        for (let i = 0; i < this.projects.length; i++) {
          this.projects[i] = JSON.parse(this.projects[i]);
          if (this.projects[i].res1) {
            this.projects[i].res1 = (this.sanitizer.bypassSecurityTrustResourceUrl("data:image/png;base64, " + this.projects[i].res1) as any);
          }
        }

      });
    });
  }

}
