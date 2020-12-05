import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-project-button',
  templateUrl: './project-button.component.html',
  styleUrls: ['./project-button.component.css']
})
export class ProjectButtonComponent implements OnInit {

  @Input() projects: [];
  @Input() i: number;
  @Input() owner: boolean;

  mobileMode: boolean;

  constructor() { }

  ngOnInit(): void {
    this.mobileMode = window.innerWidth < 768;
  }

  onResize(event): void {
    this.mobileMode = event.target.innerWidth < 768;
  }

}
