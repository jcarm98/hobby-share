import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-skills',
  templateUrl: './skills.component.html',
  styleUrls: ['./skills.component.css']
})
export class SkillsComponent implements OnInit {

  skill: string;
  @Input() skills: string[];
  @Input() readOnly: boolean;

  constructor() { }

  ngOnInit(): void {
  }

  addSkill(): void {
    if (this.skill === "" || this.skill === undefined)
      return;
    this.skills.push(this.skill);
    this.skill = "";
  }

  removeSkill(id): void {
    this.skills.splice(id, 1);
  }

}
