// import EventSource from 'eventsource';
import * as EventSource from 'eventsource';
import {MediawikiRecentchange} from './recentchanges_schema';

var url = 'https://stream.wikimedia.org/v2/stream/recentchange?since=2018-06-14T00:00:00Z';
// var url = 'https://stream.wikimedia.org/v2/stream/recentchange';

console.log(`Connecting to EventStreams at ${url}`);
var eventSource = new EventSource(url);

eventSource.onopen = function(event) {
    // TODO: probably should be loading/saving a cached file for timestamp.
    // Maybe write timestamp every few minutes, and then load last timestamp,
    // and if none, start fresh. But if found start from that timestamp.
    // See:
    console.log('--- Opened connection event:');
    console.log(event);
};

eventSource.onerror = function(event) {
    console.error('--- Encountered error', event);
    // TODO: probably some kind of exponential retry thing should be happening.
};

eventSource.onmessage = function(event) {
    // event.data will be a JSON string containing the message event.
    let wikiObj : MediawikiRecentchange = JSON.parse(((event as any).data));
    // if(wikiObj.wiki === 'enwiki' && wikiObj.type === 'log') {
    //   console.log(wikiObj);
    // }
    if(wikiObj.type === 'log'
      // && wikiObj.log_deleted !== undefined
      // && wikiObj.log_deleted !== 0
      // && wikiObj.log_action === 'delete'
      && wikiObj.log_type === 'delete'
      // && (JSON.stringify(wikiObj.log_params) !== '[]'
    ) {
      console.log(JSON.stringify(wikiObj));
      // console.log(wikiObj);
    }
};
