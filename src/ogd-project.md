# OGD Base Projekt

```js echo
const datasets = FileAttachment("ogdmetadatendatagvatsimple.xlsx").xlsx()
```

```js echo
const datasetsData = datasets.sheet(0, {
    headers: true,
    range: "A1:AF26967"
  })
```

```js
Inputs.table(datasetsData)
```

```js echo
const applications = FileAttachment("applications.xlsx").xlsx()
```

```js echo
const applicationsData = applications.sheet(0, {
    headers: true,
    // range: "A1:J10"
  })
```

```js
Inputs.table(applicationsData)
```

## Zoomable Treemap

### Data Transformation

```js echo
const datasetsDataSimple = datasetsData.flatMap(item => ({
  "Fortlaufende Nummer": item["Fortlaufende Nummer"],
  "Eindeutiger Identifikator": item["Eindeutiger Identifikator"],
  "Titel": item["Titel"],
  "Kategorie": (item["Kategorie(n)"] || "Unbekannte Kategorie").split(";")[0].trim() || "Unbekannte Kategorie",
  "Kategorien": (item["Kategorie(n)"] || "Unbekannte Kategorie").split(";")[1] || "Keine Unterkategorie",
  "Veröffentlichende Stelle": item["Veröffentlichende Stelle"] || "Unbekannte Stelle",
  "Beschreibung": item["Beschreibung"] || "Keine Beschreibung",
  "Schlagworte": item["Schlagworte"] || "Keine Schlagworte",
  "Lizenz": item["Lizenz"] || "Unbekannte Lizenz",
  "Datum": item["Zeitliche Ausdehnung (Anfang)"] || "Unbekanntes Datum"
}));
```

```js
Inputs.table(datasetsDataSimple)
```

```js echo
// List of possible groups (zoom in once)
const treemapGroups = ["Lizenz", "Veröffentlichende Stelle"]
```

```js echo
// List of possible subgroups (zoom in twice)
const treemapSubgroups = ["Datum", "Lizenz", "Schlagworte", "Veröffentlichende Stelle"]
```

```js echo
// Transform data into necessary structure for treemap
function transformToHierarchical(data, group, subgroup) {

  // Pre-Rendering Category Filter
  const filteredData = data.filter(item => treemapCategoriesIncluded.includes(item["Kategorie"]))
  
  // Group data by "Kategorie"
  const categories = d3.group(filteredData, d => d["Kategorie"]);
  
  // Create hierarchical structure
  const hierarchicalData = {
    name: "Datasets",
    children: Array.from(categories, ([key, values]) => {
      
      // Group by selected group
      const groups = d3.group(values, d => d[group]);

      return {
        name: key,
        children: Array.from(groups, ([subKey, subValues]) => {
          
          // Group by selected subgroup
          const subgroups = d3.group(subValues, d => d[subgroup]);
          
          return {
            name: subKey,
            children: Array.from(subgroups, ([subSubKey, subSubValues]) => {

              // Group by identifier to get unique nodes
              const subSubGroups = d3.group(subSubValues, d => d["Eindeutiger Identifikator"]);

              return {
                name: subSubKey,
                children: Array.from(subSubGroups, ([subSubSubKey, subSubSubValues]) => {

                  // Create 
                  const subSubSubGroups = d3.group(subSubSubValues, d => d["Eindeutiger Identifikator"]);

                  return {
                    name: subSubSubValues[0]["Titel"],
                    children: Array.from(subSubSubGroups, ([subSubSubSubKey, subSubSubSubValues]) => ({  
                      name: subSubSubSubValues[0]["Eindeutiger Identifikator"],
                      value: subSubSubSubValues.length,
                    })),
                    license: subSubSubValues[0]["Lizenz"],
                    description: subSubSubValues[0]["Beschreibung"],
                    release_date: subSubSubValues[0]["Datum"],
                  };
                })
              }; 
            })
          };
        })
      };
    })
  };

  return hierarchicalData;
}
```

```js echo
const treemapData = transformToHierarchical(datasetsDataSimple, treemapGroup, treemapSubgroup)
```

### Color Scale

