import { Component, Input, OnInit } from '@angular/core';
import * as wpconvlib from '@conversationai/wpconvlib';

@Component({
  selector: 'app-comment',
  templateUrl: './comment.component.html',
  styleUrls: ['./comment.component.css']
})
export class CommentComponent implements OnInit {
  @Input() comment: wpconvlib.Comment;
  dbg: string;

  constructor() { }

  ngOnInit() {
    this.dbg = JSON.stringify(this.comment, null, 2);
  }

}
