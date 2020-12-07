import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-verify-user',
  templateUrl: './verify-user.component.html',
  styleUrls: ['./verify-user.component.css']
})
export class VerifyUserComponent implements OnInit {

  heading = 'Verify Your Account';
  success: boolean;
  fail: boolean;
  token: string;

  constructor(private api: ApiService,
    private router: Router,
    private title: Title) { }

  ngOnInit(): void {
    this.title.setTitle("HobbyShare.app | Verify User");
  }

  verify(): void {
    if (this.token === undefined || this.token === "")
      return;
    this.api.verify(this.token)
    .subscribe(res => {
      this.success = res === 'True';
      this.fail = res === 'False';

      if (this.success) {
        setTimeout(() => {
          this.router.navigate(['/log-in/']);
        }, 3000);
      }
    });
  }

}
