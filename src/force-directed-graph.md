# Force-Directed Graph

```js
const datasets = FileAttachment("ogdmetadatendatagvatsimple.xlsx").xlsx()
```

```js
const datasetsData = datasets.sheet(0, {
    headers: true,
    range: "A1:AF26967"
  })
```

### Datasets
```js
Inputs.table(datasetsData)
```

```js
const applications = FileAttachment("applications.xlsx").xlsx()
```

```js
const applicationsData = applications.sheet(0, {
    headers: true,
    // range: "A1:J10"
  })
```

### Applications
```js
Inputs.table(applicationsData)
```

```js
function reduceData (applicationsData){
  return applicationsData.flatMap(item => ({
    "ID": item["id"],
    "Titel": item["title"],
    "Datasets": item["string_agg"].replace(/[\[\]\\"]/g, '')
  }));
}
```

```js
const reducedData = reduceData(applicationsData)
```

```js
function expandData (reducedData) {
  const expandedData = [];
  reducedData.filter(item => item.Datasets.length > 0).forEach(item => {
    const datasets = item.Datasets.split(',').map(dataset => dataset.trim());
    datasets.forEach(dataset => {
      expandedData.push({
        ID: item.ID,
        Titel: item.Titel,
        Dataset: dataset
      });
    });
  });
  return expandedData
}
```

```js
const expandedData = expandData(reducedData)
```

### Combined Dataset
```js
Inputs.table(expandedData)
```

```js
function formatData(expandedData, datasetsData) {
  const nodesMap = new Map();
  const links = [];
  const datasetMap = new Map(datasetsData.map(ds => [ds["Eindeutiger Identifikator"], ds]));

  expandedData.forEach(item => {
    if (!nodesMap.has(item.ID)) {
      nodesMap.set(item.ID, {
        id: item.ID,
        group: "Application",
        title: `Anwendung: ${item.Titel}`,
        connections: 0
      });
    }
    nodesMap.get(item.ID).connections += 1;

    if (!nodesMap.has(item.Dataset)) {
      const datasetMatch = datasetMap.get(item.Dataset);
      nodesMap.set(item.Dataset, {
        id: item.Dataset,
        group: "Dataset",
        title: `Datensatz: ${datasetMatch ? datasetMatch.Titel : null}`,
        connections: 0
      });
    }
    nodesMap.get(item.Dataset).connections += 1;
  });

  const nodes = Array.from(nodesMap.values())
    .filter(node => node.connections >= 1);
  const filteredNodeIds = new Set(nodes.map(node => node.id));

  // Old minVerbindungen filter; renders graph anew each time minVerbindungen is changed
  /*const nodes = Array.from(nodesMap.values())
    .filter(node => !(node.group === "Dataset" && node.connections < minVerbindungen))
    .filter(node => !(node.group === "Application" && node.connections < 1));
  const filteredNodeIds = new Set(nodes.map(node => node.id));*/ 
  
  expandedData.forEach(item => {
    if (filteredNodeIds.has(item.ID) && filteredNodeIds.has(item.Dataset)) {
      links.push({
        source: item.ID,
        target: item.Dataset,
        value: 1
      });
    }
  });

  return { nodes, links };
}
```

### Formatted Nodes
```js
const formattedData = formatData(expandedData, datasetsData)
```

```js
Inputs.table(formattedData.nodes)
```

### Formatted Links
```js
Inputs.table(formattedData.links)
```

```js
const minVerbindungen = view(Inputs.range([1, 10], {value: 1, step: 1, label: "Min. verbundene Applikationen"}))
```

```js
  // Initial width and height; they will be adjusted dynamically
  let width = 1800;
  let height = 1200;

  // Specify the color scale.
  const color = d3.scaleOrdinal(d3.schemeCategory10);

  // The force simulation mutates links and nodes, so create a copy
  const links = formattedData.links.map(d => ({ ...d }));
  const nodes = formattedData.nodes.map(d => ({ ...d }));
  
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


  // Filter out "dataset" nodes with fewer connections than minVerbindungen
  const visibleDatasets = nodes.filter(d => d.group === "Dataset" && d.connections >= minVerbindungen);
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