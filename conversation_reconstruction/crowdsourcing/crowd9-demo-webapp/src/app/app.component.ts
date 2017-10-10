import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// import * as wpconvlib from '@conversationai/wpconvlib';

function getRandomInt(min: number, max: number) : number {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min)) + min; //The maximum is exclusive and the minimum is inclusive
}

interface WorkToDo {
  question_id: string;
  question: string; // JSON encoded string;
  answers_per_question: number;
  answer_count: number;
}

interface WikiCommentQuestion {
  revision_id: string;
  revision_text: string;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  userNonce : string | null;

  selectedWork : WorkToDo;
  questionId : string;
  question : WikiCommentQuestion | null;

  readableAndInEnglish : boolean;
  toxicityAnswer : string;
  obsceneAnswer : string;
  insultAnswer : string;
  threatAnswer : string;
  hateAnswer : string;
  comments : string;

  loading : boolean;

  constructor(private http: HttpClient) {}

  getNextWorkItem() {
    this.loading = true;
    this.readableAndInEnglish = true;
    this.toxicityAnswer = '';
    this.obsceneAnswer = '';
    this.insultAnswer = '';
    this.threatAnswer = '';
    this.hateAnswer = '';
    this.comments = '';
    this.question = null;

    // Make the HTTP request:
    this.http.get('/api/work').subscribe((data : WorkToDo[]) => {
      this.selectedWork = data[getRandomInt(0, data.length - 1)];
      console.log(this.selectedWork);
      // let top_comment = wpconvlib.structureConversaton(selected_conv);

      this.questionId = this.selectedWork.question_id;
      this.question = JSON.parse(this.selectedWork.question);
    });
  }

  ngOnInit(): void {
    this.userNonce = localStorage.getItem('user_nonce');
    if(!this.userNonce) {
      this.userNonce = Math.random().toString();
      localStorage.setItem("user_nonce", this.userNonce);
    }
    console.log(`user_nonce: ` + this.userNonce);

    this.getNextWorkItem();
  }

  public sendScoreToApi() {
    console.log('test click');
    this.http.post('/api/answer', {
      questionId: this.questionId,
      userNonce: this.userNonce,
      readableAndInEnglish: this.readableAndInEnglish ? 'Yes' : 'No',
      toxic: this.toxicityAnswer,
      obscene: this.obsceneAnswer,
      insult: this.insultAnswer,
      threat: this.threatAnswer,
      identityHate: this.hateAnswer,
      comments: this.comments
    }).subscribe((data : {}) => {
      console.log(`send score, response:` + JSON.stringify(data, null, 2));
      this.getNextWorkItem();
    });
  }
}
