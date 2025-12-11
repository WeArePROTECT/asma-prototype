# UICT v1 Preview Output

## Schema (Columns + Data Types)

| Column | Data Type |
|--------|-----------|
| `ASMA_id` | `object` |
| `domain` | `object` |
| `phylum` | `object` |
| `class` | `object` |
| `order` | `object` |
| `family` | `object` |
| `genus` | `object` |
| `species` | `object` |
| `strain_group` | `float64` |
| `representative` | `object` |
| `scfm_n_reps` | `float64` |
| `scfm_delta_od_mean` | `float64` |
| `scfm_delta_od_sd` | `float64` |
| `scfm_delta_od_max` | `float64` |
| `scfm_last_assay_date` | `float64` |
| `scfm_growth_class` | `object` |
| `inhib_100x_n` | `float64` |
| `inhib_100x_mean` | `float64` |
| `inhib_100x_sd` | `float64` |
| `pa_inhibition_class` | `float64` |
| `inhib_last_assay_date` | `float64` |
| `no_carbon_mean_od` | `float64` |
| `no_carbon_sd_od` | `float64` |
| `carbon_last_assay_date` | `float64` |
| `glucose_mean_od` | `float64` |
| `glucose_utilization_call` | `object` |
| `lactate_mean_od` | `float64` |
| `lactate_utilization_call` | `object` |
| `serine_mean_od` | `float64` |
| `serine_utilization_call` | `object` |
| `threonine_mean_od` | `float64` |
| `threonine_utilization_call` | `object` |
| `alanine_mean_od` | `float64` |
| `alanine_utilization_call` | `object` |
| `glycine_mean_od` | `float64` |
| `glycine_utilization_call` | `object` |
| `proline_mean_od` | `float64` |
| `proline_utilization_call` | `object` |
| `isoleucine_mean_od` | `float64` |
| `isoleucine_utilization_call` | `object` |
| `leucine_mean_od` | `float64` |
| `leucine_utilization_call` | `object` |
| `valine_mean_od` | `float64` |
| `valine_utilization_call` | `object` |
| `aspartate_mean_od` | `float64` |
| `aspartate_utilization_call` | `object` |
| `glutamate_mean_od` | `float64` |
| `glutamate_utilization_call` | `object` |
| `phenylalanine_mean_od` | `float64` |
| `phenylalanine_utilization_call` | `object` |
| `tryptophan__mean_od` | `float64` |
| `tryptophan__utilization_call` | `object` |
| `lysine_mean_od` | `float64` |
| `lysine_utilization_call` | `object` |
| `histidine_mean_od` | `float64` |
| `histidine_utilization_call` | `object` |
| `arginine_mean_od` | `float64` |
| `arginine_utilization_call` | `object` |
| `ornithine_mean_od` | `float64` |
| `ornithine_utilization_call` | `object` |
| `cystein_mean_od` | `float64` |
| `cystein_utilization_call` | `object` |
| `methionine_mean_od` | `float64` |
| `methionine_utilization_call` | `object` |

## First 10 Rows

| ASMA_id | domain | phylum | class | order | family | genus | species | strain_group | representative | scfm_n_reps | scfm_delta_od_mean | scfm_delta_od_sd | scfm_delta_od_max | scfm_last_assay_date |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AB_reporter | Bacteria | Pseudomonadota | Gammaproteobacteria | Pseudomonadales | Moraxellaceae | Acinetobacter | Acinetobacter baumannii | 1.0000 | Yes | NaN | NaN | NaN | NaN | NaN |
| ASMA-1 | Bacteria | Actinomycetota | Actinomycetes | Micrococcales | Micrococcaceae | Rothia | Rothia dentocariosa | 518.0000 | No | NaN | NaN | NaN | NaN | NaN |
| ASMA-10 | Bacteria | Pseudomonadota | Gammaproteobacteria | Pseudomonadales | Pseudomonadaceae | Pseudomonas | Pseudomonas aeruginosa | 536.0000 | No | NaN | NaN | NaN | NaN | NaN |
| ASMA-100 | Fungi | Saccharomycetes | Ascomycota | Saccharomycetales | Debaryomycetaceae | Candida | Candida albicans | NaN | NaN | NaN | NaN | NaN | NaN | NaN |
| ASMA-1000 | Bacteria | Bacillota | Bacilli | Staphylococcales | Staphylococcaceae | Staphylococcus | Staphylococcus aureus | 539.0000 | No | NaN | NaN | NaN | NaN | NaN |
| ASMA-1001 | Bacteria | Bacillota | Bacilli | Staphylococcales | Staphylococcaceae | Staphylococcus | Staphylococcus aureus | 539.0000 | No | NaN | NaN | NaN | NaN | NaN |
| ASMA-1002 | Bacteria | Bacillota | Bacilli | Staphylococcales | Staphylococcaceae | Staphylococcus | Staphylococcus aureus | 539.0000 | No | NaN | NaN | NaN | NaN | NaN |
| ASMA-1003 | Bacteria | Bacillota | Bacilli | Staphylococcales | Staphylococcaceae | Staphylococcus | Staphylococcus aureus | 539.0000 | No | NaN | NaN | NaN | NaN | NaN |
| ASMA-1004 | Bacteria | Bacillota | Bacilli | Staphylococcales | Staphylococcaceae | Staphylococcus | Staphylococcus aureus | 539.0000 | No | NaN | NaN | NaN | NaN | NaN |
| ASMA-1005 | Bacteria | Bacillota | Bacilli | Staphylococcales | Staphylococcaceae | Staphylococcus | Staphylococcus aureus | 539.0000 | No | NaN | NaN | NaN | NaN | NaN |

*Note: Showing first 15 of 64 columns*


## Summary Statistics

- **Total isolates:** 3890
- **With SCFM data:** 449
- **With inhibition data (100:1):** 0
- **With carbon utilization data:** 372

### SCFM Growth Class Distribution

- `no_growth`: 313
- `robust`: 56
- `poor`: 47
- `normal`: 33

### PA Inhibition Class Distribution

- No PA inhibition class data
