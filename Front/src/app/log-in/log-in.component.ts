import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-log-in',
  templateUrl: './log-in.component.html',
  styleUrls: ['./log-in.component.css']
})
export class LogInComponent implements OnInit {

  heading = 'Log In';
  success: boolean;
  fail: boolean;
  username: string;
  password: string;

  constructor(private api: ApiService,
    private router: Router,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Log In");
  }

  login(): void {
    if (this.username === undefined || this.username === "" ||
      this.password === undefined || this.password === "")
      return;
    this.api.login(this.username, this.password)
      .subscribe(res => {
      this.success = res === 'True';
      this.fail = res === 'False';

      if (this.success) {
        setTimeout(() => {
          this.router.navigate(['/']);
          this.api.checkLogin();
        }, 500);
      }
    });
  }

}
