import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// import * as wpconvlib from '@conversationai/wpconvlib';

// The maximum is exclusive and the minimum is inclusive
function getRandomInt(min: number, max: number): number {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min)) + min;
}

interface WorkToDo {
  question_id: string;
  question: WikiCommentQuestion;
  answers_per_question: number;
  answer_count: number;
}

interface WikiCommentQuestion {
  revision_id: string;
  revision_text: string;
}

interface WorkerQualitySummary {
  answer_count: number;
  mean_score: number;
}

interface JobQualitySummary {
  toanswer_count: number;
  toanswer_mean_score: number;
}


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  userNonce: string | null;
  errorMessage: string | null;

  customClientJobKey: string = '';

  selectedWork: WorkToDo;
  questionId: string;
  question: WikiCommentQuestion | null;

  readableAndInEnglish: boolean;
  toxicityAnswer: string;
  obsceneAnswer: string;
  insultAnswer: string;
  threatAnswer: string;
  hateAnswer: string;
  comments: string;

  loading: boolean;

  training_answer_count: number = 0;
  user_mean_score: number = 0;

  overall_job_answer_count: number = 0;
  overall_job_mean_score: number = 0;

  // Saved into local storage and used to measure the number of sent
  // requests from the browser's prespective.
  local_sent_count: number = 0;

  constructor(private http: HttpClient) { }

  setDocumentHash() {
    if (this.customClientJobKey !== '') {
      document.location.hash = this.customClientJobKey + '/' + this.questionId;
    } else {
      document.location.hash = '';
    }
  }

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
    this.questionId = '';

    // Make the HTTP request:
    if (document.location.hash.substr(1).split('/').length === 2) {
      // If hash url specifies job id and question id, get that specific question.
      this.http.get('/api/work/' + document.location.hash.substr(1))
          .subscribe((data: WorkToDo) => {
        this.selectedWork = data;
        console.log(this.selectedWork);
        this.questionId = this.selectedWork.question_id;
        this.setDocumentHash();
        this.question = this.selectedWork.question;
      }, (e) => { this.errorMessage = e.message; });
    } else if (document.location.hash !== '') {
      // If hash url specified job, get next questions for that job
      this.http.get('/api/work/' + document.location.hash.substr(1))
          .subscribe((data: WorkToDo[]) => {
        this.selectedWork = data[getRandomInt(0, data.length - 1)];
        console.log(this.selectedWork);
        this.questionId = this.selectedWork.question_id;
        this.setDocumentHash();
        this.question = this.selectedWork.question;
      }, (e) => { this.errorMessage = e.message; });
    } else {
      // Otherwise get questions for this job.
      this.http.get('/api/work').subscribe((data: WorkToDo[]) => {
        this.selectedWork = data[getRandomInt(0, data.length - 1)];
        console.log(this.selectedWork);
        this.questionId = this.selectedWork.question_id;
        this.setDocumentHash();
        this.question = this.selectedWork.question;
      }, (e) => { this.errorMessage = e.message; });
    }

    // CONSIDER: support custom job keys.
    // Make the HTTP request:
    this.http.get('/api/job_quality').subscribe((data: JobQualitySummary) => {
      this.overall_job_answer_count = data.toanswer_count;
      this.overall_job_mean_score = data.toanswer_mean_score;
    }, (e) => { this.errorMessage = e.message; });
    // Make the HTTP request:
    this.http.get('/api/quality/' + this.userNonce).subscribe((data: WorkerQualitySummary) => {
      console.log(data);
      this.training_answer_count = data.answer_count;
      this.user_mean_score = data.mean_score;
    }, (e) => { this.errorMessage = e.message; });
  }

  clearError() {
    this.errorMessage = null;
  }

  ngOnInit(): void {
    const parts = document.location.hash.substr(1).split('/');
    this.customClientJobKey = parts[0];

    this.userNonce = localStorage.getItem('user_nonce');
    const maybe_local_sent_count = localStorage.getItem('local_sent_count');
    if (maybe_local_sent_count !== null) {
      this.local_sent_count = parseInt(maybe_local_sent_count, 10);
    } else {
      this.local_sent_count = 0;
      localStorage.setItem('local_sent_count', this.local_sent_count.toString());
    }

    if (!this.userNonce) {
      this.userNonce = Math.random().toString();
      localStorage.setItem('user_nonce', this.userNonce);
    }
    console.log(`user_nonce: ` + this.userNonce);

    this.getNextWorkItem();
  }

  public sendScoreToApi() {
    console.log('test click');

    let answerPath = '/api/answer';
    if (this.customClientJobKey !== '') {
      answerPath += '/' + this.customClientJobKey;
    }

    this.http.post(answerPath, {
      questionId: this.questionId,
      userNonce: this.userNonce,
      readableAndInEnglish: this.readableAndInEnglish ? 'Yes' : 'No',
      toxic: this.toxicityAnswer,
      obscene: this.obsceneAnswer,
      insult: this.insultAnswer,
      threat: this.threatAnswer,
      identityHate: this.hateAnswer,
      comments: this.comments
    }).subscribe((data: {}) => {
      console.log(`sent score; got response:` + JSON.stringify(data, null, 2));
      this.local_sent_count += 1;
      localStorage.setItem('local_sent_count', this.local_sent_count.toString());
      document.location.hash = this.customClientJobKey;
      this.getNextWorkItem();
    }, (e) => { this.errorMessage = e.message; });
  }
}
