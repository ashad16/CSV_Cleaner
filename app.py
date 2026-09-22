import io
import zipfile
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSV Cleaner", layout="wide")
st.title("CSV Header Cleaner & Modifier")

# Set for O(1) fast lookup
COLUMNS_TO_REMOVE = {
    "Editors",
    "Publisher",
    "ISSN",
    "ISBN",
    "CODEN",
    "PubMed ID",
    "Language of Original",
    "Language of Original Document",
    "Abbreviated Source Title",
    "Document Type",
    "Publication Stage",
    "Open Access",
    "Source",
    "EID",
}


def load_csv_fast(file_bytes):
    """Fast C-engine parser attempting standard CSV formats first."""
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]

    # 1. Fast path: standard C engine with common encodings
    for enc in encodings:
        try:
            return pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=enc,
                on_bad_lines="skip",
                dtype=str,  # Prevents costly auto-type inference
            )
        except Exception:
            continue

    # 2. Fallback: Python engine (only if C engine fails for auto separator detection)
    try:
        return pd.read_csv(
            io.BytesIO(file_bytes),
            sep=None,
            engine="python",
            on_bad_lines="skip",
            dtype=str,
        )
    except Exception:
        return pd.read_csv(
            io.BytesIO(file_bytes),
            encoding="utf-8",
            encoding_errors="replace",
            on_bad_lines="skip",
            dtype=str,
        )


def process_single_file(file_tuple):
    """Worker function to process one file (runs in parallel)."""
    file_name, file_bytes = file_tuple
    df = load_csv_fast(file_bytes)

    # 1. Remove unwanted columns
    cols_to_drop = [col for col in df.columns if col in COLUMNS_TO_REMOVE]
    if cols_to_drop:
        df.drop(columns=cols_to_drop, inplace=True)

    # 2. Insert 'Link' column before 'Correspondence Address'
    target_col = "Correspondence Address"
    if "Link" not in df.columns:
        if target_col in df.columns:
            idx = df.columns.get_loc(target_col)
            df.insert(idx, "Link", "")
        else:
            df["Link"] = ""

    # Convert cleaned df to CSV string
    csv_data = df.to_csv(index=False, encoding="utf-8")

    return file_name, df, csv_data


uploaded_files = st.file_uploader(
    "Upload CSV (Max 20 files)", type=["csv"], accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) > 20:
        st.error(
            "⚠️ Maximum 20 files allowed at a time. Please remove extra files and try again."
        )
        st.stop()

    # Pre-read file bytes to pass cleanly into multiprocess workers
    files_payload = [(f.name, f.read()) for f in uploaded_files]

    # Process files in parallel across CPU cores
    processed_files = {}
    with ProcessPoolExecutor() as executor:
        results = executor.map(process_single_file, files_payload)
        for file_name, df, csv_data in results:
            processed_files[file_name] = {"df": df, "csv_data": csv_data}

    # Step 2: In-memory ZIP File Generation
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, file_info in processed_files.items():
            zip_file.writestr(
                f"cleaned_{file_name}", file_info["csv_data"]
            )

    st.success("All files processed successfully!")

    st.download_button(
        label="📦 Download All Cleaned CSVs as ZIP",
        data=zip_buffer.getvalue(),
        file_name="cleaned_csv_files.zip",
        mime="application/zip",
        type="primary",
    )

    st.markdown("---")

    # Step 3: Display Preview & Individual Download Buttons
    for file_name, file_info in processed_files.items():
        st.subheader(f"Processed: {file_name}")
        st.dataframe(file_info["df"].head())

        st.download_button(
            label=f"Download cleaned_{file_name}",
            data=file_info["csv_data"],
            file_name=f"cleaned_{file_name}",
            mime="text/csv",
            key=f"download_{file_name}",
        )
        st.write("---")
