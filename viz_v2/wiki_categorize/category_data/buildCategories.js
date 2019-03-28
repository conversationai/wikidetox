const data = require('./Cloud_categories.json');
const fs = require('fs');

const categories = [];

data.forEach(category => {
    category = category.substr(1).split('/');
    switch (category.length) {
        case 1:
            categories.push({
                name: category[0],
                children: []
            });
            break;
        case 2:
            const parent = categories.find( cat => cat.name === category[0] );
            if(parent) {
                parent.children.push({
                    name: category[1],
                    children: []
                })
            } else {
                categories.push({
                    name: category[0],
                    children: [{
                        name: category[1],
                        children: []
                    }]
                });
            }
        case 3:
            const grandParent = categories.find( cat => cat.name === category[0] );
            if(grandParent) {
                const parent = grandParent.children.find( cat => cat.name === category[1] );
                if(parent) {
                    parent.children.push({name: category[2]});
                } else {
                    grandParent.children.push({
                        name: category[1],
                        children: [{name: category[2]}]
                    });
                }
                
            } else {
                categories.push({
                    name: category[0],
                    children: [{
                        name: category[1],
                        children: [{name: category[2]}]
                    }]
                });
            }
          break;
        default:
          console.log(`error: ${JSON.stringify(category)}`);
    } 
});

fs.writeFile("./cleaned_categories.json", JSON.stringify(categories), function(err) {
    if(err) {
        return console.log(err);
    }
    console.log("The file was saved!");
});

