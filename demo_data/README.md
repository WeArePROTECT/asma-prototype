# ASMA Demo Data Schemas

This folder contains mock data for the September 2025 prototype demo.
Each file is minimal but structurally aligned to real data pipelines
(Conrad/Zengler templates and GenomeDepot).

---

### patients.csv
| Column       | Description                |
|--------------|----------------------------|
| patient_id   | Unique ID (P###)           |
| age          | Patient age (years)        |
| condition    | Condition/cohort (e.g. asthma, control) |
| cohort       | Cohort/group label         |

---

### samples.csv
| Column       | Description                |
|--------------|----------------------------|
| sample_id    | Unique ID (S###)           |
| patient_id   | Link to patients.csv       |
| type         | Sample type (swab, sputum, lung) |
| date         | Collection date (YYYY-MM-DD) |
| project_id   | Project/study label (default: PROTECT) |

---

### bins.jsonl
One JSON object per line.

- `bin_id`: Unique bin ID (B###)  
- `sample_id`: Link to samples.csv  
- `taxonomy`: GTDB/NCBI taxonomic assignment  
- `abundance`: Relative abundance (0–1 mock)  
- `pathways`: List of pathways (mock DRAM/HUMAnN output)

---

### isolates.jsonl
One JSON object per line.

- `isolate_id`: Unique ID (I###)  
- `patient_id`: Link to patients.csv  
- `source_sample_id`: Origin sample ID  
- `taxonomy`: Species/strain label  
- `taxid_genus`: Genus taxid label  
- `amr_flags`: List of resistance markers (mock)  
- `linked_bins`: Associated bin IDs  
- `annotations_summary`: 1-liner annotation (mock)

---

### interactions.json
Array of edges.

- `source_isolate`, `target_isolate`: Isolate IDs  
- `type`: `"cooccurrence" | "competition" | "complementarity"`  
- `score`: Numeric mock score (0–1)  
- `evidence`: Tags for provenance/method

---

### prebiotics.csv
| Column       | Description                |
|--------------|----------------------------|
| prebiotic_id | Unique ID (PB###)          |
| name         | Prebiotic name             |
| class        | Compound class             |
| notes        | Notes                      |

---

### formulations.json
Array of formulations.

- `formulation_id`: Unique ID (F###)  
- `organisms`: List of isolate IDs  
- `prebiotics`: List of prebiotic IDs  
- `score_predicted`: Mock score (0–1)  
- `notes`: Notes for demo
