import Bot = require('nodemw');

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
        this.wikiClient.logIn(config.username, config.password, (err, res) => {
            console.log(`Logging into Wikipedia as ${config.username}`);
            if ( err ) {
                console.log( 'WikiBot log in failed: ' + JSON.stringify( err ) );
            } else {
                console.log( 'WikiBot logged in! :D' );
                console.log( res );
            }
        })
    }
    
    public editArticle(pageTitle, comment): Promise<string> {
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
                        this.wikiClient.edit( pageTitle, cleanedText, 'Edited by DetoxAgent, by WikiDetox Project', ( err, res ) => {
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