```js echo
// Get categories present in data
function getCategories(dataset, column) {
  return [...d3.rollup(dataset, v => v.length, d => d[column])]
    .sort((a, b) => b[1] - a[1]) // Sort by the counts in descending order
    .map(d => d[0]); 
}
```

```js echo
const categories = getCategories(datasetsDataSimple, "Kategorie")
```

```js echo
// data.gv.at logo colors as HEX color codes (5 colors * 3 opacity levels)
const colorsHEX = ["#00A3E5", "#86BC24", "#F07D00", "#E6177B", "#E30613",
         "#66C8EF", "#B6D77C", "#F6B166", "#F074B0", "#EE6A71",
         "#CCEDFA", "#E7F2D3", "#FCE5CC", "#FAD1E5", "#F9CDD"]
```

```js echo
// data.gv.at logo colors as RGB color codes (5 colors * 3 opacity levels)
const colorsRGB = ["rgb(0, 163, 229)", "rgb(134, 188, 36)", "rgb(240, 125, 0)", "rgb(230, 23, 123)", "rgb(227, 6, 19)",
          "rgba(0, 163, 229, 0.8)", "rgba(134, 188, 36, 0.8)", "rgba(240, 125, 0, 0.8)", "rgba(230, 23, 123, 0.8)", "rgba(227, 6, 19, 0.8)",
          "rgba(0, 163, 229, 0.6)", "rgba(134, 188, 36, 0.6)", "rgba(240, 125, 0, 0.6)", "rgba(230, 23, 123, 0.6)", "rgba(227, 6, 19, 0.6)"]
```

```js echo
// Match categories to colors
const colorScale = d3.scaleOrdinal()
  .domain(categories)
  .range(colorsHEX);
```

### Images

```js echo
const images = await Promise.all([
  FileAttachment("econ.png").url(),
  FileAttachment("envi.png").url(),
  FileAttachment("regi.png").url(),
  FileAttachment("soci.png").url(),
  FileAttachment("gove.png").url(), 
  FileAttachment("tran.png").url(),
  FileAttachment("educ.png").url(),
  FileAttachment("agri.png").url(),
  FileAttachment("heal.png").url(),
  FileAttachment("unbe.png").url(),
  FileAttachment("ener.png").url(),
  FileAttachment("just.png").url(),
  FileAttachment("tech.png").url(),
  FileAttachment("intr.png").url()
]);
```

```js echo
const imageCategoryMap = new Map(
  categories.map((category, index) => [category, images[index]])
);
```

### Legend

