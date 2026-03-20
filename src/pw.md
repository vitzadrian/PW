---
title: PW
sql:
    formattedNodes: ./data/formattedNodes.csv
    formattedLinks: ./data/formattedLinks.csv
---

```sql id=Nodes display
SELECT id, title, "group", connections
FROM formattedNodes
```

```sql id=Links display
SELECT source, "target", value
FROM formattedLinks
```


```js
const minConnections = view(Inputs.range([1, 10], {value: 1, step: 1, label: "Min. connected Apps"}))
```

```js
const width = 1800
const height = 1200

// Copy data because simulation mutates objects
const nodes = Nodes.toArray().map(d => ({...d}))
const links = Links.toArray().map(d => ({...d}))

const color = d3.scaleOrdinal(d3.schemeCategory10)

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
      .on("mouseover", mouseover)
      .on("mouseout", mouseout)
      .on("click", click)

node.append("title")
  .text(d => `${d.title}\nVerbindungen: ${d.connections}`)

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id))
  .force("charge", d3.forceManyBody().strength(-50))
  .force("x", d3.forceX().strength(0.1))
  .force("y", d3.forceY().strength(0.15))
  .force("collide", d3.forceCollide(d => radiusScale(d.connections) + 1))

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

nodes.forEach(n => adjacency.set(n.id, new Set()))

links.forEach(l => {
  const s = typeof l.source === "object" ? l.source.id : l.source
  const t = typeof l.target === "object" ? l.target.id : l.target
  adjacency.get(s).add(t)
  adjacency.get(t).add(s)
})

const degree = new Map([...adjacency].map(([id,set]) => [id,set.size]))


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
    clicked = null;
    reset();  
  } else {  // if no node is clicked -> highlight correct nodes
    clicked = d;  // assign clicked to deactivate mouseover/mouseout
    highlight(d);
  }
}

display(svg.node())
```

<!-- Simple Mouseover/Mouseout functions (not possible with click?)
function mouseover(event, d) {  // on mouseover
  node.attr("opacity", function(n) {  // set opacity of
    return (n === d ||  // the hovered node
      links.some(l => (l.source === n || l.target === n) && (l.source === d || l.target === d)  // and all directly connected nodes
    )) ? 1 : 0.1  // to 1, all others to 0.1     
  });
  link.attr("opacity", function(l) {
    return (l.source === d || l.target === d) ? 1 : 0.2  // same for all connected links
  });
  link.attr("stroke-width", function (l) {
    return (l.source === d || l.target === d) ? 2 : 1  // increase link width for further highlighting
  });
};

function mouseout(event, d) {  // on mouseout
  node.attr("opacity", 1);  // reset all node
  link.attr("opacity", 1)  // and link opacities
}
-->


<!-- Update cell to avoid reloading graph (also use adjacency map?) -->
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
links.forEach(l => {
  const s = typeof l.source === "object" ? l.source.id : l.source;
  const t = typeof l.target === "object" ? l.target.id : l.target;
  if (visibleDatasets.has(s) || visibleDatasets.has(t)) {
    visibleNodes.add(s);
    visibleNodes.add(t);
  }
});

// Toggle node visibility
node.style("display", d => visibleNodes.has(d.id) ? null : "none");

// Toggle link visibility
link.style("display", d => {
  const s = typeof d.source === "object" ? d.source.id : d.source;
  const t = typeof d.target === "object" ? d.target.id : d.target;
  return visibleNodes.has(s) && visibleNodes.has(t) ? null : "none";
});
```
