import { Component, OnInit } from '@angular/core';
import { Hero } from './hero';
import { HEROES } from './mock-heroes';

@Component({
  selector: 'app-heroes',
  templateUrl: './heroes.component.html',
  styleUrls: ['./heroes.component.less']
})
export class HeroesComponent implements OnInit {

  heroes:Hero[]=[{
    id:1,
    name: 'Ruksad siddiqui'
  }];
  selectedHero?:Hero;
  constructor() { }

  ngOnInit(): void {
   this.heroes=HEROES;
  }

  onSelectOfHero(hero:Hero):void{
    this.selectedHero=hero
    console.log("selected hero",hero);
    
  }
}
