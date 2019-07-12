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
const ALL_TEXT = 'All';
const USER_ID_TEXT = 'User ID';
const USER_NAME_TEXT = 'User Name';

const MOST_TOXIC_TEXT = 'Toxicity';

const URL_PART_FOR_SEARCHBY: {[text: string]: string} = {};
const URL_PART_FOR_BROWSEBY: {[text: string]: string} = {};
URL_PART_FOR_SEARCHBY[ALL_TEXT] = 'all';
URL_PART_FOR_SEARCHBY[COMMENT_ID_TEXT] = 'comment_id';
URL_PART_FOR_SEARCHBY[CONVERSATION_ID_TEXT] = 'conversation_id';
URL_PART_FOR_SEARCHBY[REVISION_ID_TEXT] = 'revision_id';
URL_PART_FOR_SEARCHBY[PAGE_TITLE_TEXT] = 'page_title';
URL_PART_FOR_SEARCHBY[PAGE_ID_TEXT] = 'page_id';
URL_PART_FOR_SEARCHBY[USER_ID_TEXT] = 'user_id';
URL_PART_FOR_SEARCHBY[USER_NAME_TEXT] = 'user_text';

URL_PART_FOR_BROWSEBY[MOST_TOXIC_TEXT] = 'toxicity';

interface HashObj {
  searchBy?: string;
  searchFor?: string;
  browseBy?: string;
  browseUpper?: number;
  browseLower?: number;
  embed: boolean;
  showPageContext: boolean;
  highlightId?: string;
  isHistorical?: boolean;
}

interface APIRequest {
  upper_score: number;
  lower_score: number;
  order: string;

