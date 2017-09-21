# Wikidetox Viz

This directory contains a google [Google Cloud Appengine Project](https://cloud.google.com/appengine/docs/flexible/) 
that visualizes contributions to Wikipedia. The goal is to help understand toxic contributions at scale. The models are far from perfect which means comments are sometimes incorrectly selected; we do not recommend taking an any automated action based on model scores.

The visualization works by interpreting diffs on Talk Pages into comments, and then scoring the comments
using [Perspective API hosted models](https://github.com/conversationai/perspectiveapi/blob/master/api_reference.md#models). 
If a comment is above a certain threshold, the visualization allows Wikipedians to go the [historical Wikipedia revision page](https://en.wikipedia.org/wiki/Help:Page_history) to help improve the conversation and/or raise awareness with the relevant admins. This work is part of the [Study of Harassment and its Impact](https://meta.wikimedia.org/wiki/Research:Study_of_harassment_and_its_impact), and the [WikiDetox Project](https://meta.wikimedia.org/wiki/Research:Detox), and we hope it can help support Wikipedia's [anti-harassment guidelines](https://en.wikipedia.org/wiki/Wikipedia:How_to_deal_with_harassment).

## Setup

To setup an instance you need a [Google Cloud Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with the [Perpsective API](http://perspectiveapi.com) enabled. 

1. Make a directory called `config` in this directory. 
2. Copy the `config_default_template.js` file to `config/default.js`
3. Enter the `gcloudKey` and `API_KEY` fields with a path to a keyfile for google cloud access, and a Perspective API key respectively.
