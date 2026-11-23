# Step-by-Step Guide: Running & Adapting Data Visualizations 🛠️

> **Target Directories:**
> - [`Worked Examples/opengeo/`](Worked%20Examples/opengeo)
> - [`Worked Examples/pagerank/`](Worked%20Examples/pagerank)
>
> **Key Objective:** Execute the end-to-end data pipeline from raw network ingestion to browser-based interactive visualizations.

---

## 🗺️ Pipeline 1: OpenGeo Geocoding Map

### Step 1: Ingest and Cache Geocodes (`geoload.py`)
Run `geoload.py` to process addresses in `where.data`. It queries OpenStreetMap's Nominatim geocoder while caching all responses in `opengeo.sqlite`:

```bash
cd "Worked Examples/opengeo"
python geoload.py
```

*What happens under the hood:*
1. Reads `where.data` line by line.
2. Checks `opengeo.sqlite` with `SELECT geodata FROM Locations WHERE address = ?`.
3. If not cached, fetches JSON from `https://py4e-data.dr-chuck.net/opengeo?q=...` with a politeness delay.
4. Commits coordinates to SQLite. You can pause and resume execution at any time without duplicate network requests.

### Step 2: Export Data to JavaScript (`geodump.py`)
Extract the cached coordinates from SQLite into an executable JavaScript data payload:

```bash
python geodump.py
```

Output:
```text
Found 260 locations in database...
260 lines were written to where.js
Open where.html in a web browser to view the data.
```

### Step 3: View the Interactive Map (`where.html`)
Open `where.html` in any web browser (Chrome, Firefox, Edge). OpenLayers renders pins on the world map with clickable popups showing university details.

---

## 🕸️ Pipeline 2: PageRank & D3.js Network Graph

### Step 1: Crawl the Web Page Graph (`spider.py`)
Crawl web pages starting from a seed URL (e.g. `http://data.pr4e.org/`):

```bash
cd "../pagerank"
python spider.py
```
- Enter seed URL or press Enter for default.
- Specify how many pages to crawl (e.g. `20`).
- Links are recorded as directed edges in `spider.sqlite` (Tables: `Pages`, `Links`, `Webs`).

### Step 2: Compute PageRank Iterations (`sprank.py`)
PageRank models a random surfer clicking links. Pages linked to by many other high-ranking pages receive higher authority:

$$PR(A) = (1 - d) + d \sum_{i=1}^n \frac{PR(T_i)}{C(T_i)}$$

Run the mathematical solver for 50 iterations:
```bash
python sprank.py
```
Output displays the standard deviation of rank differences until the ranks converge to a steady state.

### Step 3: Serialize to D3 JSON Format (`spjson.py`)
Extract the top $N$ ranked nodes and their interconnecting links into `spider.js`:

```bash
python spjson.py
```
Output:
```text
Creating JSON node-link data...
Writing spider.js with 25 nodes and 64 links...
Open force.html in a browser.
```

### Step 4: Launch Interactive D3 Force Simulation (`force.html`)
Open `force.html` in your browser.
- D3.js runs a physical spring-charge force simulation.
- Node size is proportional to PageRank authority.
- Connected pages pull together; you can drag nodes to explore cluster connectivity in real time.

---

## 💡 How to Adapt this to Modern Multi-Agent AI

When designing multi-agent swarms (e.g. LangGraph or CrewAI):
1. **Agent Message Topologies:** Replace URLs with `Agent_ID`s and hyperlink edges with `message_sent` events to visualize multi-agent collaboration patterns.
2. **Tool Centrality:** Run PageRank over agent tool calls to discover which tools (e.g. WebSearch vs CodeRunner) are critical hubs in your system.
3. **Trace Visualization:** Export your agent execution logs to JSON and visualize them in browser graphs to debug complex multi-step reasoning chains.
