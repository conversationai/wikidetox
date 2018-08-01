import {HttpClient, HttpResponse} from '@angular/common/http';
import {Component, OnInit} from '@angular/core';
import {ElementRef} from '@angular/core/src/linker/element_ref';
import {ViewChild} from '@angular/core/src/metadata/di';
import {FormBuilder, FormControl, FormGroup, Validators} from '@angular/forms';
import * as wpconvlib from '@conversationai/wpconvlib';
import {Subscription} from 'rxjs/Subscription';

const CONVERSATION_ID_TEXT = 'Conversation ID';
const COMMENT_ID_TEXT = 'Comment ID';
const REVISION_ID_TEXT = 'Revision ID';
const PAGE_ID_TEXT = 'Page ID';
const PAGE_TITLE_TEXT = 'Page Name';

const MOST_TOXIC_TEXT = 'Toxicity';

const URL_PART_FOR_SEARCHBY: {[text: string]: string} = {};
const URL_PART_FOR_BROWSEBY: {[text: string]: string} = {};
URL_PART_FOR_SEARCHBY[COMMENT_ID_TEXT] = 'comment-id';
URL_PART_FOR_SEARCHBY[CONVERSATION_ID_TEXT] = 'conversation-id';
URL_PART_FOR_SEARCHBY[REVISION_ID_TEXT] = 'revision-id';
URL_PART_FOR_SEARCHBY[PAGE_TITLE_TEXT] = 'page-title';
URL_PART_FOR_SEARCHBY[PAGE_ID_TEXT] = 'page-id';

URL_PART_FOR_BROWSEBY[MOST_TOXIC_TEXT] = 'toxicity';

interface HashObj {
  searchBy?: string;
  searchFor?: string;
  browseBy?: string;
  browseUpper?: string;
  browseLower?: string;
  embed: boolean;
  showPageContext: boolean;
  highlightId?: string;
}

