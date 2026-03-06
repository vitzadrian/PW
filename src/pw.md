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
`
Original avg:  ${avgOriginal.toFixed(4)} ms
Optimized avg: ${avgOptimized.toFixed(4)} ms
Speedup:       ${(avgOriginal / avgOptimized).toFixed(2)}x

Nodes: ${nodesA.length}
Links: ${linksA.length}
`
```

```js
const minConnections = view(Inputs.range([1, 10], {value: 1, step: 1, label: "Min. connected Apps"}))
```


```js
  // Force-Directed-Graph
  let width = 1800;
  let height = 1200;

  // The force simulation mutates links and nodes, so create a copy
  const nodes = Nodes.toArray().map(d => ({ ...d }));
  const links = Links.toArray().map(d => ({ ...d }));

  // Colors
  const color = d3.scaleOrdinal(d3.schemeCategory10);

  // Define a scale for the node radius based on the degree
  const radiusScale = d3.scaleLinear()
    .domain(d3.extent(nodes, d => d.connections)) // Get the min and max degree
    .range([5, 25]); // Define the min and max radius size

  // Create a simulation with several forces.
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id))
    .force("charge", d3.forceManyBody().strength(-50))  
    .force("x", d3.forceX().strength(0.1))  
    .force("y", d3.forceY().strength(0.15))  
    .force("collide", d3.forceCollide(d => radiusScale(d.connections) + 1)); 

  // Create the SVG container.
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [-width / 2, -height / 2, width, height])
    .attr("style", "max-width: 100%; height: auto;");

  const link = svg.append("g")
    .attr("stroke", "#999")
    .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke-width", d => Math.sqrt(d.value));

  const node = svg.append("g")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", d => radiusScale(d.connections))
    .attr("fill", d => color(d.group))
    .attr("opacity", 1)
      .on("mouseover", mouseover)
      .on("mouseout", mouseout)
      .on("click", click);
  
  node.append("title")
    .text(d => `${d.title}\nVerbindungen: ${d.connections}`);

  // Set the position attributes of links and nodes each time the simulation ticks.
  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);
    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);
  });


  // Filter out "dataset" nodes with fewer connections than minConnections
  const visibleDatasets = nodes.filter(d => d.group === "Dataset" && d.connections >= minConnections);
  // Create a set of IDs of visible dataset nodes
  const visibleDatasetIds = new Set(visibleDatasets.map(d => d.id));
  // Determine which links are visible based on the visible nodes
  const visibleLinks = links.filter(d => visibleDatasetIds.has(d.source.id) || visibleDatasetIds.has(d.target.id));
  // Create a set of IDs of nodes that are involved in visible links
  const visibleLinkIds = new Set(visibleLinks.flatMap(d => [d.source.id, d.target.id]));
  // Determine which nodes are visible based on the visible links
  const visibleNodes = nodes.filter(d => visibleLinkIds.has(d.id));


  function showNodesAndLinks() {
    // Update node visibility
    node.attr("opacity", d => visibleNodes.includes(d) ? 1 : 0);
    // Update link visibility
    link.attr("opacity", d => visibleLinks.includes(d) ? 1 : 0);
  }
  
  let selectedNode = null


  function highlightNodesAndLinks(nodeToHighlight) {
    if (nodeToHighlight === null){
      showNodesAndLinks();
    }
    else {
      node.attr("opacity", function(n) {
        return (n === nodeToHighlight ||
          links.some(l =>
            (l.source === n || l.target === n) &&
            (l.source === nodeToHighlight || l.target === nodeToHighlight)
          )
        ) ? 1 : (visibleNodes.includes(n) ? 0.1 : 0);
      });

      link.attr("opacity", function(l) {
        return (l.source === nodeToHighlight || l.target === nodeToHighlight) ? 1 : (visibleLinks.includes(l) ? 0.1 : 0);
      });

      link.attr("stroke-width", function (l) {
        return (l.source === nodeToHighlight || l.target === nodeToHighlight) ? 2 : (visibleLinks.includes(l) ? 0.6 : 0);
      });
    }  
  };


  function mouseover(event, d) {
    const opacity = +d3.select(event.currentTarget).style("opacity");
    if (opacity > 0 && selectedNode == null) {
      highlightNodesAndLinks(d);
//      console.log("opacity:", opacity); 
    }
  };

  const rect = svg.append("rect")
    .attr("width", width)
    .attr("height", height)
    .attr("fill", "transparent")
    .lower() // put behind nodes
    .on("click", click);

  function mouseout(event, d) {
    const opacity = +d3.select(event.currentTarget).style("opacity");
    if (opacity > 0 && selectedNode == null) {
      highlightNodesAndLinks(null); 
    }
  };

  function click(event, d) {
    const opacity = +d3.select(event.currentTarget).style("opacity");
    if (opacity > 0 && selectedNode === d) {
      // If the same node is clicked again, reset the view
      selectedNode = null;
    } else if (selectedNode === d && event.currentTarget === rect){
      selectedNode = null;
    } else {
      // Clear previous selection
      selectedNode = d;
    }
    
    // Highlight nodes and links based on the new selection
    highlightNodesAndLinks(selectedNode);
  };

  // When this cell is re-run, stop the previous simulation.
  invalidation.then(() => simulation.stop());

  const DisjointForcegraph = display(svg.node());
```

```js
// Data Prep Experiment
const nodesA = Nodes.toArray().map(d => ({ ...d }));
const linksA = Links.toArray().map(d => ({ ...d }));

const nodesB = Nodes.toArray().map(d => ({ ...d }));
const linksB = Links.toArray().map(d => ({ ...d }));

const testNode = nodesA[Math.floor(nodesA.length / 2)];


