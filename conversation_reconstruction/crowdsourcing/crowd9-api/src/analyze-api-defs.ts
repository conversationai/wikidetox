/*
Copyright 2017 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
export interface AnalyzeCommentRequest {
  comment: TextEntry;
  context?: Context;
  languages?: string[];
  requested_attributes: RequestedAttributes;
  do_not_log?: boolean;
  client_token?: string;
  session_id?: string;
}

export interface RequestedAttributes {
  // TODO(jetpack): add AttributeParameters at some point.
  [key: string]: any;
}

export interface AnalyzeCommentResponse {
  attributeScores?: AttributeScores;
  languages?: string[];
  clientToken?: string;
}

export interface SuggestCommentScoreRequest {
  comment: TextEntry;
  context?: Context;
  languages?: string[];
  attribute_scores?: AttributeScores;
  community_id?: string;
  user_id?: string;
  client_token?: string;
}

// Holds data needed for building an |AnalyzeCommentRequest|.
export interface AnalyzeCommentData {
  comment: string;
  sessionId: string;
}

// Holds data needed for building a |SuggestCommentScoreRequest|.
export interface SuggestCommentScoreData {
  comment: string;
  sessionId: string;
  commentMarkedAsToxic: boolean;
}

export interface AttributeScores {
 [key: string]: SpanScores;
}

export interface SuggestCommentScoreResponse {
  client_token?: string;
}

export interface TextEntry {
  text: string;
  type?: string;
}

export interface Context {
  entries: TextEntry[];
}

export interface SpanScores {
  spanScores?: SpanScore[];
  summaryScore?: Score;
}

export interface SpanScore {
  begin?: number;
  end?: number;
  score: Score;
}

export interface Score {
  value: number;
  type?: string;
}

// Two client interfaces exist below:
//   1. The Gapi interface which allows clients to make requests directly from
//      javascript to the Comment Analyzer API.
//   2. The Node interface which is used by a Node server to proxy calls from
//      the client to the Comment Analyzer API.
//
// The Gapi and Node client interfaces are separated below for clarity and type
// safety, since each interface accepts slightly different request and response
// types.

export interface GapiAnalyzeClient {
  commentanalyzer: GapiCommentAnalyzer;
}

export interface GapiCommentAnalyzer {
  comments: GapiAnalyzer;
}

// The Gapi interface returns the responses wrapped in a result field.
export interface GapiAnalyzeCommentResponse {
  result: AnalyzeCommentResponse;
}

export interface GapiSuggestCommentScoreResponse {
  result: SuggestCommentScoreResponse;
}

// Extends base interfaces for gapi request types for naming clarity.
export interface GapiAnalyzeCommentRequest extends AnalyzeCommentRequest {}

export interface GapiSuggestCommentScoreRequest extends
  SuggestCommentScoreRequest{}

export interface GapiAnalyzer {
  analyze(obj: GapiAnalyzeCommentRequest): Promise<GapiAnalyzeCommentResponse>;
  suggestscore(obj: GapiSuggestCommentScoreRequest)
    : Promise<GapiSuggestCommentScoreResponse>;
}

export interface NodeAnalyzeApiClient {
  comments: NodeAnalyzer;
}

// The Node API interface includes an API key and the request wrapped in a
// resource field.
export interface NodeAnalyzeCommentRequest {
  key: string;
  resource: AnalyzeCommentRequest;
}

export interface NodeSuggestCommentScoreRequest {
  key: string;
  resource: SuggestCommentScoreRequest;
}

// Extends base interfaces for node response types for naming clarity.
export interface NodeAnalyzeCommentResponse extends AnalyzeCommentResponse {}

export interface NodeSuggestCommentScoreResponse extends
  SuggestCommentScoreResponse {}

export interface NodeAnalyzer {
  analyze(obj: NodeAnalyzeCommentRequest,
          handleFn: (error: Error, response: AnalyzeCommentResponse) => void)
    : Promise<NodeAnalyzeCommentResponse>;
  suggestscore(obj: NodeSuggestCommentScoreRequest,
               handleFn: (error: Error,
                          response: SuggestCommentScoreResponse) => void)
    : Promise<NodeSuggestCommentScoreResponse>;
}

export interface ResponseError {
  code: number;
  errors: string[];
}
