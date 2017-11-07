/*
Copyright 2017 Google Inc.

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
import * as questionaire from './questionaire';
import { expect } from 'chai';

describe('Testing questionaire: answerScore', function() {

  it('Simple answer test', function() {
    let acceptedAnswers = { toxic: { enum: { notatall: 0, somewhat: -1, very: -1 } } };
    let answer = { toxic: 'very' };

    let score = questionaire.answerScore(acceptedAnswers, answer);
    expect(score).to.equal(-1);
  });

  it('Answer some of multiple question parts', function() {
    let acceptedAnswers = {
      toxic: { enum: { notatall: 0, somewhat: -1, very: -1 } },
      obscene: { optional: true, enum: { notatall: 0, somewhat: -1, very: -1 } },
    };
    let answer = { toxic: 'very' };

    let score = questionaire.answerScore(acceptedAnswers, answer);
    expect(score).to.equal(-1);
  });

  it('Non-existent answer entry throws exception', function() {
    let acceptedAnswers = { toxic: { enum: { notatall: 0, somewhat: -1, very: -1 } } };
    let answer = { nosuchquestion: 'foo' };

    expect(() => questionaire.answerScore(acceptedAnswers, answer)).to.throw;
  });

  it('Non-existent answer for optional question gives 0 score', function() {
    let acceptedAnswers = { toxic: {
        optional: true,
        enum: { notatall: 0, somewhat: -1, very: -1 } } };
    let answer = { nosuchquestion: 'foo' };
    let score = questionaire.answerScore(acceptedAnswers, answer);
    expect(score).to.equal(0);
  });

  it('Non-existent enum entry throws exception', function() {
    let acceptedAnswers = { toxic: { enum: { notatall: 0, somewhat: -1, very: -1 } } };
    let answer = { toxic: 'foo' };
    expect(() => questionaire.answerScore(acceptedAnswers, answer)).to.throw;
  });

  it('RegExp matching', function() {
    let acceptedAnswers = { thingMaybeDigits: {
        stringRegExp: { regexp: '\\d+', regexpFlags: 'g', matchScore: 1, noMatchScore: -1 } } };
    let answer1 = { thingMaybeDigits: 'foo bar \n 123 bugs' };
    let answer2 = { thingMaybeDigits: 'foo bar' };
    expect(questionaire.answerScore(acceptedAnswers, answer1)).to.equal(1);
    expect(questionaire.answerScore(acceptedAnswers, answer2)).to.equal(-1);
  });

  it('Free text string', function() {
    let acceptedAnswers = { comments: { freeStringConstScore: 1 } };
    let answer = { comments: 'foo bar' };
    expect(questionaire.answerScore(acceptedAnswers, answer)).to.equal(1);
  });
});


describe('Testing questionaire: answerMatchesSchema', function() {
  it('simple answerMatchesSchema is true', function() {
    let answerSchema = { toxic: { validEnumValues: ['notatall', 'somewhat', 'very'] },
                         comments: { stringInput : {}, optional: true } };
    let answer = { toxic: 'very' };
    expect(questionaire.answerMatchesSchema(answerSchema, answer)).to.equal(true);
  });
  it('optional answerMatchesSchema is true', function() {
    let answerSchema = { toxic: { validEnumValues: ['notatall', 'somewhat', 'very'] },
                         comments: { stringInput : {}, optional: true } };
    let answer = { toxic: 'very', comments: 'blah de blah' };
    expect(questionaire.answerMatchesSchema(answerSchema, answer)).to.equal(true);
  });
  it('answerMatchesSchema only optional is false', function() {
    let answerSchema = { toxic: { validEnumValues: ['notatall', 'somewhat', 'very'] },
                         comments: { stringInput : {}, optional: true } };
    let answer = { comments: 'very' };
    expect(questionaire.answerMatchesSchema(answerSchema, answer)).to.equal(false);
  });
  it('answerMatchesSchema bad key is false', function() {
    let answerSchema = { toxic: { validEnumValues: ['notatall', 'somewhat', 'very'] },
                         comments: { stringInput : {}, optional: true } };
    let answer = { foo: 'very' };
    expect(questionaire.answerMatchesSchema(answerSchema, answer)).to.equal(false);
  });
});
