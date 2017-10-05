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

export interface QuestionPart {
  // Associates a score value to each possible string answer.
  enumScores?: { [enumValue:string] : number };
  // If the answer is in the enumScores above, then this is the score.
  noValueScore: number;
}

// A questionaire (for a given question) consists of a named set of question parts.
export interface Questionaire { [questionPartId:string] : QuestionPart }

// An answer to a part of a question.
export interface QuestionPartAnswer {
  // An answer to an 'enumScores' question.
  enumAnswer?: string;
}

export interface Answer {
  [questionairePartId:string] : QuestionPartAnswer
}

export function answerScore(q:QuestionPart, a:QuestionPartAnswer) : number {
  function noValue() {
    if (q.noValueScore === undefined) {
      throw Error('No such enumAnswer in question enumScores, and no noValueScore.');
    }
    return q.noValueScore;
  }

  if(q.enumScores) {
    if (!a.enumAnswer || !(a.enumAnswer in q.enumScores)) {
      return noValue();
    }
    return q.enumScores[a.enumAnswer];
  } else {
    console.error('partAnswerScore: unsupported question: only enumScores questions are supported right now.');
    // TODO(ldixon): consider should this throw?
    return noValue();
  }
}

// May throw an JSON parse exception.
export function answerScoreFromJson(questionaireJson:string, answersJson:string) : number {
    let questionaire = JSON.parse(questionaireJson);
    let answers = JSON.parse(answersJson);
    let score = 0;
    for (let q in questionaire) {
      score += answerScore(questionaire[q], answers[q]);
    }
    return score;
}