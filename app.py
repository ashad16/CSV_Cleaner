import io
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSV Cleaner", layout="wide")
st.title("Scopus Format Modifier")

# Sirf yeh required columns hi output mein rahenge.
# Extra koi bhi column hoga toh woh automatic remove ho jayega.
REQUIRED_COLUMNS = [
    "Authors",
    "Author Full Names",
    "Author(s) ID",
    "Title",
    "Year",
    "Source title",
    "Volume",
    "Issue",
    "Art. No.",
    "Page start",
    "Page end",
    "Page count",
    "Cited by",
    "DOI",
    "Link",  # "Correspondence Address" se pehle empty link column
    "Affiliations",
    "Authors with affiliations",
    "Abstract",
    "Author Keywords",
    "Index Keywords",
    "Correspondence Address",
]


def load_csv_safely(uploaded_file):
    """Safely reads uploaded CSV by testing encodings, auto-detecting separators"""
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
    total_files = len(uploaded_files)

    # --- File Limit Validation ---
    if total_files > 20:
        st.error(
            f"⚠️ Maximum 20 files allowed at a time. You uploaded {total_files} files. Please remove extra files and try again."
        )
        st.stop()

    st.info(f"📁 **Total Files Uploaded:** {total_files}")

    processed_files = {}

    # Step 1: Process all files and strictly select required columns
    for uploaded_file in uploaded_files:
        df = load_csv_safely(uploaded_file)

        # Ensure 'Link' column exists as empty if it is not in the uploaded file
        if "Link" not in df.columns:
            df["Link"] = ""

        # Ensure all required columns exist in df (create blank if missing)
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        # Strictly select and reorder ONLY the required columns
        # (This automatically removes all other unwanted columns)
        df_cleaned = df[REQUIRED_COLUMNS]

        # Convert cleaned df to CSV string
        csv_buffer = io.StringIO()
        df_cleaned.to_csv(csv_buffer, index=False, encoding="utf-8")

        processed_files[uploaded_file.name] = {
            "df": df_cleaned,
            "csv_data": csv_buffer.getvalue(),
        }

    # Step 2: ZIP File Generation
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer, "w", zipfile.ZIP_DEFLATED
    ) as zip_file:
        for file_name, file_info in processed_files.items():
            zip_file.writestr(
                f"cleaned_{file_name}", file_info["csv_data"]
            )

    st.success(f"✅ Successfully processed {total_files} file(s)!")

    # ZIP download button
    st.download_button(
        label=f"📦 Download All {total_files} Cleaned CSVs as ZIP",
        data=zip_buffer.getvalue(),
        file_name="cleaned_csv_files.zip",
        mime="application/zip",
        type="primary",
    )

    st.markdown("---")

    # Step 3: Display Preview & Individual Downloads
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
