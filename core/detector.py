import pandas as pd
from collections import Counter
from presidio_analyzer import AnalyzerEngine

from core.sampling import get_robust_sample
from core.free_text import is_free_text, mask_free_text_row
from core.policy import SKIP_PII_ENTITIES

# ===============================
# INIT ANALYZER 
# ===============================


import streamlit as st

@st.cache_resource
def get_analyzer():
    return AnalyzerEngine()

analyzer =get_analyzer()

# ===============================
# MAIN DETECTOR
# ===============================
def detect_and_mask_pii(df: pd.DataFrame, score_threshold: float = 0.4):
    """
    Runs PII detection + masking.

    Returns:
      masked_df  : DataFrame (PII masked)
      summary_df : DataFrame with columns:
                   [column, type, pii, entity, density, details]
    """

    masked_df = df.copy()
    summary_rows = []

    for column in df.columns:
        sample_data = get_robust_sample(df[column])

        # ---------------- EMPTY ----------------
        if not sample_data:
            summary_rows.append({
                "column": column,
                "type": "Unknown",
                "pii": "NO",
                "entity": "-",
                "density": "-",
                "details": "Empty"
            })
            continue

        # ---------------- FREE TEXT ----------------
        if is_free_text(sample_data):
            masked_df[column] = df[column].apply(mask_free_text_row)

            summary_rows.append({
                "column": column,
                "type": "Free Text",
                "pii": "YES",
                "entity": "Mixed",
                "density": "-",
                "details": "Row-level span masking"
            })
            continue

        # ---------------- STRUCTURED ----------------
        raw_entity_rows = Counter()
        valid_entity_rows = Counter()
        total_checks = 0

        for item in sample_data:
            if len(item) < 2:
                continue

            total_checks += 1
            text = f"The value is {item}"

            results = analyzer.analyze(
                text=text,
                language="en",
                score_threshold=score_threshold
            )

            if not results:
                continue

            relevant = [r for r in results if r.start >= 12]
            if not relevant:
                continue

            best = max(relevant, key=lambda x: x.score)
            entity = best.entity_type

            raw_entity_rows[entity] += 1

            if entity not in SKIP_PII_ENTITIES:
                valid_entity_rows[entity] += 1

        if total_checks == 0:
            summary_rows.append({
                "column": column,
                "type": "Structured",
                "pii": "NO",
                "entity": "-",
                "density": "-",
                "details": "No valid data"
            })
            continue

        # -------- ORIGINAL OG DENSITY --------
        best_entity = None
        best_density = 0.0

        for entity, count in raw_entity_rows.items():
            density = count / total_checks
            if density > best_density:
                best_entity = entity
                best_density = density

        density_str = f"{int(best_density * 100)}%"

        # -------- DOMINANCE RULE (STABLE OG) --------
        if (
            best_entity
            and best_entity in valid_entity_rows
            and best_density >= 0.45
        ):
            masked_df[column] = df[column].apply(
                lambda x: f"<{best_entity}>" if pd.notna(x) else x
            )

            summary_rows.append({
                "column": column,
                "type": "Structured",
                "pii": "YES",
                "entity": best_entity,
                "density": density_str,
                "details": "Column masked"
            })
        else:
            if best_entity in SKIP_PII_ENTITIES:
                reason = "Non-PII entity"
            elif best_entity:
                reason = f"Low dominance {best_entity}"
            else:
                reason = "Clean"

            summary_rows.append({
                "column": column,
                "type": "Structured",
                "pii": "NO",
                "entity": best_entity or "-",
                "density": density_str,
                "details": reason
            })

    summary_df = pd.DataFrame(summary_rows)
    return masked_df, summary_df
