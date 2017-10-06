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

    let acceptedAnswersJson = `{ \"toxicity\": { \"enumScores\": { \"ok\": 0, \"not sure\": -1, \"toxic\": -1 } } }`;
    let answerJson = "{ \"toxicity\": { \"enumAnswer\": \"toxic\" } }";

    let score = questionaire.answerScoreFromJson(acceptedAnswersJson, answerJson);
    expect(score).to.equal(-1);
  });

  it('Non-existent entry without a noValue score throws exception', function() {
    let acceptedAnswersJson = `{ \"toxicity\": { \"enumScores\": { \"ok\": 0, \"not sure\": -1, \"toxic\": -1 } } }`;
    let answerJson = "{ \"toxicity\": { \"enumAnswer\": \"foo\" } }";

    expect(() => questionaire.answerScoreFromJson(acceptedAnswersJson, answerJson)).to.throw;
  });

  it('Non-existent entry with set noValue scire is noValue score', function() {
    let acceptedAnswersJson = `{ \"toxicity\": {
        \"noValueScore\": -2,
        \"enumScores\": { \"ok\": 0, \"not sure\": -1, \"toxic\": -1 } } }`;
    let answerJson = "{ \"toxicity\": { \"enumAnswer\": \"foo\" } }";

    let score = questionaire.answerScoreFromJson(acceptedAnswersJson, answerJson);
    expect(score).to.equal(-2);
  });
});

