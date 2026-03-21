---
title: PW
sql:
    formattedNodes: ./data/formattedNodes.csv
    formattedLinks: ./data/formattedLinks.csv
---

<!-- Data Loading / Display -->

```sql id=Nodes display
SELECT id, title, "group", connections
FROM formattedNodes
```

```sql id=Links display
SELECT source, "target", value
FROM formattedLinks
```

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
    .on("mouseover", mouseover)  // event handlers
    .on("mouseout", mouseout)
    .on("click", click)

node.append("title").text(d => `${d.title}\nConnections: ${d.connections}`) // append titles

// Force Simulation
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id))
  .force("charge", d3.forceManyBody().strength(-50))
  .force("x", d3.forceX().strength(0.1))
  .force("y", d3.forceY().strength(0.15))
  .force("collide", d3.forceCollide(d => radiusScale(d.connections) + 1))
  .alphaDecay(0.03)

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
const getId = x => typeof x === "object" ? x.id : x;  // ID helper (also used in update cell)

nodes.forEach(n => adjacency.set(n.id, new Set()))

links.forEach(l => {
  const s = getId(l.source)
  const t = getId(l.target)
  adjacency.get(s).add(t)
  adjacency.get(t).add(s)
})


// Highlight/Reset helper functions
let clicked = null;

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
      l.source.id === d.id || l.target.id === d.id ? 2 : 1  // same for link stroke width
    );
}

function reset() {
  node.attr("opacity", 1);  // reset node opacity
  link.attr("opacity", 1).attr("stroke-width", 1);  // reset link opacity and stroke width
  clicked = null;
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
  if (clicked && clicked.id === d.id) {  // if a node is clicked twice -> reset graph view
    reset();  
  } else {  // if no node is clicked -> highlight correct nodes
    clicked = d;  // assign clicked to deactivate mouseover/mouseout
    highlight(d);
  }
}

// Display the graph
display(svg.node())
```

<!-- Update Cell (avoid reloading the graph) -->

```js
const visibleDatasets = new Set();
const visibleNodes = new Set();

// Keep dataset nodes with enough connections
nodes.forEach(n => {
  if (n.group === "Dataset" && n.connections >= minConnections) {
    visibleDatasets.add(n.id);
  }
});

// Add applications directly connected to the dataset nodes
visibleDatasets.forEach(id => {
  visibleNodes.add(id);
  adjacency.get(id)?.forEach(neighbourId => visibleNodes.add(neighbourId));
});

// Toggle node visibility
node.style("display", n => visibleNodes.has(n.id) ? null : "none");

// Toggle link visibility
link.style("display", l => {
  const source = getId(l.source);
  const target = getId(l.target);
  return visibleNodes.has(source) && visibleNodes.has(target) ? null : "none";
});
```