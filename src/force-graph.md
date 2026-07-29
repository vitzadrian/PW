---
sql:
    formattedNodes: data/graph/formattedNodes.csv
    formattedLinks: data/graph/formattedLinks.csv
---



<style>
.observablehq input[type="range"] {
  accent-color: var(--theme-foreground-focus);
}
</style>


<!-- Data Loading / Tables -->

```sql id=Nodes
SELECT id, title, "group", connections
FROM formattedNodes
```

```sql id=Links
SELECT source, "target", value
FROM formattedLinks
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

<!-- Slider Cells -->

<div class="grid grid-cols-2">
  <div>

```js
const minConnections = view(Inputs.range([1, 10], {value: 1, step: 1, label: "Connected Apps"}))
```

  </div>
  <div>

```js
const tableEntriesInput = Inputs.range([1, 20], {value: 5, step: 1, label: "Number of Rows"});
const tableEntries = view(tableEntriesInput);
```

  </div>
</div>


<!-- Table Cells (Data/Display) -->

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
// Helper Cell (group path and table builder)
const groupPath = { "Dataset": "datasets", "Application": "applications" };
const stripTitlePrefix = title => title.replace(/^(Dataset|Application): /, "");

function buildTable(titleHtml, columns, rows) {
  const table = html`
    <div style="overflow-x: auto; max-height: 400px; overflow-y: auto;">
      <p style="display: block; min-width: 100%">${titleHtml}</p>
      <table style="width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; min-width: 100%;">
        <thead><tr style="border-bottom: 1px solid #ccc; text-align: left;"></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  `;
  table.querySelector("thead tr").innerHTML = columns.map(c =>
    `<th style="padding: 6px 12px; width: ${c.width};">${c.label}</th>`
  ).join("");
  table.querySelector("tbody").innerHTML = rows;
  return table;
}
```

```js
// Connected Nodes Table
const tableDataSliced = tableData.slice(0, Math.min(tableEntries, tableData.length));

const displayedEntries = tableDataSliced.length;

const tableTitle = clickedNode === null
  ? `Top ${displayedEntries} Datasets`
  : clickedNode.group === "Dataset"
    ? `Top ${displayedEntries} Applications linked to ${clickedNode.title}`
    : `Top ${displayedEntries} Datasets linked to ${clickedNode.title}`;

const connectedNodesGroup = clickedNode === null
  ? "Application" : clickedNode.group;

display(buildTable(
  html`<strong>${tableTitle}</strong> ranked by number of connected ${connectedNodesGroup}s.`,
  [
    { label: "Name", width: "80%" },
    { label: "Group", width: "10%" },
    { label: "Connections", width: "10%" }
  ],
  tableDataSliced.map(d => `
    <tr style="border-bottom: 0.5px solid #eee;">
      <td style="padding: 6px 12px; max-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
        <a href="https://www.data.gv.at/${groupPath[d.group]}/${d.id}/" target="_blank" title="${stripTitlePrefix(d.title)}">${stripTitlePrefix(d.title)}</a></td>
      <td style="padding: 6px 12px;">${d.group}</td>
      <td style="padding: 6px 12px;">${d.connections}</td>
    </tr>
  `).join("")
));
```

```js
// Similarity Measure Radio
const similarityMeasureInput = Inputs.radio(["Jaccard Similarity", "Shared Connections"], {value: "Jaccard Similarity", label: "Similarity Measure"});
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
// Similarity Table
if (clickedNode !== null && similarityData.length > 0) {
  display(buildTable(
    html`<strong>Top ${tableEntries} ${clickedNode.group}s</strong> most similar to <strong>${stripTitlePrefix(clickedNode.title)}</strong> ranked by ${similarityMeasure}.`,
    [
      { label: "Name", width: "70%" },
      { label: "Jaccard", width: "10%" },
      { label: "Shared", width: "10%" },
      { label: "Total", width: "10%" }
    ],
    similarityData.map(d => `
      <tr style="border-bottom: 0.5px solid #eee;">
        <td style="padding: 6px 12px; max-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
          <a href="https://www.data.gv.at/${groupPath[d.group]}/${d.id}/" target="_blank" title="${stripTitlePrefix(d.title)}">${stripTitlePrefix(d.title)}</a></td>
        <td style="padding: 6px 12px;">${d.jaccard.toFixed(3)}</td>
        <td style="padding: 6px 12px;">${d.shared}</td>
        <td style="padding: 6px 12px;">${d.connections}</td>
      </tr>
    `).join("")
  ));
} else {
  display(html`<span></span>`);
}
```
