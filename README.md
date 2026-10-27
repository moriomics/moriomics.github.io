# moriomics Portfolio

A curated GitHub Pages portfolio for selected software projects.

The site intentionally shows only projects chosen for portfolio use rather than automatically listing every public GitHub repository.

## Project visibility management

Portfolio entries are managed in `projects.js`.

Each project has a `visible` setting:

```js
{
  title: "Molarity Calculator",
  visible: true,
  // ...
}
```

- `visible: true` — the project is shown on the portfolio.
- `visible: false` — the project remains in `projects.js` but is hidden from the portfolio.

The display order is the same as the order of entries in `projects.js`. Project numbers are generated automatically from the currently visible entries.

This makes it possible to change which projects are shown to employers without deleting repositories or editing the main HTML layout.

## Portfolio sections

The site is organized into:

- Tools
- Data Analysis
- Case Studies

Data Analysis and Case Studies are currently placeholders and will be populated later.

## Included tools

The current Tools configuration includes:

- OpenAlex Literature Search
- Molarity Calculator
- PDF Toolkit
- Local Transcriber — Windows desktop MVP, published under `tools/local-transcriber`
- Image Resizer
- Grayscale Trinarization Desktop App

## Features

- Responsive single-page portfolio
- Separate Tools, Data Analysis, and Case Studies sections
- Japanese / English two-button language switch
- Project summary, technologies, live web-app link, and GitHub source link
- Project cards generated from a single configuration file
- `visible: true / false` control for portfolio inclusion
- Selected-project curation independent of the full public repository list
- No framework or build step required

## Files

- `index.html` — Portfolio page structure
- `projects.js` — Project list, descriptions, technologies, links, ordering, and visibility settings
- `styles.css` — Responsive styling
- `script.js` — Project rendering and Japanese / English UI switching

## Deployment

This repository is published as the GitHub Pages user site:

`https://moriomics.github.io/`

## License

No open-source license is included.

Source code is publicly available for portfolio and review purposes. No license for reuse, modification, or redistribution is granted.

