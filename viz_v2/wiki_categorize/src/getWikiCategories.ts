import fetch from 'node-fetch';

export class getCategories {
    public categoryUrl = `https://en.wikipedia.org/w/api.php?format=json&action=query&prop=categories&cllimit=max&titles=`;

    // Rules for category formating, exclude if these conditions met
    private keywords = ['Wikipedia', 'AC with', 'CS1', 
                        'Good articles', 'Articles', 'All articles', 'Pages', 
                        'Use mdy dates from', 'Use dmy dates from', 'English from', 
                        'Webarchive template', 'births', 'deaths',
                        'Redirects'];

    cleanCategories(categories) {
        let catArray = categories.filter((cat) => {
            return !this.keywords.some(key => cat.title.includes(key));
        }).map(cat => {
            return cat.title.substring(9);
        });
        if (catArray.length === 0) {
            return undefined; // no valid wikipedia categories returned
        } else {
            const catString = catArray.join(', ');
            return catString;
        }
        
    }

    getWikiCategories(title) {
        if (title.includes('/Archive')) {
            title = title.split('/')[0];
        }
        return fetch(`${this.categoryUrl}${encodeURIComponent(title)}`)
            .then(res => res.json())
            .then(body => { 
                //console.log(body);
                const results = body.query.pages;
                const firstKey = Object.keys(results)[0];
                const categories = results[firstKey].categories;
                if (categories) {
                    const cleanedCats = this.cleanCategories(categories);
                    if (cleanedCats !== undefined) {
                        console.log(`Got wiki categories for ${title}`);
                        return `${title}, ${cleanedCats}`;
                    } else {
                        console.log(`No valid categories returned for ${title}`);
                        return cleanedCats;
                    }
                   
                }
            })
            .catch(err => { 
                console.error(err);
            });
        
    }

}
