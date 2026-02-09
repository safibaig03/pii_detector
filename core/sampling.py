import pandas as pd

def get_robust_sample(series, min_samples=50, max_samples=200):
    valid = series.dropna().astype(str)
    valid = valid[valid.str.strip().str.len() > 0]

    total = len(valid)
    if total == 0:
        return []

    if total <= max_samples:
        return valid.tolist()

    return valid.sample(n=max_samples, random_state=42).tolist()
