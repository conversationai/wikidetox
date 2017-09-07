# WikiDetox

The shared codebase for experiments on Wikimedia, part of [the Study of
Harassment and its
Impact](https://meta.wikimedia.org/wiki/Research:Study_of_harassment_and_its_impact), and [the WikiDetox Project](https://meta.wikimedia.org/wiki/Research:Detox).

This project consists of trying to reconstruct the conversation structure from Wikipedia diffs, human and machine annotation of the structured conversations, and analysis of the impact of harassment and other toxic contributions, and also experimention with ways to visualize this information and make it interesting and useful to Wikipedians.

For large scale machine scoring of comments, we use the [Perspective API](https://www.perspectivepai.com).

Below is an idea for how we might vizualise toxic comments on Wikipedia (as red objects), and show when they are reverted (as grey objects), where size is the toxicity probability.

![sphere_interface_low_res_preview](https://user-images.githubusercontent.com/1489560/30126500-1520b868-930a-11e7-8383-3d551637c758.jpg)

We're still exploring how we might visualize more information, such as:
 * Which are the more recent comments? Can we visualizse when comments happen?
 * Can we cluster comments by topic in a meaningful way?
 * Can we make the visualization live, so that new comments 'fly' in when they are sent to wikipedia? 
 * Other cool ideas? File an issue with you idea :) 

## Notes

This code is an experimental Conversation AI project; it is not an official Google product.
