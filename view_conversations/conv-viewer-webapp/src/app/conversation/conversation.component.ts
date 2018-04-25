import {Component, Input, OnInit} from '@angular/core';
import * as wpconvlib from '@conversationai/wpconvlib';

@Component({
  selector: 'app-conversation',
  templateUrl: './conversation.component.html',
  styleUrls: ['./conversation.component.css']
})
export class ConversationComponent implements OnInit {
  @Input() rootComment: wpconvlib.Comment;
  isHighlighted = false;
  dbg: string;

  constructor() {}

  ngOnInit() {
    this.dbg = JSON.stringify(this.rootComment, null, 2);
    if (this.rootComment.comment_to_highlight &&
        this.rootComment.comment_to_highlight === this.rootComment.id) {
      this.isHighlighted = true;
    }
  }
}
