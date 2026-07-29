---
lang: en
---

<div style="max-width: 640px; margin: 0 auto; text-align: center; padding: 3rem 0 2rem;">
  <h1 style="font-size: 48px; font-weight: 600; margin: 0 0 0.5rem;">
    Practical Work: Open Data &amp; Vis Landscape
  </h1>
  <h2 style="font-size: 20px; font-weight: 400; margin: 0; color: var(--theme-foreground-muted);">
    Visualizing Austria's Open Government Data Ecosystem
  </h2>
</div>

<style>
.about-section {
  max-width: 640px;
  margin: 0 auto 2rem;
  line-height: 1.7;
  font-size: 16px;
  text-align: justify;
  hyphens: auto;
  -webkit-hyphens: auto;
}

.about-section h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 2rem 0 0.5rem;
  color: var(--theme-foreground);
}

.about-section p {
  color: var(--theme-foreground-muted);
  margin: 0 0 1rem;
}

.about-section ul {
  color: var(--theme-foreground-muted);
  padding-left: 1.5rem;
  margin: 0 0 1rem;
}

.about-section ul li {
  margin-bottom: 0.4rem;
}

.about-section a {
  color: var(--theme-foreground-focus);
}
</style>

<div class="about-section">

## Motivation

Austria's [data.gv.at](https://www.data.gv.at) portal is one of the more active 
Open Government Data (OGD) ecosystems in Europe, cataloging thousands of publicly 
available datasets alongside several hundred applications built upon them. While 
finding a specific entry on the portal is straightforward, gaining a structural 
overview of what is available, which datasets are most actively used in practice, 
and how entries relate to one another is difficult through browsing alone.

This project addresses that gap by showing the Austrian OGD ecosystem through 
two complementary interactive visualizations built on live data fetched directly 
from the portal's API.

## Visualizations

The **[Force-Directed Graph](/force-graph)** maps the full network of applications and the datasets 
they are built upon. Each node represents either a dataset or an application, 
with size scaled to the number of connections. The layout naturally surfaces 
widely-used datasets as prominent, central nodes, while revealing thematic 
clusters within the ecosystem. Interactivity includes:

- Hover highlighting of direct neighbours.
- Click-based selection with connection tables.
- A minimum connections filter to focus on the most active part of the network.
- Similarity scoring via shared connections or Jaccard Similarity.

The **[Zoomable Treemap](/treemap)** provides a hierarchical thematic overview of the catalog, 
allowing users to navigate from broad topic areas down through subcategories to 
individual datasets by topic, publisher, and license. This visualization 
complements the force graph by situating datasets within their broader subject 
domains rather than their relational structure.

## Implementation

The application is built on [Observable Framework](https://observablehq.com/framework/), 
a static site framework with a reactive programming model that allows JavaScript, 
Python, and SQL to work in tandem within a single project. Data visualizations 
are implemented in [D3.js](https://d3js.org/).

Data is sourced from the data.gv.at Piveau API via a Python data loader.
A scheduled GitHub Actions workflow runs daily, checking whether the list of 
published applications has changed and triggering a full data reload when 
additions or deletions are detected. A weekly hard reset captures subtler 
changes such as updated titles or newly linked datasets, ensuring the 
visualization always reflects the current state of the portal.

## Outlook

The Austrian OGD ecosystem exhibits a pattern common to many open data portals: 
a small number of highly connected datasets consumed by many applications, and 
a long tail of datasets with few or no real-world uses. This suggests that 
investment in dataset discoverability and active outreach to application 
developers may be more impactful for ecosystem health than simply increasing 
the volume of published data.

The most natural extension of this project is to broaden its scope to other 
European OGD portals. The [European Data Portal](https://data.europa.eu) 
aggregates metadata from national portals across EU member states and exposes 
a comparable API, making a cross-national version of this visualization 
technically feasible with relatively minor modifications to the existing data 
pipeline. Such an extension would enable comparison of OGD ecosystem maturity 
across countries and analysis of which thematic domains are underrepresented 
in specific national catalogs.

## About

This project was developed as a Practical Work for the AI BSc program at 
[JKU Linz](https://www.jku.at), supervised by Andreas Hinterreiter and 
Prof. Marc Streit at the 
[Institute of Computer Graphics](https://www.jku.at/en/institute-of-computer-graphics/). 
Source code is available on [GitHub](https://github.com/vitzadrian/PW).

</div>