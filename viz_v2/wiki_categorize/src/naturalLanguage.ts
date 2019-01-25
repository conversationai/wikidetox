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
// Imports the Google Cloud client library
import * as language from '@google-cloud/language';

interface Category {
  category: string;
  subCategory: string;
  subsubCategory: string;
  confidence: number;
}

export class naturalLanguageApi {
  public client: any;

  constructor(config) {
    this.client = new language.LanguageServiceClient({
      keyFilename: config.keyFilename
    });
  }

  cleanCatResults(categories) {
    let cleanedCats: Category[] = [];
    const prop = 'confidence';

    categories.forEach((category) => {
        category.name = category.name.substr(1);
        const cat = category.name.split('/');
        cleanedCats.push({
            category: cat[0],
            subCategory: cat[1]?cat[1]:null,
            subsubCategory: cat[2]?cat[2]:null,
            confidence: category.confidence
        });
    });

    cleanedCats = cleanedCats.sort((a, b) => a[prop] < b[prop] ? 1 : a[prop] === b[prop] ? 0 : -1 );
    return cleanedCats;
  }

  getCloudCategory = (text, title) => {
    const content = `${text}, ${title}`;
    return this.client
      .classifyText({document: {
        content: content,
        type: 'PLAIN_TEXT',
      }})
      .then(results => {
        const classification = results[0].categories; 
        return this.cleanCatResults(classification);
      })
      .catch(err => {
        if (err.details === 'Invalid text content: too few tokens (words) to process.') {
          return this.getCloudCategory(`${content}, ${content}`, title);
        } else if (err.code === 8) {  
          // Quota exceedded 
          console.log('ERROR:', err)
          return setTimeout((text) => this.getCloudCategory(text, title), 1000); 
        }
        else {  
          console.error('ERROR:', err);                         
          return undefined;
        }
      });
  }
  

}