```js echo
// Copyright 2021, Observable Inc.
// Released under the ISC license.
// https://observablehq.com/@d3/color-legend
function Swatches(color, {
  columns = null,
  format,
  unknown: formatUnknown,
  swatchSize = 15,
  swatchWidth = swatchSize,
  swatchHeight = swatchSize,
  marginLeft = 0
} = {}) {
  const id = `-swatches-${Math.random().toString(16).slice(2)}`;
  const unknown = formatUnknown == null ? undefined : color.unknown();
  const unknowns = unknown == null || unknown === d3.scaleImplicit ? [] : [unknown];
  const domain = color.domain().concat(unknowns);
  if (format === undefined) format = x => x === unknown ? formatUnknown : x;

  function entity(character) {
    return `&#${character.charCodeAt(0).toString()};`;
  }

  if (columns !== null) return htl.html`<div style="display: flex; align-items: center; margin-left: ${+marginLeft}px; min-height: 33px; font: 10px sans-serif;">
  <style>

.${id}-item {
  break-inside: avoid;
  display: flex;
  align-items: center;
  padding-bottom: 1px;
}

.${id}-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: calc(100% - ${+swatchWidth}px - 0.5em);
}

.${id}-swatch {
  width: ${+swatchWidth}px;
  height: ${+swatchHeight}px;
  margin: 0 0.5em 0 0;
}

  </style>
  <div style=${{width: "100%", columns}}>${domain.map(value => {
    const label = `${format(value)}`;
    return htl.html`<div class=${id}-item>
      <div class=${id}-swatch style=${{background: color(value)}}></div>
      <div class=${id}-label title=${label}>${label}</div>
    </div>`;
  })}
  </div>
</div>`;

  return htl.html`<div style="display: flex; align-items: center; min-height: 33px; margin-left: ${+marginLeft}px; font: 10px sans-serif;">
  <style>

.${id} {
  display: inline-flex;
  align-items: center;
  margin-right: 1em;
}

.${id}::before {
  content: "";
  width: ${+swatchWidth}px;
  height: ${+swatchHeight}px;
  margin-right: 0.5em;
  background: var(--color);
}

  </style>
  <div>${domain.map(value => htl.html`<span class="${id}" style="--color: ${color(value)}">${format(value)}</span>`)}</div>`;
}
```

```js echo
function updateLegend(selectedCategories) {
  // Filter the color scale based on the selected categories
  const filteredCategories = categories.filter(category => selectedCategories.includes(category));

  // Create a new scale for the filtered categories
  const filteredColorScale = d3.scaleOrdinal()
    .domain(filteredCategories)
    .range(filteredCategories.map(category => colorScale(category))); // Ensure the same colors

  // Update the legend using Swatches or any other method you prefer
  return Swatches(filteredColorScale, { columns: "180px" });
}
```

```js echo
updateLegend(treemapCategoriesIncluded);
```

### Filters

```js
const treemapGroup = view(Inputs.radio(
  treemapGroups,
  {value: "Veröffentlichende Stelle", label: "Gruppe"}
))
```

```js
const treemapSubgroup = view(Inputs.radio(
  treemapSubgroups.filter(category => category !== treemapGroup), 
  {value: ["Schlagworte", "Veröffentlichende Stelle"].find(category => category !== treemapGroup), label: "Untergruppe"}
))
```

```js
const treemapCategoriesIncluded = view(Inputs.checkbox(
  (function() {
    return getCategories(datasetsDataSimple, "Kategorie");
  })(),
  {
    // Set initial value to all categories (or a default value)
    value: getCategories(datasetsDataSimple, "Kategorie"),
    label: "Kategorien"
  }
))
```

```js
const treemapMode = view(Inputs.radio(
  new Map([["Binary", d3.treemapBinary], ["Squarify", d3.treemapSquarify]]),
  {label: "Layout", value: d3.treemapBinary}
))
```

```js
// Specify chart dimensions
const width = 1000;
const height = 800;

// This custom tiling function adapts the built-in binary/squarify tiling 
// function for the appropriate aspect ratio when the treemap is zoomed-in.
function tile(node, x0, y0, x1, y1) {
  treemapMode(node, 0, 0, width, height);
  for (const child of node.children) {
    child.x0 = x0 + child.x0 / width * (x1 - x0);
    child.x1 = x0 + child.x1 / width * (x1 - x0);
    child.y0 = y0 + child.y0 / height * (y1 - y0);
    child.y1 = y0 + child.y1 / height * (y1 - y0);
  }
}

// Compute the layout
const hierarchy = d3.hierarchy(treemapData)
  .sum(d => d.value)
  .sort((a, b) => b.value - a.value);
const root = d3.treemap().tile(tile)(hierarchy);

// Create the scales
const x = d3.scaleLinear().rangeRound([0, width]);
const y = d3.scaleLinear().rangeRound([0, height]);

// Formatting utilities
const format = d3.format(",d");
const name = d => d.data.name

// Create the SVG container
const svg = d3.create("svg")
  .attr("viewBox", [0.5, -30.5, width, height + 30])
  .attr("width", width)
  .attr("height", height + 30)
  .attr("style", "max-width: 100%; height: auto;")
  .style("font", "20px Roboto, sans-serif");

// Display the root
let group = svg.append("g")
    .call(render, root);

function uid(name) {
  const id = `${name}-${Math.random().toString(36).substr(2, 9)}`;
  return {
    id: id,
    href: `#${id}`
  };
}

