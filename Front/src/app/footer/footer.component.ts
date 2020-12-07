import { Component, OnInit, Input } from '@angular/core';

import { Link } from '../link';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.css']
})
export class FooterComponent implements OnInit {

  constructor() { }

  @Input() links: Link[];
  @Input() activeId: number;

  ngOnInit(): void {
  }

}
