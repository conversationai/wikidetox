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
const USER_ID_TEXT = 'User ID';
const USER_NAME_TEXT = 'User Name';

const ATTRIBUTE_TOXICITY = 'Toxicity';

const URL_PART_FOR_SEARCHBY: {[text: string]: string} = {};
const URL_PART_FOR_SORT_BY_ATTR: {[text: string]: string} = {};
URL_PART_FOR_SEARCHBY[COMMENT_ID_TEXT] = 'comment_id';
URL_PART_FOR_SEARCHBY[CONVERSATION_ID_TEXT] = 'conversation_id';
URL_PART_FOR_SEARCHBY[REVISION_ID_TEXT] = 'revision_id';
URL_PART_FOR_SEARCHBY[PAGE_TITLE_TEXT] = 'page_title';
URL_PART_FOR_SEARCHBY[PAGE_ID_TEXT] = 'page_id';
URL_PART_FOR_SEARCHBY[USER_ID_TEXT] = 'user_id';
URL_PART_FOR_SEARCHBY[USER_NAME_TEXT] = 'user_text';

URL_PART_FOR_SORT_BY_ATTR[ATTRIBUTE_TOXICITY] = 'toxicity';

interface FormObj {
  searchBy?: string;
  searchFor?: string;
  highlightId?: string;
  sortByAttr?: string;
  maxScore?: number;
  minScore?: number;
  showTitleContext?: boolean;
  showParentContext: boolean;
  order: 'ASC' | 'DESC';
  embed: boolean;
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
  browseBys = [ATTRIBUTE_TOXICITY];
  searchBys = [
    CONVERSATION_ID_TEXT, COMMENT_ID_TEXT, REVISION_ID_TEXT, PAGE_ID_TEXT,
    PAGE_TITLE_TEXT, USER_ID_TEXT, USER_NAME_TEXT
  ];

  inFlightRequest?: Subscription;
  inFlightBrowseRequest?: Subscription;
  rootComment?: wpconvlib.Comment;
  answerComments?: wpconvlib.Comment[];

  // Form values.
  searchForm: FormGroup;

  sortByAttr = new FormControl('', Validators.required);
  minScore = new FormControl(0, Validators.required);
  maxScore = new FormControl(1, Validators.required);
  sortOrder = new FormControl('DESC', Validators.required);
  searchBy = new FormControl(URL_PART_FOR_SEARCHBY[COMMENT_ID_TEXT], Validators.required);
  searchFor = new FormControl('');
  isHistorical = new FormControl(false, Validators.required);
  showTitleContext = new FormControl(true, Validators.required);
  showParentContext = new FormControl(true, Validators.required);
  embed = new FormControl(false, Validators.required);

  // Id of an individual comment to highlight.
  highlightId = new FormControl('');

  rawResultJson = '';
  errorMessage?: string = null;

  constructor(private http: HttpClient, private formBuilder: FormBuilder) {

    this.searchForm = formBuilder.group({
      searchBy: this.searchBy,
      searchFor: this.searchFor,
      sortOrder: this.sortOrder,
      sortByAttr: this.sortByAttr,
      maxScore: this.maxScore,
      minScore: this.minScore,
      isHistorical: this.isHistorical,
      highlightId: this.highlightId,
      showTitleContext: this.showTitleContext,
      showParentContext: this.showParentContext,
      embed: this.embed,
    });

    console.log(`init-hash: ${decodeURI(document.location.hash.substr(1))}`);
    try {
      const hashObj: FormObj = JSON.parse(decodeURI(document.location.hash.substr(1)));
      this.updateFormValues(hashObj);
      this.submitBrowse();
    } catch (e) {
      console.log(`can't parse, starting with empty search.`);
      if (document.location.hash !== '' && document.location.hash !== '#') {
        this.errorMessage = e.message;
      }
    }
  }

  ngOnInit(): void {}

  updateFormValues(obj: FormObj) {
    if (obj.searchBy) {
      this.searchBy.setValue(obj.searchBy);
      this.searchFor.setValue(obj.searchFor);
    }
    this.sortOrder.setValue(obj.order);
    if (obj.sortByAttr) {
      this.sortByAttr.setValue(obj.sortByAttr);
      this.maxScore.setValue(obj.maxScore);
      this.minScore.setValue(obj.minScore);
    }
    this.isHistorical.setValue(obj.isHistorical);
    this.highlightId.setValue(obj.highlightId);
    this.showTitleContext.setValue(obj.showTitleContext);
    this.showParentContext.setValue(obj.showParentContext);
    this.embed.setValue(obj.embed);
    console.log(`parsed-hash: ${JSON.stringify(obj, null, 2)}`);
  }

  updateLocationHash() {
    console.log('updateLocationHash');
    const objToEncode: FormObj = {
      searchBy: this.searchBy.value,
      searchFor: this.searchFor.value,
      sortByAttr: this.sortByAttr.value,
      maxScore: this.maxScore.value,
      minScore: this.minScore.value,
      embed: this.embed.value,
      order: this.sortOrder.value,
      showTitleContext: this.showTitleContext.value,
      showParentContext: this.showParentContext.value,
      isHistorical: this.isHistorical.value,
    };
    if (this.highlightId) {
      objToEncode.highlightId = this.highlightId.value;
    }
    document.location.hash = JSON.stringify(objToEncode);
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
                    this.rawResultJson = JSON.stringify(actions, null, 2);
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
    console.log(this.searchForm.value);
    this.updateLocationHash();
    this.browseByScore();
  }

  browseByScore() {
    this.errorMessage = null;
    const apiRequest: APIRequest = {
      upper_score: this.maxScore.value,
      lower_score: this.minScore.value,
      order: this.sortOrder.value,
      isAlive: !this.isHistorical.value
    };

    apiRequest[URL_PART_FOR_SEARCHBY[this.searchBy.value]] = this.searchFor.value;

    this.inFlightBrowseRequest =
        this.http
            .get(encodeURI(
              '/api/' + URL_PART_FOR_SORT_BY_ATTR[this.searchBy.value] + '/' + JSON.stringify(apiRequest, null, 2)))
            .subscribe(
                (comments: wpconvlib.Comment[]) => {
                  console.log('got comments!');
                  this.rawResultJson = JSON.stringify(comments, null, 2);
                  delete this.inFlightBrowseRequest;
                  console.log(comments);
                  for (const comment of comments) {
                    comment.isCollapsed = false;
                    let commentScore : number | null = null;
                    if (this.searchForm.value.browseBy === ATTRIBUTE_TOXICITY) {
                      comment.displayScore = ATTRIBUTE_TOXICITY + ' Score: ' + comment.RockV6_1_TOXICITY;
                      commentScore = comment.RockV6_1_TOXICITY;
                    }
                  }
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

  // Fetch the so-far conversation given a comment ID.
  browseByComment(searchFor: string) {
    this.errorMessage = null;
    console.log('Browsing by comment-id: ' + searchFor);
    this.inFlightBrowseRequest =
        this.http
            .get(encodeURI(
              '/api/comment-id/' + searchFor))
            .subscribe(
                (comments: wpconvlib.Comment[]) => {
                  console.log('got comments!');
                  this.rawResultJson = JSON.stringify(comments, null, 2);
                  delete this.inFlightBrowseRequest;
                  console.log(comments);
                  this.answerComments = comments.filter(i => i.id === searchFor);
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