function render(group, root) {
  const node = group
    .selectAll("g")
    .data(root.children.concat(root))
    .join("g");

  node.filter(d => d === root ? d.parent : d.children)
    .attr("cursor", "pointer")
    .on("click", (event, d) => d === root ? zoomout(root) : // Zoom out if root selected 
        d.depth === 4 ? window.open(`https://data.gv.at/katalog/dataset/${d.children[0].data.name}`) : // Open link if dataset node
        zoomin(d))

  node.append("title")
      .text(d => d.depth === 4 ? // tooltip for dataset nodes
            `Titel: ${name(d)}\nLizenz: ${d.data.license}\nVeröffentlichung: ${d.data.release_date}\nBeschreibung: ${d.data.description}` : 
            `${name(d)}\nDatensätze: ${format(d.value)}`); // Tooltip for other nodes

  node.append("rect")
    .attr("id", d => (d.leafUid = uid("leaf")).id)
    .attr("fill", d => {
      if (d === root) {
        return "#fff";  // Root node color (white)
      } else {
        while (d.depth > 1) {
          d = d.parent;
        }
        return colorScale(d.data.name); // Color based on category
      }
    })
    .attr("fill-opacity", d => {
      if (d.depth < 2) {
        return 1; // Full opacity for base level nodes
      } else {
        const scale = getOpacityScale(root.children.filter(n => n.depth === d.depth));
        return scale(d.value);  // Assign opacity based on respective node value
      }
    })
    .attr("stroke", "#fff");  // White outlines (#000 for black)

  node.append("clipPath")
      .attr("id", d => (d.clipUid = uid("clip")).id)
    .append("use")
      .attr("xlink:href", d => d.leafUid.href);

  // Append images to large enough base level nodes (values > 0.1% of root value)
  node.filter(d => d.depth === 1 && d.value / d.ancestors().slice(1, 2).map(d => d.value) >= 0.001)
    .append("image")
    .attr("clip-path", d => d.clipUid)
    .attr("xlink:href", d => imageCategoryMap.get(d.data.name)) // Get corresponding images
    .attr("width", d => {
      d.imageSize = Math.min(0.8 * (x(d.x1) - x(d.x0)), 0.7 * (y(d.y1) - y(d.y0)))  // Bigger images if node is taller than wide
      return d.imageSize;
    })
    .attr("height", d => d.width) // If images are not squares: d => d.width * (y(d.y1) - y(d.y0)) / (x(d.x1) - x(d.x0))
    .attr("x", d => (x(d.x1) - x(d.x0) - d.imageSize) / 2)
    .attr("y", d => {
      // Store upper edge of the image (1/3 of remaining node space is above image)
      d.imageY0 = (y(d.y1) - y(d.y0) - d.imageSize) / 3; 
      // Store lower edge of the image (2/3 of remaining node space are below image to accomodate text)
      d.imageY1 = (y(d.y1) - y(d.y0) + 2 * d.imageSize) / 3; 
      return d.imageY0;
    });
  
  // Append text to large enough nodes (values > 0.4% of root value)
  node.filter(d => d === root || d.value / d.ancestors().slice(1, 2).map(d => d.value) >= 0.004)
    .append("foreignObject")  // Use foreignObjects avoid manual line breaks
      .attr("clip-path", d => d.clipUid)
      .append("xhtml:div")
        // .attr("xmlns", "http://www.w3.org/1999/xhtml") // Necessary for foreignObject structuring?
        .style("font-family", "Roboto, sans-serif")
        .style("font-weight", d => d === root ? "bold" : "normal")  
        .style("color", "black")
        .style("text-align", "center")
        .style("font-size", "12px")
      .html(d => d === root ? `${d.data.name} - ${d.value}` : d.data.name)
        .filter(d => d.depth !== 1) // Vertical centering for non-base nodes
        .style("display", "flex") 
        .style("justify-content", "center") 
        .style("align-items", "center"); 

  // Wait for transition to complete to define text; necessary to have correct positions/sizes
  requestAnimationFrame(() => {
    node.selectAll("foreignObject")
        .attr("x", d => d.x0) 
        .attr("y", d => d === root ? 0 : d.depth === 1 ? d.imageY1 : d.y0) 
        .attr("width", d => x(d.x1) - x(d.x0))
        .attr("height", d => d === root ? 30 // Fixed root height
              : d.depth === 1 ? d.imageY0 // Symmetrical space below image for text on base nodes
              : y(d.y1) - y(d.y0)) // Normal node height
    node.selectAll("foreignObject > div")
        // Redefine div height to center text vertically          
      .style("height", d => d === root ? "30px" : 
              d.depth === 1 ? (y(d.y1) - y(d.y0) - d.imageY0 - d.imageY1).toFixed(0) + "px" : 
              y(d.y1) - y(d.y0) + "px") 
      .style("width", d => x(d.x1) - x(d.x0) + "px")
      // Calculate largest fitting font size
      .each(function(d) {
        const foreignElement = d3.select(this);
        const nodeWidth = parseFloat(foreignElement.node().style.width);
        const nodeHeight = parseFloat(foreignElement.node().style.height); 
        setFontSize(d, foreignElement, nodeWidth, nodeHeight);
      })
  });
  
  group.call(position, root);
}


