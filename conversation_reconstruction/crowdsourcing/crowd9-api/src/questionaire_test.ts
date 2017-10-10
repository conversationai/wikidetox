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
import * as questionaire from './questionaire';
import { expect } from 'chai';

describe('Testing questionaire', function() {
  it('Simple answer test', function() {

    let acceptedAnswersJson = `{ "toxicity": { "enum": { "ok": 0, "unsure": -1, "very": -1 } } }`;
    let answerJson = `{ "toxicity": "very" }`;

    let score = questionaire.answerScoreFromJson(acceptedAnswersJson, answerJson);
    expect(score).to.equal(-1);
  });

  it('Non-existent answer entry throws exception', function() {
    let acceptedAnswersJson = `{ "toxicity": { "enum": { "ok": 0, "unsure: -1, "very": -1 } } }`;
    let answerJson = `{ "nosuchquestion": "foo" }`;

    expect(() => questionaire.answerScoreFromJson(acceptedAnswersJson, answerJson)).to.throw;
  });

  it('Non-existent answer for optional question gives 0 score', function() {
    let acceptedAnswersJson = `{ "toxicity": {
        "optional": true,
        "enum": { "ok": 0, "unsure": -1, "toxic": -1 } } }`;
    let answerJson = `{ "nosuchquestion": "foo" }`;
    let score = questionaire.answerScoreFromJson(acceptedAnswersJson, answerJson);
    expect(score).to.equal(0);
  });

  it('Non-existent enum entry throws exception', function() {
    let acceptedAnswersJson = `{ "toxicity": { "enum": { "ok": 0, "unsure": -1, "very": -1 } } }`;
    let answerJson = `{ "toxicity": "foo" }`;

    expect(() => questionaire.answerScoreFromJson(acceptedAnswersJson, answerJson)).to.throw;
  });

  it('RegExp matching', function() {
    let acceptedAnswersJson = `{ "thingMaybeDigits": {
        "stringRegExp": { "regexp": "\\\\d+", "regexpFlags": "g", "matchScore": 1, "noMatchScore": -1 } } }`;
    let answer1Json = `{ "thingMaybeDigits": "foo bar \\n123 bugs" }`;
    let answer2Json = `{ "thingMaybeDigits": "foo bar" }`;
    expect(questionaire.answerScoreFromJson(acceptedAnswersJson, answer1Json)).to.equal(1);
    expect(questionaire.answerScoreFromJson(acceptedAnswersJson, answer2Json)).to.equal(-1);
  });

  it('Free text string', function() {
    let acceptedAnswersJson = `{ "comments": { "freeStringConstScore": 1 } }`;
    let answerJson = `{ "comments": "foo bar" }`;
    expect(questionaire.answerScoreFromJson(acceptedAnswersJson, answerJson)).to.equal(1);
  });
});

