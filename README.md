# ASMA Prototype

The **Airway Synthetic Microbial Atlas (ASMA) Prototype** is an early research and development (R&D) platform built to explore what the full ASMA system could become.  
It is designed to serve as a **vision testbed**: helping our team, collaborators, and stakeholders experiment with interfaces, data flows, and analyses before committing to a production platform.

This repository contains a minimal but functional prototype of the ASMA platform, with both a **FastAPI backend** and a **React frontend**. It demonstrates how multi-omic and isolate data can be browsed, linked, and explored interactively.

⚠️ **Important note:** This is strictly an **R&D prototype**. It is **not production software**, and its purpose is to guide design discussions, test ideas, and show what ASMA could evolve into.

---

## Current Functionality

Through multiple sprints, the prototype currently supports:

### 1. Universal Browser
- Browse across **Patients → Samples → Bins → Isolates** in a lineage view.  
- Search across entities (`/search?q=...`).  
- Export tables to CSV/JSON (`/download/{entity}`).

### 2. Functional-Omics Dashboard (stubbed)
- For each bin, view basic abundance bars and pathway “chips.”  
- Provides placeholders for integration of real functional-omics pipelines (e.g., DRAM, HUMAnN).

### 3. Interaction Network
- Force-layout graph of isolates with edge types (competition, co-occurrence, complementarity).  
- Node clicks open isolate cards.  
- Isolates can be added to the formulation cart directly from the network.

### 4. Formulation Builder
- Drag-and-drop isolates and prebiotics into a cart.  
- Preview mock formulation scores and rationale (`/formulations/preview`).  
- Demonstrates scenario building and predictive scoring concepts.

### 5. Landing Page + Demo Polish
- A simple landing page with three tiles: **Universal Browser**, **Interaction Network**, **Formulation Builder**.  
- Export buttons for main tables.  
- Demo-ready click path (browse a patient → open a bin → view an isolate → explore the network → build a formulation).

### 6. Configurability + Packaging
- Data directory configurable via `ASMA_DATA_DIR`.  
- Designed to swap `/demo_data/` for real datasets.  
- Early containerization planned with Podman compatibility (FastAPI + static frontend).

### 7. Taxonomic Table & Isolate Treemap Viewers
- **Taxonomic Table Viewer** (`/api/taxonomy/table`) - Interactive DataTables view of ASMA isolate taxonomy data.
- **Isolate Treemap Viewer** (`/api/taxonomy/treemap`) - Plotly treemap visualization of taxonomic hierarchy.
- **Taxonomy Data** (`/api/taxonomy/tsv`) - Raw TSV data endpoint for programmatic access.
- All endpoints read directly from Alex Styer's data directory to stay in sync.

---

## Roadmap & Vision

The prototype is **not the final ASMA system**.  
Instead, it is a sandbox for answering key questions:  

- What interfaces best serve researchers?  
- How should ASMA connect patients, samples, omics data, and isolates?  
- What scoring models and visualizations are most useful for testing microbial formulations?  

Future iterations will incorporate:
- GenomeDepot links for isolates.  
- Integration of real functional-omics results.  
- Extended formulation scoring models.  
- AI/LLM-powered explainers to enhance isolate and network exploration.  

---

## Getting Started

1. Clone the repo and install dependencies (`requirements.txt` and `requirements-dev.txt`).  
2. Launch the backend:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
3. Launch the frontend (React/Vite or Next):  
   ```bash
   npm install
   npm run dev
   ```
4. Open the app in your browser and explore demo data.

## Container Deployment

For production deployment, use the provided deployment script:

```bash
./deploy_container.sh [image_name] [container_name] [port]
```

Or manually ensure all required configuration:

```bash
podman run -d --name asma-proto-v10 -p 8765:5000 \
  -v /opt/shared/spencerlong/asma-prototype/demo_data:/app/demo_data:ro \
  -v /usr2/people/alex.styer/public_html:/app/alex_public_html:ro \
  -e ASMA_DATA_DIR=/app/demo_data \
  -e ALEX_PUBLIC_HTML_DIR=/app/alex_public_html \
  --restart unless-stopped \
  localhost/asma-prototype:main-latest
```

**⚠️ Important:** Both volume mounts and both environment variables are required. The application will log warnings at startup if configuration is incorrect.

---

## License

This code is provided for **research and prototyping purposes only**.  
Not intended for clinical use or production deployment.
