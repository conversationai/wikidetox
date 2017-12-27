import { Component, OnInit, Input } from '@angular/core';
import * as wpconvlib from '@conversationai/wpconvlib';

@Component({
  selector: 'app-conversation',
  templateUrl: './conversation.component.html',
  styleUrls: ['./conversation.component.css']
})
export class ConversationComponent implements OnInit {
  @Input() rootComment: wpconvlib.Comment;
  dbg: string;

  constructor() { }

  ngOnInit() {
    this.dbg = JSON.stringify(this.rootComment, null, 2);
  }

}
