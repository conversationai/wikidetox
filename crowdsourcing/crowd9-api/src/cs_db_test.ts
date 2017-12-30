// import * as spanner from '@google-cloud/spanner';
// import * as crowdsourcedb from './crowdsourcedb';
// import { expect } from 'chai';

// class FakeSpannerDB implements spanner.Database {
//   close(cb : Function) => { setTimeout(() => cb(), 0) },
//   table(tableName:string) : spanner.Table => {
//     let x : spanner.Table;
//     return x;
//   };
//   run(query:Query): Promise<QueryResult[]>;
// }

// class FakeSpannerDB implements spanner.Database {
//   close(cb : Function) => { setTimeout(() => cb(), 0) },
//   table(tableName:string) : spanner.Table => {
//     let x : spanner.Table;
//     return x;
//   };
//   run(query:Query): Promise<QueryResult[]>;
// }


// describe('Testing questionaire', function() {

//   it('Simple answer test', function() {

//     let acceptedAnswers = { toxic: { enum: { notatall: 0, somewhat: -1, very: -1 } } };
//     let answer = { toxic: 'very' };

//     let score = questionaire.answerScore(acceptedAnswers, answer);
//     expect(score).to.equal(-1);
//   });

// });