// Update positions when zooming in/out
function position(group, root) {
  group.selectAll("g")
      .attr("transform", d => d === root ? `translate(0,-30)` : `translate(${x(d.x0)},${y(d.y0)})`)
    .select("rect")
      .attr("width", d => d === root ? width : x(d.x1) - x(d.x0))
      .attr("height", d => d === root ? 30 : y(d.y1) - y(d.y0));

  // Confirm image position and size after transition
  group.selectAll("image")
    .attr("width", d => {
      d.imageSize = Math.min(0.8 * (x(d.x1) - x(d.x0)), 0.7 * (y(d.y1) - y(d.y0))) 
      return d.imageSize;
    })
    .attr("height", d => d.width) 
    .attr("x", d => (x(d.x1) - x(d.x0) - d.imageSize) / 2)
    .attr("y", d => {
      d.imageY0 = (y(d.y1) - y(d.y0) - d.imageSize) / 3; 
      d.imageY1 = (y(d.y1) - y(d.y0) + 2 * d.imageSize) / 3; 
      return d.imageY0;
    });

  group.selectAll("foreignObject")
    .attr("x", d => d.x0) 
    .attr("y", d => d === root ? 0 : d.depth === 1 ? d.imageY1 : d.y0) 
    .attr("width", d => x(d.x1) - x(d.x0))
    .attr("height", d => d === root ? 30 : d.depth === 1 ? d.imageY0 : y(d.y1) - y(d.y0))
}

function setFontSize(nodeData, foreignElement, nodeWidth, nodeHeight) {
  let divElement = foreignElement.node(); // Get the current <div> inside the foreignObject
  
  let minFontSize = 9; // Minimum font size
  let maxFontSize = 33; // Maximum font size
  let padding = 1; // Padding around text
  
  // Function to set the font size and check if it fits within the node
  function fitsInNode(fontSize) {
    divElement.style.fontSize = `${fontSize}px`;
    return divElement.scrollWidth <= nodeWidth && divElement.scrollHeight <= nodeHeight;
  }
  
  // Binary search for the maximum fitting font size
  let fontSize;
  while (minFontSize <= maxFontSize) {
    fontSize = Math.floor((minFontSize + maxFontSize) / 2);
    if (fitsInNode(fontSize)) {
      minFontSize = fontSize + 1; // Try a bigger size
    } else {
      maxFontSize = fontSize - 1; // Try a smaller size
    }
  }

  // Apply the largest fitting font size
  fontSize = maxFontSize - padding; // Reduce by padding if necessary
  divElement.style.fontSize = fontSize > 0 ? `${fontSize}px` : "0px"; // Hide if too small

  // Optionally, remove text if it doesn't fit at the smallest font size
  if (!fitsInNode(fontSize)) {
    divElement.style.fontSize = "0px";
  } 
}

// Define opacity of nodes scaled by node size (=value)
function getOpacityScale(nodes) {
  const valueExtent = d3.extent(nodes, d => d.value);
  return d3.scaleLinear()
    .domain(valueExtent) 
    .range([0.66, 1]); 
}


// Prevent rapid clicks, as they can cause issues
// State variable to manage transition state
let transitionInProgress = false;

// Zoom functions
function zoomin(d) {
  if (transitionInProgress) return; // Exit if a transition is already in progress
  transitionInProgress = true;

  const group0 = group.attr("pointer-events", "none");
  const group1 = group = svg.append("g").call(render, d);

  x.domain([d.x0, d.x1]);
  y.domain([d.y0, d.y1]);

  svg.transition()
    .duration(750)
    .call(t => group0.transition(t).remove()
      .call(position, d.parent))
    .call(t => group1.transition(t)
      .attrTween("opacity", () => d3.interpolate(0, 1))
      .call(position, d))
    .on("end", () => transitionInProgress = false); // Reset flag after transition ends
}