// original

function highlightOriginal(nodeToHighlight) {
  nodesA.forEach(n => {
    linksA.some(l =>
      (l.source === n || l.target === n) &&
      (l.source === nodeToHighlight || l.target === nodeToHighlight)
    );
  });

  linksA.forEach(l => {
    l.source === nodeToHighlight ||
    l.target === nodeToHighlight;
  });
}


// optimized

const adjacency = new Map();
nodesB.forEach(n => adjacency.set(n.id, new Set()));

linksB.forEach(l => {
  if (!adjacency.has(l.source)) adjacency.set(l.source, new Set());
  if (!adjacency.has(l.target)) adjacency.set(l.target, new Set());

  adjacency.get(l.source).add(l.target);
  adjacency.get(l.target).add(l.source);
});

function highlightOptimized(nodeToHighlight) {
  const neighbors = adjacency.get(nodeToHighlight.id) || new Set();

  nodesB.forEach(n => {
    n.id === nodeToHighlight.id ||
    neighbors.has(n.id);
  });

  linksB.forEach(l => {
    l.source === nodeToHighlight.id ||
    l.target === nodeToHighlight.id;
  });
}


// benchmark attempt

function benchmark(fn, iterations = 300) {
  const t0 = performance.now();
  for (let i = 0; i < iterations; i++) {
    fn(testNode);
  }
  const t1 = performance.now();
  return (t1 - t0) / iterations;
}

const avgOriginal = benchmark(highlightOriginal);
const avgOptimized = benchmark(highlightOptimized);

`
Original avg:  ${avgOriginal.toFixed(4)} ms
Optimized avg: ${avgOptimized.toFixed(4)} ms
Speedup:       ${(avgOriginal / avgOptimized).toFixed(2)}x

Nodes: ${nodesA.length}
Links: ${linksA.length}
`
```


<!-- Vorkurzem copy pasted chatgpt version (noch nicht genauer angeschaut)

```js
// --- Dimensions ---
const width = 1800;
const height = 1200;

// --- Data ---
const nodes = Nodes.toArray().map(d => ({ ...d }));
const links = Links.toArray().map(d => ({ ...d }));

// --- Color ---
const color = d3.scaleOrdinal(d3.schemeCategory10);

// --- Radius scale ---
const radiusScale = d3.scaleLinear()
  .domain(d3.extent(nodes, d => d.connections))
  .range([5, 25]);

// --- Precompute adjacency map for fast highlight ---
const adjacency = new Map();
nodes.forEach(n => adjacency.set(n.id, new Set()));

links.forEach(l => {
  adjacency.get(l.source)?.add(l.target);
  adjacency.get(l.target)?.add(l.source);
});

// --- Simulation ---
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id))
  .force("charge", d3.forceManyBody().strength(-50))
  .force("x", d3.forceX().strength(0.1))
  .force("y", d3.forceY().strength(0.15))
  .force("collide", d3.forceCollide(d => radiusScale(d.connections) + 1));

// --- SVG ---
const svg = d3.create("svg")
  .attr("viewBox", [-width / 2, -height / 2, width, height])
  .attr("style", "max-width: 100%; height: auto;");

// --- Links ---
const link = svg.append("g")
  .attr("stroke", "#999")
  .attr("stroke-opacity", 0.6)
  .selectAll("line")
  .data(links)
  .join("line")
  .attr("stroke-width", d => Math.sqrt(d.value));

// --- Nodes ---
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
  .on("click", click);

node.append("title")
  .text(d => `${d.title}\nVerbindungen: ${d.connections}`);

// --- Tick update ---
simulation.on("tick", () => {
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);
});

// --- Visibility Filtering (FAST via Sets) ---
const visibleDatasetIds = new Set(
  nodes
    .filter(d => d.group === "Dataset" && d.connections >= minConnections)
    .map(d => d.id)
);

const visibleLinks = links.filter(l =>
  visibleDatasetIds.has(l.source.id) ||
  visibleDatasetIds.has(l.target.id)
);

const visibleNodeIds = new Set(
  visibleLinks.flatMap(l => [l.source.id, l.target.id])
);

// --- Visibility Update ---
function showNodesAndLinks() {
  node.attr("opacity", d => visibleNodeIds.has(d.id) ? 1 : 0);
  link.attr("opacity", d =>
    visibleDatasetIds.has(d.source.id) ||
    visibleDatasetIds.has(d.target.id) ? 1 : 0
  );
}

let selectedNode = null;

// --- Optimized Highlight ---
function highlightNodesAndLinks(d) {
  if (!d) {
    showNodesAndLinks();
    link.attr("stroke-width", l => Math.sqrt(l.value));
    return;
  }

  const neighbors = adjacency.get(d.id) || new Set();

  node.attr("opacity", n => {
    if (!visibleNodeIds.has(n.id)) return 0;
    return (n.id === d.id || neighbors.has(n.id)) ? 1 : 0.1;
  });

  link
    .attr("opacity", l =>
      (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1
    )
    .attr("stroke-width", l =>
      (l.source.id === d.id || l.target.id === d.id) ? 2 : 0.6
    );
}

// --- Interaction ---
function mouseover(event, d) {
  if (!selectedNode) highlightNodesAndLinks(d);
}

function mouseout() {
  if (!selectedNode) highlightNodesAndLinks(null);
}

const rect = svg.append("rect")
  .attr("width", width)
  .attr("height", height)
  .attr("fill", "transparent")
  .lower()
  .on("click", click);

function click(event, d) {
  selectedNode = selectedNode === d ? null : d;
  highlightNodesAndLinks(selectedNode);
}

// --- Cleanup ---
invalidation.then(() => simulation.stop());

display(svg.node());
```
-->