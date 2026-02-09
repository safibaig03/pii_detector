import streamlit as st
import pandas as pd
from core.detector import detect_and_mask_pii

st.set_page_config(page_title="PII Detector", layout="wide")

st.title("PII Detection & Masking Tool")

uploaded_file = st.file_uploader(
    "Upload CSV file",
    type=["csv"]
)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("Preview")
    st.dataframe(df.head())

    if st.button("Run PII Detection"):
        with st.spinner("Detecting PII..."):
            masked_df, summary_df = detect_and_mask_pii(df)

        st.subheader("PII Summary")
        st.dataframe(summary_df)

        st.subheader("Masked Preview")
        st.dataframe(masked_df.head())

        csv = masked_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Masked CSV",
            csv,
            file_name="masked.csv",
            mime="text/csv"
        )

  