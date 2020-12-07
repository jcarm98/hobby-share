import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ApiService } from './api.service';
import { Link } from './link';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {

  loggedIn: boolean;

  constructor(private location: Location, private api: ApiService) {
  }

  title = 'HobbyShare.app';

  headerLinks: Link[];

  footerLinks = [
    { route: "/about", text: "About" },
    { route: "/contact", text: "Contact Us" },
  ]

  ngOnInit(): void {
    this.api.loggedIn$.subscribe(res => {
      this.loggedIn = res === "True";
      this.headerLinks = this.loggedIn ?
        [
          { route: "/", text: "Home" },
          { route: "/user", text: "Profile" },
          { route: "/log-out", text: "Log Out" },
        ]
        :
        [
          { route: "/", text: "Home" },
          { route: "/sign-up", text: "Sign Up" },
          { route: "/log-in", text: "Log In" },
        ];
    });
    this.api.checkLogin();
  }

  getActiveHeaderId(): number {
    switch (this.location.path()) {
      case "":
        return 0;
      case "/sign-up":
        return 1;
      case "/log-in":
        return 2;
      case "/user":
        //If logged in and looking at their own profile, then 1
        //Else -1
        return 1;
      default:
        return -1;
    }
  }

  getActiveFooterId(): number {
    switch (this.location.path()) {
      case "/about":
        return 0;
      case "/contact":
        return 1;
      default:
        return -1;
    }
  }

}
