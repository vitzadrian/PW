# Austrian Open Government Data & Vis Landscape

An interactive web application visualizing the Austrian Open Government Data 
(OGD) ecosystem. Explore the relationships between publicly available datasets 
and the applications built upon them, hosted at 
[vitzadrian.github.io/PW](https://vitzadrian.github.io/PW).

## What it does

Austria's [data.gv.at](https://www.data.gv.at) portal catalogs thousands of 
datasets alongside several hundred applications. This project makes the 
structure of that ecosystem visible through two interactive visualizations:

- **Force-Directed Graph** — A network of all applications and the datasets 
  they are built upon. Node size reflects connection count. Click any node to 
  inspect its direct connections and discover similar entries by Jaccard 
  similarity. Filter by minimum connectivity to focus on the most widely used 
  datasets.
- **Zoomable Treemap** — A hierarchical thematic overview of the catalog, 
  navigable by categories like topics, publishers, licenses, and more.

The data is fetched from the data.gv.at Piveau API and updated automatically every 
day via a scheduled GitHub Actions workflow.

## Project structure

src/
index.md # main page with force-directed graph
treemap.md # zoomable treemap page
data/
graph.zip.py # Python data loader (nodes + links CSVs)
check_updates.py # daily change detection script

## Tech stack

- [Observable Framework](https://observablehq.com/framework/) — static site 
  framework with reactive cells and SQL data queries
- [D3.js](https://d3js.org/) — force simulation and treemap layout
- Python — data loader fetching and assembling the API data
- GitHub Actions — scheduled daily data updates and deployment to GitHub Pages


