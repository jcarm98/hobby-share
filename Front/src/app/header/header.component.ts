import { Component, OnInit, Input } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../api.service';
import { Link } from '../link';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent implements OnInit {

  constructor(private api: ApiService,
  private router: Router) {}

  @Input() title: string;
  @Input() links: Link[];
  @Input() activeId: number;
  isCollapsed = true;

  ngOnInit(): void {
  }

  logout(): void {
    this.api.logout().subscribe(() => {
      setTimeout(() => {
        this.router.navigate(['/']);
        this.api.checkLogin();
    }, 100);
    });
  }

}
