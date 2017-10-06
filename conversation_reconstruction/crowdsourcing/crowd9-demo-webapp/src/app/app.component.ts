import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import * as wpconvlib from '@conversationai/wpconvlib';

function getRandomInt(min: number, max: number) : number {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min)) + min; //The maximum is exclusive and the minimum is inclusive
}


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'app';

  results : string = "Loading work...";

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    // Make the HTTP request:
    this.http.get('http://localhost:8080/work').subscribe((data : wpconvlib.Conversation[]) => {

      let selected_conv : wpconvlib.Conversation = data[getRandomInt(0, data.length - 1)];
      let top_comment = wpconvlib.structureConversaton(selected_conv);

      // Read the result field from the JSON response.
      this.results = JSON.stringify(top_comment, null, 2);
    });
  }
}
