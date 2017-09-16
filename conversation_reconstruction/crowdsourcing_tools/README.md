# Crowd-Sourcing Tools

This directory contains some tools to support Crowd Sourcing using CrowdFlower. In particular, some JavaScript to allow a prettier layout of the conversation structure.

## Setup

This is a standard nodejs/yarn project. You need to have installed
`npm` and `node` (Recommended to install using [nvm](https://github.com/creationix/nvm), the node version manager).

Once you have `npm`, install `yarn` and `typescript` globally with:

```shell
npm install -g yarn typescript
```

Then, from this directory, you can setup the this node package with:

```shell
yarn install
```

## Build

```shell
yarn run build
```

Generated files end up in `build/dist`.

## Test Locally

```shell
yarn run serve
```

Then open this URL in your browser:

http://localhost:8000/src/testdata/test.html

And observe the test conversations look right, and that no errors appear in the
JavaScript console.

## Deploy to CrowdFlower

CrowdFlower has 3 sections that need files from this directory need to be copied to the relevant UI input boxes in a CrowdFlower's Job page (afer you run the build command):

* CML: `src/cml.html`
* JavaScript: `build/dist/index.js`
* CSS: `src/style.css`
