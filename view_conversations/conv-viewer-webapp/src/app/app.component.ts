import { Component, OnInit } from '@angular/core';
import { ViewChild } from '@angular/core/src/metadata/di';
import { ElementRef } from '@angular/core/src/linker/element_ref';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { Subscription } from 'rxjs/Subscription';
import * as wpconvlib from '@conversationai/wpconvlib';
import { FormGroup, FormControl, Validators, FormBuilder } from '@angular/forms';

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
  inFlightRequest?: Subscription;
  rootComment?: wpconvlib.Comment;
  form: FormGroup;

  searchResult = '';
  errorMessage ?: string = null;

  constructor(private http: HttpClient, private formBuilder: FormBuilder) {
    let searchBy = CONVERSATION_ID_TEXT;
    let searchFor = '';
    console.log(`init-hash: ${document.location.hash}`);
    try {
      const hashObj = JSON.parse(document.location.hash.substr(1));
      searchBy = hashObj.searchBy;
      searchFor = hashObj.searchFor;
      console.log(`parsed-hash: ${JSON.stringify(hashObj, null, 2)}`);
    } catch (e) {
      console.log(`can't parse, starting with empty search.`);
      if (document.location.hash !== '' && document.location.hash !== '#') {
        this.errorMessage = e.message;
      }
    }

    this.form = formBuilder.group({
      searchBy: new FormControl(searchBy, Validators.required),
      searchFor: new FormControl(searchFor, Validators.required),
    });
  }

  ngOnInit(): void {
  }

  updateLocationHash() {
    document.location.hash = JSON.stringify(
      {searchBy: this.form.value.searchBy, searchFor: this.form.value.searchFor});
  }

  submitSearch() {
    console.log('model-based form submitted');
    console.log(this.form.value);
    this.errorMessage = null;
    this.updateLocationHash();

    this.inFlightRequest = this.http
      .get(encodeURI('/api/' + URL_PART_FOR_SEARCHBY[this.form.value.searchBy] +
                     '/' + this.form.value.searchFor))
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
      console.log(e);
      if (e.error && e.error.error) {
        this.errorMessage = e.message + '\n' + e.error.error;
      } else {
        this.errorMessage = e.message;
      }
      delete this.inFlightRequest;
    });
  }
}
