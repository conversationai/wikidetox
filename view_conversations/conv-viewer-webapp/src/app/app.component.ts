import { Component, OnInit } from '@angular/core';
import { ViewChild } from '@angular/core/src/metadata/di';
import { ElementRef } from '@angular/core/src/linker/element_ref';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { Subscription } from 'rxjs/Subscription';
import * as wpconvlib from '@conversationai/wpconvlib';

const CONVERSATION_ID_TEXT = 'Conversation ID';
const REVISION_ID_TEXT = 'Revision ID';
const PAGE_ID_TEXT = 'Page ID';
const PAGE_TITLE_TEXT = 'Page Name';

const URL_PART_FOR_SEARCHBY: { [text: string]: string } = {};
URL_PART_FOR_SEARCHBY[CONVERSATION_ID_TEXT] = 'conversation-id';
URL_PART_FOR_SEARCHBY[REVISION_ID_TEXT] = 'revision-id';
URL_PART_FOR_SEARCHBY[PAGE_TITLE_TEXT] = 'page-title';
URL_PART_FOR_SEARCHBY[PAGE_ID_TEXT] = 'page-id';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  searchBys = [CONVERSATION_ID_TEXT, REVISION_ID_TEXT, PAGE_ID_TEXT, PAGE_TITLE_TEXT];
  searchBy: string;
  searchFor: string;
  inFlightRequest?: Subscription;
  rootComment?: wpconvlib.Comment;

  searchResult = '';
  errorMessage ?: string = null;

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
    console.log(`init-hash: ${document.location.hash}`);
    try {
      const hashObj = JSON.parse(document.location.hash.substr(1));
      this.searchBy = hashObj.searchBy;
      this.searchFor = hashObj.searchFor;
      console.log(`parsed-hash: ${JSON.stringify(hashObj, null, 2)}`);
    } catch (e) {
      this.searchBy = CONVERSATION_ID_TEXT;
      this.searchFor = '';
      if (document.location.hash !== '' && document.location.hash !== '#') {
        this.errorMessage = e.message;
      }
    }
  }

  updateLocationHash() {
    document.location.hash = JSON.stringify({searchBy: this.searchBy, searchFor: this.searchFor});
  }

  submitSearch() {
    this.errorMessage = null;
    console.log(this.searchBy);
    console.log(this.searchFor);
    this.updateLocationHash();

    this.inFlightRequest = this.http
      .get(encodeURI('/api/' + URL_PART_FOR_SEARCHBY[this.searchBy] + '/' + this.searchFor))
      .subscribe((actions: wpconvlib.Comment[]) => {
        console.log('got conversation!');
        this.searchResult = JSON.stringify(actions, null, 2);
        delete this.inFlightRequest;

        const conversation: wpconvlib.Conversation = {};
        for (const a of actions) {
          conversation[a.id] = a;
        }

        console.log(conversation);

        this.rootComment = wpconvlib.structureConversaton(conversation);
        if (!this.rootComment) {
          this.errorMessage = 'No Root comment in conversation';
          return;
        }

    }, (e) => {
      this.errorMessage = e.message;
      delete this.inFlightRequest;
    });
  }
}