function zoomout(d) {
  if (transitionInProgress) return; // Exit if a transition is already in progress
  transitionInProgress = true;

  const group0 = group.attr("pointer-events", "none");
  const group1 = group = svg.insert("g", "*").call(render, d.parent);

  x.domain([d.parent.x0, d.parent.x1]);
  y.domain([d.parent.y0, d.parent.y1]);

  svg.transition()
    .duration(750)
    .call(t => group0.transition(t)
        .attrTween("opacity", () => d3.interpolate(1, 0))
        .call(position, d))
    .call(t => group1.transition(t)
        .call(position, d.parent))
    .on("end", () => transitionInProgress = false); // Reset flag after transition ends
}

const treemap = display(svg.node());
```

## Animated Treemap

```js echo
const sources = ["Offenerhaushalt.at", "Nationalparks Austria"]
```

```js echo
const years = Array.from({ length: 35 }, (_, i) => 1990 + i);
```

```js
function groupData(data) {
  const filteredData = data.filter(item => animatedTreemapCategoriesIncluded.includes(item["Kategorie"])).filter(item => !animatedTreemapSourcesExcluded.includes(item["Veröffentlichende Stelle"]))
  
  const grouped = new Map();

  filteredData.forEach(d => {
    const category = d["Kategorie"];
    const subcategory = d[filter_animated];
    const year = new Date(d.Datum).getFullYear();
    
    if (!grouped.has(category)) {
      grouped.set(category, new Map());
    }
    
    const categoryMap = grouped.get(category);
    
    if (!categoryMap.has(subcategory)) {
      categoryMap.set(subcategory, Array(years.length).fill(0));
    }
    
    const values = categoryMap.get(subcategory);
    
    // Find the index of the year in the years array
    const yearIndex = years.indexOf(year);
    if (yearIndex >= 0) {
      // Update values with cumulative count
      for (let i = yearIndex; i < values.length; i++) {
        values[i] += 1;
      }
    }
  });

  return grouped;
}
```

```js echo
const treemapDataGrouped = groupData(datasetsDataSimple)
```

```js
function transformToAnimated(data) {
  const result = { 
    keys: years, 
    group: new Map() 
  };

  data.forEach((stelleMap, category) => {
    result.group.set(category, new Map([
      [category, Array.from(stelleMap.entries()).map(([stelle, values]) => ({
        name: stelle,
        values
      }))]
    ]));
  });

  return result;
}
```

```js echo
const treemapDataAnimated = transformToAnimated(treemapDataGrouped)
```

```js echo
const filter_animated = view(Inputs.radio(
    ["Beschreibung", "Kategorien", "Lizenz", "Schlagworte", "Veröffentlichende Stelle"], {value: "Veröffentlichende Stelle"}
))
```

```js
const animatedTreemapCategoriesIncluded = view(Inputs.checkbox(
  (function() {
    return getCategories(datasetsDataSimple, "Kategorie");
  })(),
  {
    // Set initial value to all categories (or a default value)
    value: getCategories(datasetsDataSimple, "Kategorie"),
    label: "Kategorien"
  }
));
```

```js
const animatedTreemapSourcesExcluded = view(Inputs.checkbox(
  sources,
  {label: "Exkludierte Herausgeber"}
));
```

```js
const index = view(Scrubber(d3.range(treemapDataAnimated.keys.length), {
  delay: 1000,
  loop: false,
  format: i => treemapDataAnimated.keys[i]
}));
```

```js echo
updateLegend(treemapCategoriesIncluded);
```

```js
function createTreemapChart(data, colorScale, index) {
  const width = 928;
  const height = width;
  const initialIndex = index.value || 0;
  const parseNumber = string => +string.replace(/,/g, "");
  const formatNumber = d3.format(",d");

  const max = d3.max(data.keys, (d, i) =>
    d3.hierarchy(data.group).sum(d => d.values[i]).value
  );

  const color = colorScale;

  const treemap = d3.treemap()
    .size([width, height])
    .tile(d3.treemapResquarify)
    .padding(d => (d.height === 1 ? 1 : 0))
    .round(true);

  const root = treemap(
    d3
      .hierarchy(data.group)
      .sum(d => (Array.isArray(d.values) ? d3.sum(d.values) : 0))
      .sort((a, b) => b.value - a.value)
  );

  const svg = d3
    .create("svg")
    .attr("width", width)
    .attr("height", height + 20)
    .attr("viewBox", [0, -20, width, height + 20])
    .attr(
      "style",
      "max-width: 100%; height: auto; font: 10px sans-serif; overflow: visible;"
    );

  const box = svg
    .append("g")
    .selectAll("g")
    .data(
      data.keys
        .map((key, i) => {
          const value = root.sum(d => d.values[i]).value;
          return { key, value, i, k: Math.sqrt(value / max) };
        })
        .reverse()
    )
    .join("g")
    .attr(
      "transform",
      ({ k }) => `translate(${(1 - k) / 2 * width},${(1 - k) / 2 * height})`
    )
    .attr("opacity", ({ i }) => (i >= initialIndex ? 1 : 0))
    .call(g =>
      g
        .append("text")
        .attr("y", -6)
        .attr("fill", "#777")
        .selectAll("tspan")
        .data(({ key, value }) => [key, ` ${formatNumber(value)}`])
        .join("tspan")
        .attr("font-weight", (d, i) => (i === 0 ? "bold" : null))
        .text(d => d)
    )
    .call(g =>
      g
        .append("rect")
        .attr("fill", "none")
        .attr("stroke", "#ccc")
        .attr("width", ({ k }) => k * width)
        .attr("height", ({ k }) => k * height)
    );

  const leaf = svg
    .append("g")
    .selectAll("g")
    .data(layout(initialIndex))
    .join("g")
    .attr("transform", d => `translate(${d.x0},${d.y0})`);

  leaf
    .append("rect")
    .attr("id", d => (d.leafUid = uid("leaf")).id)
    .attr("fill", d => {
      while (d.depth > 1) d = d.parent;
      return color(d.data[0]);
    })
    .attr("width", d => d.x1 - d.x0)
    .attr("height", d => d.y1 - d.y0);

  leaf
    .append("clipPath")
    .attr("id", d => (d.clipUid = uid("clip")).id)
    .append("use")
    .attr("xlink:href", d => d.leafUid.href);

  leaf
    .append("text")
    .attr("clip-path", d => d.clipUid)
    .selectAll("tspan")
    .data(d => [d.data.name, formatNumber(d.value)])
    .join("tspan")
    .attr("x", 3)
    .attr(
      "y",
      (d, i, nodes) => `${(i === nodes.length - 1) * 0.3 + 1.1 + i * 0.9}em`
    )
    .attr("fill-opacity", (d, i, nodes) =>
      i === nodes.length - 1 ? 0.7 : null
    )
    .text(d => d);

  leaf.append("title").text(d => d.data.name);

  function layout(index) {
    const k = Math.sqrt(root.sum(d => d.values[index]).value / max);
    const tx = ((1 - k) / 2) * width;
    const ty = ((1 - k) / 2) * height;
    return treemap
      .size([width * k, height * k])(root)
      .each(
        d =>
          (d.x0 += tx,
          d.x1 += tx,
          d.y0 += ty,
          d.y1 += ty)
      )
      .leaves();
  }

  function uid(name) {
    const id = `${name}-${Math.random().toString(36).substr(2, 9)}`;
    return {
      id: id,
      href: `#${id}`
    };
  }

  return Object.assign(svg.node(), {
    update(index, duration) {
      box
        .transition()
        .duration(duration)
        .attr("opacity", ({ i }) => (i >= index ? 1 : 0));

      leaf
        .data(layout(index))
        .transition()
        .duration(duration)
        .ease(d3.easeLinear)
        .attr("transform", d => `translate(${d.x0},${d.y0})`)
        .call(leaf =>
          leaf
            .select("rect")
            .attr("width", d => d.x1 - d.x0)
            .attr("height", d => d.y1 - d.y0)
        )
        .call(leaf =>
          leaf
            .select("text tspan:last-child")
            .tween("text", function(d) {
              const i = d3.interpolate(parseNumber(this.textContent), d.value);
              return function(t) {
                this.textContent = formatNumber(i(t));
              };
            })
        );
    }
  });
}
```

```js echo
const updateChart = createTreemapChart(treemapDataAnimated, colorScale, index)
updateChart.update(index, 1000) // trigger animation from the scrubber
```

```js echo
// animated_treemap
```

```js echo
// update = animated_treemap.update(index, 1000) // trigger animation from the scrubber
```

```js
// import { chart as animated_treemap }
// with {treemapDataAnimated as data}
// from "@d3/animated-treemap"
```

```js
function Scrubber(values, {
  format = value => value,
  initial = 0,
  direction = 1,
  delay = null,
  autoplay = true,
  loop = true,
  loopDelay = null,
  alternate = false
} = {}) {
  values = Array.from(values);
  const form = html`<form style="font: 12px var(--sans-serif); font-variant-numeric: tabular-nums; display: flex; height: 33px; align-items: center;">
  <button name=b type=button style="margin-right: 0.4em; width: 5em;"></button>
  <label style="display: flex; align-items: center;">
    <input name=i type=range min=0 max=${values.length - 1} value=${initial} step=1 style="width: 180px;">
    <output name=o style="margin-left: 0.4em;"></output>
  </label>
</form>`;
  let frame = null;
  let timer = null;
  let interval = null;
  function start() {
    form.b.textContent = "Pause";
    if (delay === null) frame = requestAnimationFrame(tick);
    else interval = setInterval(tick, delay);
  }
  function stop() {
    form.b.textContent = "Play";
    if (frame !== null) cancelAnimationFrame(frame), frame = null;
    if (timer !== null) clearTimeout(timer), timer = null;
    if (interval !== null) clearInterval(interval), interval = null;
  }
  function running() {
    return frame !== null || timer !== null || interval !== null;
  }
  function tick() {
    if (form.i.valueAsNumber === (direction > 0 ? values.length - 1 : direction < 0 ? 0 : NaN)) {
      if (!loop) return stop();
      if (alternate) direction = -direction;
      if (loopDelay !== null) {
        if (frame !== null) cancelAnimationFrame(frame), frame = null;
        if (interval !== null) clearInterval(interval), interval = null;
        timer = setTimeout(() => (step(), start()), loopDelay);
        return;
      }
    }
    if (delay === null) frame = requestAnimationFrame(tick);
    step();
  }
  function step() {
    form.i.valueAsNumber = (form.i.valueAsNumber + direction + values.length) % values.length;
    form.i.dispatchEvent(new CustomEvent("input", {bubbles: true}));
  }
  form.i.oninput = event => {
    if (event && event.isTrusted && running()) stop();
    form.value = values[form.i.valueAsNumber];
    form.o.value = format(form.value, form.i.valueAsNumber, values);
  };
  form.b.onclick = () => {
    if (running()) return stop();
    direction = alternate && form.i.valueAsNumber === values.length - 1 ? -1 : 1;
    form.i.valueAsNumber = (form.i.valueAsNumber + direction) % values.length;
    form.i.dispatchEvent(new CustomEvent("input", {bubbles: true}));
    start();
  };
  form.i.oninput();
  if (autoplay) start();
  else stop();
  Inputs.disposal(form).then(stop);
  return form;
}
```

## Force-Directed Graph

### Data

```js
function reduceData (applicationsData){
  return applicationsData.flatMap(item => ({
    "ID": item["id"],
    "Titel": item["title"],
    "Datasets": item["string_agg"].replace(/[\[\]\\"]/g, '')
  }));
}
```

```js echo
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

```js echo
const expandedData = expandData(reducedData)
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

```js echo
const formattedData = formatData(expandedData, datasetsData)
```

```js echo
const minVerbindungen = view(Inputs.range([1, 10], {value: 10, step: 1, label: "Min. Verbindungen"}))
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
  const visibleDatasetNodes = nodes.filter(d => d.group === "Dataset" && d.connections >= minVerbindungen);
  // Create a set of IDs of visible dataset nodes
  const visibleDatasetIds = new Set(visibleDatasetNodes.map(d => d.id));
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

  // Initial call to set the visibility based on initial minVerbindungen value
  showNodesAndLinks();
  
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
