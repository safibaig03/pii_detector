import pandas as pd
import numpy as np
from presidio_analyzer import AnalyzerEngine
from core.policy import SKIP_PII_ENTITIES
import streamlit as st

@st.cache_resource
def get_analyzer():
    return AnalyzerEngine()

analyzer = get_analyzer()

def is_free_text(sample_data):
    return (
        np.mean([len(s) for s in sample_data]) > 50 or
        np.mean([s.count(" ") for s in sample_data]) > 5
    )

def mask_free_text_row(text, score_threshold=0.4):
    if pd.isna(text):
        return text

    text = str(text)
    results = analyzer.analyze(
        text=text,
        language="en",
        score_threshold=score_threshold
    )

    masked = text
    for r in sorted(results, key=lambda x: x.start, reverse=True):
        if r.entity_type in SKIP_PII_ENTITIES:
            continue
        masked = masked[:r.start] + f"<{r.entity_type}>" + masked[r.end:]

    return masked