function highlightComments(actions : wpconvlib.Comment[], highlightId: string | undefined){
  const conversation: wpconvlib.Conversation = {};
  for (const a of actions) {
    conversation[a.id] = a;
    if (highlightId) {
      if (highlightId === a.id) {
        conversation[a.id].comment_to_highlight = a.id;
      } else {
        delete conversation[a.id].comment_to_highlight;
      }
    }
  }
  return conversation;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  browseBys = [MOST_TOXIC_TEXT];
  searchBys = [
    CONVERSATION_ID_TEXT, COMMENT_ID_TEXT, REVISION_ID_TEXT, PAGE_ID_TEXT,
    PAGE_TITLE_TEXT
  ];
  inFlightRequest?: Subscription;
  inFlightBrowseRequest?: Subscription;
  rootComment?: wpconvlib.Comment;
  answerComments?: wpconvlib.Comment[];
  searchForm: FormGroup;
  browseForm: FormGroup;
  scoreLower?: number;
  scoreUpper?: number;
  scoreCategory?: string:

  embed = false;
  showPageContext = true;
  highlightId: string;

  searchResult = '';
  browseResult = '';
  errorMessage?: string = null;

  constructor(private http: HttpClient, private formBuilder: FormBuilder) {
    let searchBy = CONVERSATION_ID_TEXT;
    let searchFor = '';

    let browseBy = MOST_TOXIC_TEXT;
    let browseUpper = 1;
    let browseLower = 0;

    console.log(`init-hash: ${document.location.hash}`);
    try {
      const hashObj: HashObj = JSON.parse(document.location.hash.substr(1));
      searchBy = hashObj.searchBy;
      searchFor = hashObj.searchFor;
      this.embed = hashObj.embed === undefined ? false : hashObj.embed;
      this.showPageContext = hashObj.showPageContext === undefined ?
          true :
          hashObj.showPageContext;
      this.highlightId = hashObj.highlightId;
      console.log(`parsed-hash: ${JSON.stringify(hashObj, null, 2)}`);
    } catch (e) {
      console.log(`can't parse, starting with empty search.`);
      if (document.location.hash !== '' && document.location.hash !== '#') {
        this.errorMessage = e.message;
      }
    }

    this.searchForm = formBuilder.group({
      searchBy: new FormControl(searchBy, Validators.required),
      searchFor: new FormControl(searchFor, Validators.required),
    });
    this.browseForm = formBuilder.group({
      browseBy: new FormControl(browseBy, Validators.required),
      browseUpper: new FormControl(browseUpper, Validators.required),
      browseLower: new FormControl(browseLower, Validators.required),
    });


    if (searchFor && searchBy && this.embed) {
      this.submitSearch();
    }
    if (browseUpper && browseLower && browseBy && this.embed) {
      this.submitBrowse();
    }

  }

  ngOnInit(): void {}

  updateLocationHash() {
    console.log('updateLocationHash');
    const objToEncode: HashObj = {
      searchBy: this.searchForm.value.searchBy,
      searchFor: this.searchForm.value.searchFor,
      browseBy: this.browseForm.value.browseBy,
      browseUpper: this.browseForm.value.browseUpper,
      browseLower: this.browseForm.value.browseLower,
      embed: this.embed,
      showPageContext: this.showPageContext,
    };
    if (this.highlightId) {
      objToEncode.highlightId = this.highlightId;
    }
    document.location.hash = JSON.stringify(objToEncode);
  }

  fetchConversations(actions: wpconvlib.Comment[]) {
    this.searchResult = JSON.stringify(actions, null, 2);
    delete this.inFlightRequest;
    console.log('got conversation!');

    const conversation: wpconvlib.Conversation = highlightComments(actions, this.highlightId);
    console.log(conversation);

    this.rootComment =
        wpconvlib.structureConversaton(conversation);
    if (!this.rootComment) {
      this.errorMessage = 'No Root comment in conversation';
      return;
    }
  }


  submitCommentSearch(comment : wpconvlib.Comment) {
    console.log('model-based form submitted');
    this.errorMessage = null;
    this.updateLocationHash();

    this.inFlightRequest =
        this.http
            .get(encodeURI(
              '/api/comment-id/' + comment.id))
            .subscribe(
                (actions: wpconvlib.Comment[]) => {
                    this.searchResult = JSON.stringify(actions, null, 2);
                    delete this.inFlightRequest;
                    console.log('got conversation!');
                    const conversation: wpconvlib.Conversation = highlightComments(actions, comment.id);
                    console.log(conversation);
                    comment.rootComment =
                        wpconvlib.structureConversaton(conversation);
                    if (!comment.rootComment) {
                      this.errorMessage = 'No Root comment in conversation';
                      return;
                    }
                  },
                (e) => {
                  console.log(e);
                  if (e.error && e.error.error) {
                    this.errorMessage = e.message + '\n' + e.error.error;
                  } else {
                    this.errorMessage = e.message;
                  }
                  delete this.inFlightRequest;
                });
  }

  submitSearch() {
    console.log('model-based form submitted');
    console.log(this.searchForm.value);
    this.errorMessage = null;
    this.updateLocationHash();

    this.inFlightRequest =
        this.http
            .get(encodeURI(
                '/api/' + URL_PART_FOR_SEARCHBY[this.searchForm.value.searchBy] +
                '/' + this.searchForm.value.searchFor))
            .subscribe(
                this.fetchConversations,
                (e) => {
                  console.log(e);
                  if (e.error && e.error.error) {
                    this.errorMessage = e.message + '\n' + e.error.error;
                  } else {
                    this.errorMessage = e.message;
                  }
                  delete this.inFlightRequest;
                });
  }

  submitBrowse() {
    console.log('model-based browse form submitted');
    console.log(this.browseForm.value);
    this.browseByScore(this.browseForm.value.browseBy, this.browseForm.value.browseUpper, this.browseForm.value.browseLower);
  }

  browseByScore(browseBy : string, browseUpper: number, browseLower: number) {
    this.errorMessage = null;
    this.updateLocationHash();
    console.log(browseUpper, browseLower);

    this.inFlightBrowseRequest =
        this.http
            .get(encodeURI(
                '/api/' + URL_PART_FOR_BROWSEBY[browseBy] +
              '/' + browseUpper+ '/' + browseLower))
            .subscribe(
                (comments: wpconvlib.Comment[]) => {
                  console.log('got comments!');
                  this.browseResult = JSON.stringify(comments, null, 2);
                  delete this.inFlightBrowseRequest;
                  this.scoreLower = browseUpper;
                  this.scoreUpper = browseLower;
                  console.log(comments);
                  for (const comment of comments) {
                    comment.isCollapsed = false;
                    if (this.browseForm.value.browseBy === MOST_TOXIC_TEXT) {
                      comment.displayScore = MOST_TOXIC_TEXT + ' Score: ' + comment.RockV6_1_TOXICITY
                      const commentScore = comment.RockV6_1_TOXICITY;
                    }
                    this.scoreLower = (commentScore !== undefined && parseFloat(commentScore) < parseFloat(this.scoreLower)) ? commentScore : this.scoreLower;
                    this.scoreUpper = (commentScore !== undefined && parseFloat(commentScore) > parseFloat(this.scoreUpper)) ? commentScore : this.scoreUpper;
                  }
                  this.scoreCategory = browseBy;
                  this.answerComments = comments;
                },
                (e) => {
                  console.log(e);
                  if (e.error && e.error.error) {
                    this.errorMessage = e.message + '\n' + e.error.error;
                  } else {
                    this.errorMessage = e.message;
                  }
                  delete this.inFlightBrowseRequest;
                });
  }

}
