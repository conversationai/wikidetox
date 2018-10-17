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

  getCloudCategory = (text) => {
    return this.client
      .classifyText({document: {
        content: text,
        type: 'PLAIN_TEXT',
      }})
      .then(results => {
        const classification = results[0].categories; 
        return this.cleanCatResults(classification);
      })
      .catch(err => {
        if (err.details === 'Invalid text content: too few tokens (words) to process.') {
          // If not enought words
          return this.getCloudCategory(`${text}, ${text}`);
        } else if (err.code === 8) { 
          // If quota exceedded 
          return setTimeout(() => this.getCloudCategory(text), 5000); 
        }
        else {
          console.error('ERROR:', err);                            
          return undefined;
        }
      });
  }
  

}