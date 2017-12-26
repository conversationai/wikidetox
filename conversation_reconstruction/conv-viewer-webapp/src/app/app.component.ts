import { Component, OnInit } from '@angular/core';
import { ViewChild } from '@angular/core/src/metadata/di';
import { ElementRef } from '@angular/core/src/linker/element_ref';
import { HttpClient } from '@angular/common/http';

const CONVERSATION_ID_TEXT = 'Conversation ID';
const REVISION_ID_TEXT = 'Revision ID';
const PAGE_NAME_TEXT = 'Page Name';

const URL_PART_FOR_SEARCHBY: { [text: string]: string } = {};
URL_PART_FOR_SEARCHBY[CONVERSATION_ID_TEXT] = 'conversation';
URL_PART_FOR_SEARCHBY[REVISION_ID_TEXT] = 'revision';
URL_PART_FOR_SEARCHBY[PAGE_NAME_TEXT] = 'page';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  searchBys = [CONVERSATION_ID_TEXT, REVISION_ID_TEXT, PAGE_NAME_TEXT];
  searchBy: string;
  searchFor: string;

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
      this.errorMessage = e.message;
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

    this.http
      .get('/api/' + URL_PART_FOR_SEARCHBY[this.searchBy] + '/' + this.searchFor)
      .subscribe((data: string) => {
        this.searchResult = JSON.stringify(data, null, 2);
    }, (e) => { this.errorMessage = e.message; });
  }
}
