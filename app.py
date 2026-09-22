import io
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSV Cleaner", layout="wide")
st.title("CSV Header Cleaner & Modifier")

# List of columns to drop
columns_to_remove = [
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
]


def load_csv_safely(uploaded_file):
    """Safely reads uploaded CSV by testing encodings, auto-detecting separators,"""
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]

    for enc in encodings:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(
                uploaded_file,
                encoding=enc,
                sep=None,
                engine="python",
                on_bad_lines="skip",
            )
        except Exception:
            continue

    for enc in encodings:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(
                uploaded_file,
                encoding=enc,
                sep=",",
                on_bad_lines="skip",
            )
        except Exception:
            continue

    uploaded_file.seek(0)
    return pd.read_csv(
        uploaded_file,
        encoding="utf-8",
        encoding_errors="replace",
        on_bad_lines="skip",
    )


uploaded_files = st.file_uploader(
    "Upload CSV (Max 20 files)", type=["csv"], accept_multiple_files=True
)

if uploaded_files:
    # --- File Limit Validation ---
    if len(uploaded_files) > 20:
        st.error("⚠️ Maximum 20 files allowed at a time. Please remove extra files and try again.")
        st.stop()  # Prevents any downstream code execution

    processed_files = {}

    # Step 1: Process all files and store clean CSV string in memory
    for uploaded_file in uploaded_files:
        df = load_csv_safely(uploaded_file)

        # 1. Remove unwanted columns
        cols_to_drop = [col for col in columns_to_remove if col in df.columns]
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
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding="utf-8")

        # Save result to dictionary
        processed_files[uploaded_file.name] = {
            "df": df,
            "csv_data": csv_buffer.getvalue(),
        }

    # Step 2: ZIP File Generation Option
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer, "w", zipfile.ZIP_DEFLATED
    ) as zip_file:
        for file_name, file_info in processed_files.items():
            zip_file.writestr(
                f"cleaned_{file_name}", file_info["csv_data"]
            )

    st.success("All files processed successfully!")

    # Top ZIP download button for ALL files
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
