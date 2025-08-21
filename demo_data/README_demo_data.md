# 🧪 ASMA Prototype Demo Data

This folder contains **mock data files** used to power the ASMA prototype API and UI.  
The goal is to provide a **swap-ready structure**: the schemas match what real data will eventually look like, so these files can be replaced in the future without breaking the API.

---

## 📂 Files

### `patients.csv`
- **Mock:** 3 patients (IDs: P001–P003) with age and condition.
- **Real Source:** Patient/animal metadata from **Conrad Lab** and **Zengler Lab** metadata templates.

### `samples.csv`
- **Mock:** 5 samples (S001–S005) linked to patients, with type and date.
- **Real Source:** Sample metadata from **Conrad/Zengler lab submissions**, SRA/ENA metadata.

### `bins.jsonl`
- **Mock:** 5 bins with taxonomy, abundance, `pathways`, and `pathways_scored` fields.
- **Real Source:** Metagenomic bins from **MetaBAT2/DASTool**, annotated with **HUMAnN, eggNOG-mapper, KEGG/MetaCyc, DRAM**. Abundances from **CoverM** or similar.

### `isolates.jsonl`
- **Mock:** 4 isolates linked to bins, with AMR flags and annotations. Includes demo fields:
  - `growth_media` (fake media recipes)
  - `metabolite_markers` (stub metabolite tags)
  - `genome_depot_id` (fake accession ID)
- **Real Source:** Isolate genomes and metadata from **UCB (Arkin Lab)** isolation pipeline.  
  Growth media and metabolite data from **lab notebooks** and **metabolomics assays**.  
  `genome_depot_id` will map to entries in the **GenomeDepot** instance.

### `interactions.json`
- **Mock:** Small graph of isolate–isolate interactions with fake scores.
- **Real Source:** Co-abundance correlation (SparCC, SPIEC-EASI) and metabolic complementarity (Pathway Tools, **MIND framework**).

### `prebiotics.csv`
- **Mock:** Simple entries like Inulin and FOS.
- **Real Source:** Literature curation + **Conrad Lab** formulation experiments.

### `formulations.json`
- **Mock:** Two formulations combining isolates + prebiotics with stub scores.
- **Real Source:** Outputs from **formulation scoring models** (ML or rule-based), validated against in vitro assays.

---

## 🔑 Usage Notes
- This data is **demo-only** — not intended for analysis.  
- The schemas are designed to match **future production data**.  
- Replacing these files with real lab-generated data should not require changes to the API.  
- Endpoints tested with this mock data:
  - `/patients`, `/samples`, `/bins`, `/isolates`, `/interactions`, `/prebiotics`, `/formulations`
  - Specialized: `/bins/{id}/pathways`, `/isolates/{id}/omics`, `/samples/{id}/abundance`, `/network`

---


