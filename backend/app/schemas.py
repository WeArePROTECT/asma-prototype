"""
backend/app/schemas.py
======================
Pydantic v2 response models for the ASMA Prototype API.
Shared by the FastAPI backend and the ETL script (real_data/prepare_real_data.py).

Field validators handle:
  • NaN / pd.NA / "nan" / "none" / "" → None (or field default)
  • sex:    Male → M, Female → F, else → "Unknown"
  • condition / cohort: normalised capitalisation, null → "Unknown"
  • collection_date: any common date format → "YYYY-MM-DD"; null → None
  • Optional[float]: inf / NaN → None
  • Optional[str]: strip whitespace; empty after strip → None (or default)
  • patient_id / sample_id: always coerced to str
  • isolate_id: must start with "ASMA-"; raises ValueError otherwise
  • taxonomy / genus: null or unmatched → "Unknown"

Backward compatibility (for demo_data/ with old field names):
  • Isolate: source_sample_id → sample_id fallback
  • Isolate: taxid_genus     → genus fallback
  • Isolate: linked_bins[]   → linked_bin (first element) fallback
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ── Blank / NaN sentinel set ──────────────────────────────────────────────────

_BLANK = {"nan", "none", "null", "na", "n/a", ""}


def _nil(v: Any) -> Any:
    """Return None if v is NaN-ish, blank string, or pandas NA; else v unchanged."""
    if v is None:
        return None
    # pandas NA — bool(pd.NA) raises TypeError, so test with a try/except
    try:
        import pandas as _pd  # noqa: F401 (optional dep)
        if v is _pd.NA:
            return None
    except ImportError:
        pass
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, str) and v.strip().lower() in _BLANK:
        return None
    return v


def _clean_dict(d: dict) -> dict:
    return {k: _nil(v) for k, v in d.items()}


# ── Patient ───────────────────────────────────────────────────────────────────

class Patient(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    patient_id: str
    age: Optional[float] = None
    sex: Optional[str] = "Unknown"
    condition: Optional[str] = "Unknown"
    cohort: Optional[str] = "Unknown"
    fev1_pp: Optional[float] = None
    fev1_l: Optional[float] = None
    fvc_pp: Optional[float] = None
    fvc_l: Optional[float] = None
    fev1_fvc_ratio: Optional[float] = None
    bmi: Optional[float] = None
    weight_kg: Optional[float] = None
    ht_cm: Optional[float] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    cftr_modulator_status: Optional[str] = None
    patient_population: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _clean(cls, data: Any) -> Any:
        return _clean_dict(data) if isinstance(data, dict) else data

    @field_validator("patient_id", mode="before")
    @classmethod
    def _pid(cls, v: Any) -> str:
        if v is None:
            raise ValueError("patient_id must not be null")
        return str(v).strip()

    @field_validator(
        "age", "fev1_pp", "fev1_l", "fvc_pp", "fvc_l",
        "fev1_fvc_ratio", "bmi", "weight_kg", "ht_cm",
        mode="before",
    )
    @classmethod
    def _float(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            f = float(v)
            return None if (math.isnan(f) or math.isinf(f)) else f
        except (TypeError, ValueError):
            return None

    @field_validator("sex", mode="before")
    @classmethod
    def _sex(cls, v: Any) -> str:
        if v is None:
            return "Unknown"
        s = str(v).strip().lower()
        return "M" if s in ("male", "m") else "F" if s in ("female", "f") else "Unknown"

    @field_validator("condition", mode="before")
    @classmethod
    def _condition(cls, v: Any) -> str:
        if v is None:
            return "Unknown"
        s = str(v).strip()
        return s if s else "Unknown"

    @field_validator("cohort", mode="before")
    @classmethod
    def _cohort(cls, v: Any) -> str:
        if v is None:
            return "Unknown"
        s = str(v).strip()
        _MAP = {
            "adult": "Adult", "pediatric": "Pediatric", "paediatric": "Pediatric",
            "case": "Case", "control": "Control",
        }
        return _MAP.get(s.lower(), s.capitalize()) or "Unknown"

    @field_validator(
        "race", "ethnicity", "cftr_modulator_status", "patient_population",
        mode="before",
    )
    @classmethod
    def _ostr(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


# ── Sample ────────────────────────────────────────────────────────────────────

class Sample(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    sample_id: str
    patient_id: str
    sample_type: Optional[str] = None
    collection_date: Optional[str] = None
    visit_number: Optional[int] = None
    days_since_first_collection: Optional[int] = None
    project_id: str = "PROTECT"
    patient_status_collection: Optional[str] = None
    assessment_of_pex: Optional[str] = None
    antibiotic_status: Optional[str] = None
    any_iv_antibiotics: Optional[bool] = None
    n_active_antibiotics: Optional[float] = None
    pa_positive: Optional[bool] = None
    has_isolates: Optional[bool] = False
    has_metag: Optional[bool] = False
    has_metars: Optional[bool] = False
    data_streams_count: Optional[int] = None
    metag_shannon: Optional[float] = None
    metag_richness: Optional[float] = None
    metag_chao1: Optional[float] = None
    metag_simpson: Optional[float] = None
    metag_total_reads: Optional[float] = None
    metag_alignment_rate: Optional[float] = None
    pa_alignment_pct: Optional[float] = None
    sampling_site: Optional[str] = None
    sample_material: Optional[str] = None
    isolation_source_type: Optional[str] = None
    asma_id_count: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def _clean(cls, data: Any) -> Any:
        return _clean_dict(data) if isinstance(data, dict) else data

    @field_validator("sample_id", "patient_id", mode="before")
    @classmethod
    def _ids(cls, v: Any) -> str:
        if v is None:
            raise ValueError("ID field must not be null")
        return str(v).strip()

    @field_validator("collection_date", mode="before")
    @classmethod
    def _date(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return None

    @field_validator(
        "visit_number", "days_since_first_collection",
        "data_streams_count", "asma_id_count",
        mode="before",
    )
    @classmethod
    def _int(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        try:
            f = float(v)
            return None if (math.isnan(f) or math.isinf(f)) else int(f)
        except (TypeError, ValueError):
            return None

    @field_validator(
        "n_active_antibiotics", "metag_shannon", "metag_richness",
        "metag_chao1", "metag_simpson", "metag_total_reads",
        "metag_alignment_rate", "pa_alignment_pct",
        mode="before",
    )
    @classmethod
    def _float(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            f = float(v)
            return None if (math.isnan(f) or math.isinf(f)) else f
        except (TypeError, ValueError):
            return None

    @field_validator(
        "any_iv_antibiotics", "pa_positive",
        "has_isolates", "has_metag", "has_metars",
        mode="before",
    )
    @classmethod
    def _bool(cls, v: Any) -> Optional[bool]:
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in ("true", "1", "yes"):
            return True
        if s in ("false", "0", "no"):
            return False
        return None

    @field_validator(
        "sample_type", "patient_status_collection", "assessment_of_pex",
        "antibiotic_status", "sampling_site", "sample_material",
        "isolation_source_type",
        mode="before",
    )
    @classmethod
    def _ostr(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


# ── Isolate ───────────────────────────────────────────────────────────────────

class Isolate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    isolate_id: str
    sample_id: str
    patient_id: str
    taxonomy: Optional[str] = "Unknown"
    genus: Optional[str] = "Unknown"
    family: Optional[str] = None
    order: Optional[str] = None
    class_: Optional[str] = None
    phylum: Optional[str] = None
    growth_media: Optional[str] = None
    genome_depot_id: Optional[str] = None
    linked_bin: Optional[str] = None
    amr_flags: Optional[List[str]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _compat_and_clean(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = _clean_dict(data)
        # source_sample_id → sample_id (demo data back-compat)
        if d.get("sample_id") is None and d.get("source_sample_id") is not None:
            d["sample_id"] = d["source_sample_id"]
        # taxid_genus → genus (demo data back-compat)
        if d.get("genus") is None and d.get("taxid_genus") is not None:
            d["genus"] = d["taxid_genus"]
        # linked_bins list → linked_bin first element (demo data back-compat)
        if d.get("linked_bin") is None:
            lb = d.get("linked_bins")
            if isinstance(lb, list) and lb:
                d["linked_bin"] = lb[0]
            elif isinstance(lb, str) and lb.strip():
                d["linked_bin"] = lb.strip()
        return d

    @field_validator("isolate_id", mode="before")
    @classmethod
    def _iid(cls, v: Any) -> str:
        if v is None:
            raise ValueError("isolate_id must not be null")
        s = str(v).strip()
        if not s.startswith("ASMA-"):
            raise ValueError(f"isolate_id must start with 'ASMA-'; got {s!r}")
        return s

    @field_validator("sample_id", "patient_id", mode="before")
    @classmethod
    def _ids(cls, v: Any) -> str:
        if v is None:
            raise ValueError("ID field must not be null")
        s = str(v).strip()
        if not s:
            raise ValueError("ID field must not be empty")
        return s

    @field_validator("taxonomy", mode="before")
    @classmethod
    def _tax(cls, v: Any) -> str:
        if v is None:
            return "Unknown"
        s = str(v).strip()
        return s if s else "Unknown"

    @field_validator("genus", mode="before")
    @classmethod
    def _genus(cls, v: Any) -> str:
        if v is None:
            return "Unknown"
        s = str(v).strip()
        return s if s else "Unknown"

    @field_validator(
        "family", "order", "class_", "phylum",
        "growth_media", "genome_depot_id", "linked_bin",
        mode="before",
    )
    @classmethod
    def _ostr(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @field_validator("amr_flags", mode="before")
    @classmethod
    def _amr(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v if x is not None]
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed if x]
            except (json.JSONDecodeError, ValueError):
                pass
            return [x.strip() for x in s.split(",") if x.strip()]
        return []