  [key : string] : any;
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
    ALL_TEXT,
    CONVERSATION_ID_TEXT, COMMENT_ID_TEXT, REVISION_ID_TEXT, PAGE_ID_TEXT,
    PAGE_TITLE_TEXT, USER_ID_TEXT, USER_NAME_TEXT
  ];
  inFlightRequest?: Subscription;
  inFlightBrowseRequest?: Subscription;
  rootComment?: wpconvlib.Comment;
  answerComments?: wpconvlib.Comment[];
  searchForm: FormGroup;
  browseForm: FormGroup;
  scoreLower?: number;
  scoreUpper?: number;
  scoreCategory?: string;
  searchBy?: string;
  searchFor?: string | null;
  isHistorical?: boolean;

  embed = false;
  showPageContext = true;
  highlightId: string;

  searchResult = '';
  browseResult = '';
  errorMessage?: string = null;

  constructor(private http: HttpClient, private formBuilder: FormBuilder) {
    let searchBy : string | null = null;
    let searchFor : string | null = null;

    let browseBy : string | null = null;
    let browseUpper : number | null = null;
    let browseLower : number | null = null;
    let isHistorical : boolean | null = null;

    console.log(`init-hash: ${decodeURI(document.location.hash.substr(1))}`);
    try {
      const hashObj: HashObj = JSON.parse(decodeURI(document.location.hash.substr(1)));
      if (hashObj.searchBy) {
        searchBy = hashObj.searchBy;
        searchFor = hashObj.searchFor;
      }
      if (hashObj.browseBy) {
        browseBy = hashObj.browseBy;
        browseUpper = hashObj.browseUpper;
        browseLower = hashObj.browseLower;
      }
      this.embed = hashObj.embed === undefined ? false : hashObj.embed;
      this.showPageContext = hashObj.showPageContext === undefined ?
          true :
          hashObj.showPageContext;
      this.highlightId = hashObj.highlightId;
      this.isHistorical = hashObj.isHistorical;
      console.log(`parsed-hash: ${JSON.stringify(hashObj, null, 2)}`);
    } catch (e) {
      console.log(`can't parse, starting with empty search.`);
      if (document.location.hash !== '' && document.location.hash !== '#') {
        this.errorMessage = e.message;
      }
    }

    this.browseForm = formBuilder.group({
      browseBy: new FormControl(browseBy, Validators.required),
      browseUpper: new FormControl(browseUpper, Validators.required),
      browseLower: new FormControl(browseLower, Validators.required),
      searchBy: new FormControl(searchBy, Validators.required),
      searchFor: new FormControl(searchFor, ),
      isHistorical: new FormControl(isHistorical, Validators.required)
    });
    this.searchScopeChanged();
    if (searchBy && browseUpper && browseLower && browseBy &&
       this.embed && (searchFor || searchBy === 'All'))  {
      this.submitBrowse();
    }

  }

  ngOnInit(): void {}

  updateLocationHash(searchBy : string | null, searchFor: string | null, browseBy: string | null, browseUpper: number | null, browseLower: number | null , isHistorical: boolean | null) {
    console.log('updateLocationHash');
    const objToEncode: HashObj = {
      searchBy: searchBy,
      searchFor: searchFor,
      browseBy: browseBy,
      browseUpper: browseUpper,
      browseLower: browseLower,
      embed: this.embed,
      showPageContext: this.showPageContext,
      isHistorical: isHistorical,
    };
    if (this.highlightId) {
      objToEncode.highlightId = this.highlightId;
    }
    document.location.hash = JSON.stringify(objToEncode);
  }

  searchScopeChanged() {
    const searchValue = this.browseForm.get('searchFor');
    this.browseForm.get('searchBy').valueChanges.subscribe(
      (scope: string) => {
        if (scope === 'All') {
          searchValue.clearValidators();
        } else {
          searchValue.setValidators([Validators.required]);
        }
        searchValue.updateValueAndValidity();
      });
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
    if (!comment.isCollapsed) {
      return;
    }
    console.log('model-based form submitted');
    this.errorMessage = null;

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

  submitBrowse() {
    console.log('model-based browse form submitted');
    console.log(this.browseForm.value);
    this.updateLocationHash(this.browseForm.value.searchBy, this.browseForm.value.searchFor, this.browseForm.value.browseBy, this.browseForm.value.browseUppder, this.browseForm.value.browseLower, this.browseForm.value.isHistorical);
    this.browseByScore(this.browseForm.value.browseBy, this.browseForm.value.browseUpper, this.browseForm.value.browseLower, this.browseForm.value.searchBy, this.browseForm.value.searchFor, 'DESC', this.browseForm.value.isHistorical);
  }

  browseByScore(browseBy : string, browseUpper: number, browseLower: number, searchBy: string, searchFor: string, order: string, isHistorical: boolean) {
    this.errorMessage = null;
    console.log(browseUpper, browseLower, searchBy);
    let apiRequest: APIRequest = {upper_score: browseUpper, lower_score: browseLower, order: order, isAlive: !isHistorical};
    apiRequest[URL_PART_FOR_SEARCHBY[searchBy]] = searchFor

    this.inFlightBrowseRequest =
        this.http
            .get(encodeURI(
              '/api/' + URL_PART_FOR_BROWSEBY[browseBy] + '/' + JSON.stringify(apiRequest, null, 2)))
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
                    let commentScore : number | null = null;
                    if (this.browseForm.value.browseBy === MOST_TOXIC_TEXT) {
                      comment.displayScore = MOST_TOXIC_TEXT + ' Score: ' + comment.RockV6_1_TOXICITY
                      commentScore = comment.RockV6_1_TOXICITY;
                    }
                    this.scoreLower = (commentScore !== null && commentScore < this.scoreLower) ? commentScore : this.scoreLower;
                    this.scoreUpper = (commentScore !== null && commentScore > this.scoreUpper) ? commentScore : this.scoreUpper;
                  }
                  this.updateLocationHash(searchBy, searchFor, browseBy, this.scoreUpper, this.scoreLower, isHistorical);
                  if (order == 'ASC') {comments = comments.reverse();}
                  this.scoreCategory = browseBy;
                  this.searchBy = searchBy;
                  this.searchFor = searchFor;
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
