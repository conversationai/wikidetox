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

// Only one of the properties of QuestionPartSchema
// should be set.
export interface QuestionPartSchema {
  validEnumValues ?: string[];
  stringInput ?: {}
}

export interface QuestionSchema {
  [questionPartId:string] : QuestionPartSchema
}

export interface QuestionPartScores {
  // Optional question: you get scores if you answer it, but you may skip.
  optional ?: boolean;  // Is not set treated as false.

  // Only one of these should be set.

  // Associates a score value to each possible string answer.
  enum ?: { [enumValue:string] : number };

  // Regexp where string gets score depending on match/no match.
  stringRegExp ?: {
    regexp : string;
    regexpFlags: string;
    matchScore: number;
    noMatchScore: number;
  };
  // Free test strings that always get the same score.
  freeStringConstScore ?: number;
}

// A questionaire (for a given question) consists of a named set of question parts.
export interface QuestionScores { [questionPartId:string] : QuestionPartScores }

// TODO: consider: should we deal with other answer types apart from string.
// e.g. compound objects? And should we check for them?
export interface Answer {
  [questionairePartId:string] : string;
}

export function answerPartScore(q:QuestionPartScores, answer:string | undefined | null) : number {
  if(answer === undefined || answer === null) {
    if(!q.optional) {
      throw Error('Answer must be provided, but was not.');
    } else {
      return 0;
    }
  }

  if(q.enum !== undefined) {
    let lowerCaseAnswer = answer.toLowerCase();
    if (!(lowerCaseAnswer in q.enum)) {
      throw Error(`Answer ${lowerCaseAnswer} does not match enum values:` +
        ` ${JSON.stringify(Object.keys(q.enum))}`);
    }
    return q.enum[lowerCaseAnswer];
  } else if(q.stringRegExp !== undefined) {
    let regexp = new RegExp(q.stringRegExp.regexp, q.stringRegExp.regexpFlags);
    if(answer.match(regexp)) {
      return q.stringRegExp.matchScore;
    } else {
      return q.stringRegExp.noMatchScore;
    }
  } else if(q.freeStringConstScore !== undefined) {
    return q.freeStringConstScore;
  } else{
    throw Error('Unrecognized question' + JSON.stringify(Object.keys(q)));
  }
}

export function answerScore(questionScores:QuestionScores, answer:Answer) : number {
    let score = 0;
    for (let q in questionScores) {
      score += answerPartScore(questionScores[q], answer[q]);
    }
    return score;
}

// Checks that for part of an answer matches the expected kind of answer.
export function answerPartMatchesSchema(
    partSchema: QuestionPartSchema, answerPart : string) {
  if (partSchema.validEnumValues !== undefined) {
    return partSchema.validEnumValues.indexOf(answerPart) != -1;
  } else if (partSchema.stringInput !== undefined) {
    return typeof(answerPart) === 'string';
  }
  else {
    console.error('Unimplemented schema');
    return false;
  }
}

// All parts of schema exist in the answer. But the answer may have more stuff too.
export function answerMatchesSchema(schema: QuestionSchema, answer: Answer) {
  // let answerCopy = JSON.parse(JSON.stringify(answer));
  for (let partSchemaKey in schema) {
    if(!(partSchemaKey in answer)) {
      return false;
    }
    return answerPartMatchesSchema(schema[partSchemaKey], answer[partSchemaKey]);
  }
  return true;
}

