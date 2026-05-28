---
sql:
    formattedNodes: data/graph/formattedNodes.csv
    formattedLinks: data/graph/formattedLinks.csv
---

<div class="hero">
  <h1>Practical Work OGD</h1>
  <h2>by Adrian Vitzthum-Lettner</h2>
</div>

<style>

.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: var(--sans-serif);
  margin: 4rem 0 8rem;
  text-wrap: balance;
  text-align: center;
}

.hero h1 {
  margin: 1rem 0;
  padding: 1rem 0;
  max-width: none;
  font-size: 14vw;
  font-weight: 900;
  line-height: 1;
  background: linear-gradient(30deg, var(--theme-foreground-focus), currentColor);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero h2 {
  margin: 0;
  max-width: 34em;
  font-size: 20px;
  font-style: initial;
  font-weight: 500;
  line-height: 1.5;
  color: var(--theme-foreground-muted);
}

@media (min-width: 640px) {
  .hero h1 {
    font-size: 90px;
  }
}

</style>


<!-- Data Loading / Tables -->

# Data

### Nodes

```sql id=Nodes display
SELECT id, title, "group", connections
FROM formattedNodes
```

### Links

```sql id=Links display
SELECT source, "target", value
FROM formattedLinks
```

# Force-Directed Graph

<!-- Connections Slider -->

```js
const minConnections = view(Inputs.range([1, 10], {value: 1, step: 1, label: "Min. connected Apps"}))
```

<!-- Force-Graph Cell-->

```js
// Base graph dimensions (adjusted automatically)
const width = 1800
const height = 1200

// Copy data because simulation mutates objects
const nodes = Nodes.toArray().map(d => ({...d}))
const links = Links.toArray().map(d => ({...d}))

// Node color scale
const color = d3.scaleOrdinal(d3.schemeCategory10)

// SVG properties
const radiusScale = d3.scaleLinear()
  .domain(d3.extent(nodes, d => d.connections))
  .range([5, 25])

const svg = d3.create("svg")
  .attr("width", width)
  .attr("height", height)
  .attr("viewBox", [-width/2, -height/2, width, height])
  .style("max-width", "100%")
  .style("height", "auto")

// Reset graph on background click
svg.on("click", function(event) {
  if (event.target === this) {  // only fire if the click was on the SVG background, not a node
    reset();
  }
});

const link = svg.append("g")
  .attr("stroke", "#999")
  .attr("stroke-opacity", 0.6)
  .style("pointer-events", "none")  // make sure links cant be hovered/clicked
  .selectAll("line")
  .data(links)
  .join("line")
  .attr("stroke-width", d => Math.sqrt(d.value))

const node = svg.append("g")
  .attr("stroke", "#fff")
  .attr("stroke-width", 1.5)
  .selectAll("circle")
  .data(nodes)
  .join("circle")
  .attr("r", d => radiusScale(d.connections))
  .attr("fill", d => color(d.group))
    // event handlers
    .on("mouseover", mouseover)  
    .on("mouseout", mouseout)
    .on("click", click)

node.append("title").text(d => `${d.title}\nConnections: ${d.connections}`) // append titles

// Force Simulation
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id))
  .force("charge", d3.forceManyBody().strength(-50))
  .force("x", d3.forceX().strength(0.115))
  .force("y", d3.forceY().strength(0.18))
  .force("collide", d3.forceCollide(d => radiusScale(d.connections) + 1))
  .alphaDecay(0.03)  // stabilize the simulation quickly, but accurately

simulation.on("tick", () => {
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y)
  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y)
})

// Adjacency map for efficient calcs
const adjacency = new Map() 
const getId = x => typeof x === "object" ? x.id : x;  // ID helper (also used in other cells)

nodes.forEach(n => adjacency.set(n.id, new Set()))

links.forEach(l => {
  const s = getId(l.source)
  const t = getId(l.target)
  adjacency.get(s).add(t)
  adjacency.get(t).add(s)
})

// If an application node is clicked, we want to display all neighbouring dataset nodes,
// even if they have less connections than minConnections, but clicking them breaks the graph.
// We want to avoid graph reloading, but cannot reassign external variables in Observable. 
// Mutating an external property like clickThreshold.state however is allowed.
const clickThreshold = { state: 1 };

// Highlight/Reset helper functions
let clicked = null;
let clickedNode = Mutable(null);  // mutable to avoid graph reloading in update cell
let nodeById = new Map(nodes.map(n => [n.id, n]));

function highlight(d) {
  const neighbours = adjacency.get(d.id) || new Set();  // get all direct neighbours from adjacency map
  node.attr("opacity", n =>
    n.id === d.id || neighbours.has(n.id) ? 1 : 0.1  // set opacity of the node and its neighbours to 1; all others to 0.1
  );
  link
    .attr("opacity", l =>
      l.source.id === d.id || l.target.id === d.id ? 1 : 0.2  // set opacity of links connected to node to 1; all others 0.2
    )
    .attr("stroke-width", l =>
      l.source.id === d.id || l.target.id === d.id ? 2 : 1  // similar for link stroke width
    );
}

function reset() {
  node.attr("opacity", 1);  // reset node opacity
  link.attr("opacity", 1).attr("stroke-width", 1);  // reset link opacity and stroke width
  clicked = null;
  clickedNode.value = null;
}

// Event functions
function mouseover(event, d) {
  if (clicked) return;  // do nothing if a node is clicked
  highlight(d);  // otherwise highlight correct nodes
}

function mouseout(event, d) {
  if (clicked) return;  // do nothing if a node is clicked
  reset();  // otherwise reset graph view
}

function click(event, d) {
  if (d.group === "Dataset" && d.connections < clickThreshold.state) return;  // do not allow clicking "bonus" nodes
  if (clicked && clicked.id === d.id) {  // if a node is clicked twice -> reset graph view
    reset();  
  } else {  // if no node is clicked -> highlight correct nodes
    clicked = d;  // assign clicked to deactivate mouseover/mouseout
    clickedNode.value = d;
    highlight(d);
  }
}

// Display the graph
display(svg.node())

// Color legend
const legendItemHeight = 32;
const legendWidth = 160;

const groups = [...new Set(nodes.map(n => n.group))].sort();

const legend = svg.append("g")
  .attr("transform", `translate(${width/2 - legendWidth - 20}, ${-height/2 + 20})`);

groups.forEach((group, i) => {
  const row = legend.append("g")
    .attr("transform", `translate(0, ${i * legendItemHeight})`);
  row.append("circle")
    .attr("r", 10)
    .attr("fill", color(group))
    .attr("stroke", "currentColor")  // adjust circle outline color to background color
    .attr("stroke-width", 1.5);
  row.append("text")
    .attr("x", 20)
    .attr("y", 10)
    .attr("font-size", 28)
    .attr("fill", "currentColor")
    .text(group);
});
```

<!-- Update Cell (avoid reloading the graph) -->

```js
clickThreshold.state = minConnections;  // update "bonus" node clickThreshold value
const visibleDatasets = new Set();
const visibleNodes = new Set();
const bonusNodes = new Set();

// Get dataset nodes with enough connections
nodes.forEach(n => {
  if (n.group === "Dataset" && n.connections >= minConnections) {
    visibleDatasets.add(n.id);
  }
});

// Add datasets and directly connected applications to visibleNodes
visibleDatasets.forEach(id => {
  visibleNodes.add(id);
  adjacency.get(id)?.forEach(neighbourId => visibleNodes.add(neighbourId));
});

// Identify normally not visible (due to minConnections slider) "bonus" nodes if a neighbour is clicked
if (clickedNode && clickedNode.group === "Application") {
  adjacency.get(clickedNode.id)?.forEach(neighbourId => {
    if (!visibleNodes.has(neighbourId)) {
      bonusNodes.add(neighbourId);
    }
  });
}

// Add "bonus" nodes to the visibleNodes
bonusNodes.forEach(id => visibleNodes.add(id));

// Toggle node visibility
node.style("display", n => visibleNodes.has(n.id) ? null : "none")

// Toggle link visibility
link.style("display", l => {
  const source = getId(l.source);
  const target = getId(l.target);
  return visibleNodes.has(source) && visibleNodes.has(target) ? null : "none";
});
```

<!-- Table Cells (Data/Slider/Display) -->

```js
// Top 20 datasets by connections (default)
const topDatasets = nodes
  .filter(n => n.group === "Dataset")
  .sort((a, b) => b.connections - a.connections)
  .slice(0, 20);

// Most connected neighbours lookup helper
function getNeighbourNodes(d) {
  return [...(adjacency.get(d.id) || new Set())]
    .map(id => nodeById.get(id))  // helper function from graph cell
    .sort((a, b) => b.connections - a.connections);    
}

// Resolve what to show
const tableData = clickedNode === null
  ? topDatasets  // if no node is clicked -> show default table
  : getNeighbourNodes(clickedNode);  // if a node is clicked -> show neighbouring nodes table
```

```js
const tableEntries = view(Inputs.range([1, tableData.length], {value: 5, step: 1, label: "Number of Rows"}))
```

```js
const tableDataSliced = tableData.slice(0, tableEntries);  // slice table data according to slider
const stripTitlePrefix = title => title.replace(/^(Dataset|Application): /, "")  // strip title prefixes

// Table title
const tableTitle = clickedNode === null
  ? `Top ${tableEntries} Datasets`
  : clickedNode.group === "Dataset"
    ? `Top ${tableEntries} Applications linked to ${clickedNode.title}`
    : `Top ${tableEntries} Datasets linked to ${clickedNode.title}`;

const connectedNodesGroup = clickedNode === null
  ? "Application" : clickedNode.group

// Build table HTML - header is in the html template, rows are injected via innerHTML
// to avoid Observable wrapping map() results in fragments that break table structure
const table = html`
  <div style="overflow-x: auto; max-height: 460px; overflow-y: auto;">
    <p><strong>${tableTitle}</strong> ranked by number of connected ${connectedNodesGroup}s.</p>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; min-width: 600px;">
      <thead>
        <tr style="border-bottom: 1px solid #ccc; text-align: left;">
          <th style="padding: 6px 12px; width: 50%;">Name</th>
          <th style="padding: 6px 12px; width: 20%;">Group</th>
          <th style="padding: 6px 12px; width: 15%;">Connections</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
`;

table.querySelector("tbody").innerHTML = tableDataSliced.map(d => `
  <tr style="border-bottom: 0.5px solid #eee;">
    <td style="padding:6px 12px;"><a href="https://www.data.gv.at/${d.group}s/${d.id}/" target="_blank">${stripTitlePrefix(d.title)}</a></td>
    <td style="padding:6px 12px;">${d.group}</td>
    <td style="padding:6px 12px;">${d.connections}</td>
  </tr>
`).join("");

display(table);
```

```js
// Similarity measure Slider
const similarityMeasureInput = Inputs.radio(["Shared Connections", "Jaccard Similarity"], {value: "Shared Connections", label: "Similarity Measure"});
const similarityMeasure = view(similarityMeasureInput);
```

```js
similarityMeasureInput.style.display = clickedNode !== null ? null : "none";  // only show when a node is clicked
```

```js
// Compute similarity table data when a node is clicked
const similarityData = clickedNode === null ? [] : (() => {
  const sourceNeighbours = adjacency.get(clickedNode.id) || new Set();
  
  return nodes
    .filter(n => n.group === clickedNode.group && n.id !== clickedNode.id)
    .map(n => {
      const candidateNeighbours = adjacency.get(n.id) || new Set();
      const shared = [...sourceNeighbours].filter(id => candidateNeighbours.has(id)).length;
      const union = new Set([...sourceNeighbours, ...candidateNeighbours]).size;
      const jaccard = union === 0 ? 0 : shared / union;
      return { ...n, shared, jaccard };
    })
    .filter(n => n.shared > 0)
    .sort((a, b) => similarityMeasure === "Jaccard Similarity"
      ? b.jaccard - a.jaccard
      : b.shared - a.shared
    )
    .slice(0, tableEntries);
})();
```

```js
// Similarity table
const groupPath = { "Dataset": "datasets", "Application": "applications" };  // more robust links

if (clickedNode !== null && similarityData.length > 0) {

  const similarTable = html`
    <p><strong>Top ${tableEntries} ${clickedNode.group}s</strong> most similar to <strong>${stripTitlePrefix(clickedNode.title)}</strong> ranked by ${similarityMeasure}.</p>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
      <thead>
        <tr style="border-bottom: 1px solid #ccc; text-align: left;">
          <th style="padding: 6px 12px;">Name</th>
          <th style="padding: 6px 12px;">Shared Connections</th>
          <th style="padding: 6px 12px;">Jaccard Similarity</th>
          <th style="padding: 6px 12px;">Total Connections</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  `;

  similarTable.querySelector("tbody").innerHTML = similarityData.map(d => `
    <tr style="border-bottom: 0.5px solid #eee;">
      <td style="padding: 6px 12px;"><a href="https://www.data.gv.at/${groupPath[d.group]}/${d.id}/" target="_blank">${stripTitlePrefix(d.title)}</a></td>
      <td style="padding: 6px 12px;">${d.shared}</td>
      <td style="padding: 6px 12px;">${d.jaccard.toFixed(3)}</td>
      <td style="padding: 6px 12px;">${d.connections}</td>
    </tr>
  `).join("");

  display(similarTable);
} else {
  display(html`<span></span>`);
}
```