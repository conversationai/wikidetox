import Bot = require('nodemw');
const fetch = require('node-fetch');

interface WikiConfig {
    protocol: string;
    server: string;
    path: string;
    debug: boolean;
    username: string;
    userAgent: string;
    password: string;
}

export class WikiBot {
    private wikiClient: any;

    constructor(config: WikiConfig) {
        this.wikiClient = new Bot(config);
    }

    public getRevisionID(pageid): Promise<number> {
        const URL = `https://en.wikipedia.org/w/api.php?` +
        `action=query&format=json&prop=revisions&` +
        `pageids=${pageid}&rvlimit=1&rvprop=ids`
        return fetch(URL, {
            method: 'GET',
            mode: 'cors',
            cache: 'no-cache',
            headers: {
              'Content-Type': 'application/json'
            }
        })
        .then(res => {
              if (res.ok) {
                return res.json()
              } else {
                throw Error(`Wiki request rejected with status ${res.status}`)
              }
        }).then(res => {
              return res.query.pages[pageid].revisions[0].revid;
        }).catch(error => {
            console.error(error)
        })
    }
    
    public editArticle(pageTitle, comment): Promise<string> { // need authentication flow or bot approval
        return new Promise((resolve, reject) => {
            this.wikiClient.getArticle(pageTitle, ( err, res ) => {
                if ( err ) {
                    reject(new Error('Get article failed'));
                    return;
                } else { 
                    if (res === undefined || '') {
                        resolve('Article not found');
                        return;
                    }
                    if (res.includes(comment)) {
                        // Comment still exists on page
                        const cleanedText = res.replace(new RegExp(comment, "g"), '');
                        // if page & comment exists, edit page
                        this.wikiClient.edit( pageTitle, cleanedText, 'Edited with wikidetox-viz.appspot.com, made possible by WikiDetox Project', ( err, res ) => {
                            if ( err ) {
                                console.log( `${pageTitle} edit failed: ${JSON.stringify( err )}` );
                                reject(new Error('Edit failed'));
                                return;
                            } else {
                                resolve(`${pageTitle} edited`);
                                return;
                            }
                        });
                    } else {
                        resolve('Comment not found');
                    }
                }
            });
        });
    }
}

