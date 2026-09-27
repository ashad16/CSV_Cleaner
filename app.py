import io
import zipfile
import pandas as pd
import streamlit as st

# Set page config
st.set_page_config(
    page_title="Scopus CSV Cleaning Tool",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    /* Main Background Accent */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Hero Header Banner */
    .hero-container {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.2rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .hero-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #e0e6ed;
        margin-top: 0.4rem;
        margin-bottom: 0;
    }

    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e3c72;
    }

    /* Streamlit Download Buttons */
    .stDownloadButton button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    /* Card Container */
    .css-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Default columns to remove
DEFAULT_COLUMNS_TO_REMOVE = [
    "Editors", "Publisher", "ISSN", "ISBN", "CODEN",
    "PubMed ID", "Language of Original", "Language of Original Document",
    "Abbreviated Source Title", "Document Type", "Publication Stage",
    "Open Access", "Source", "EID"
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

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/ms-excel.png", width=60)
    st.title("Settings & Options")
    st.markdown("---")
    
    st.subheader("🧹 Cleaning Rules")
    st.caption("Customize which default Scopus metadata columns should be stripped.")
    
    columns_to_remove = st.multiselect(
        "Columns to remove:",
        options=DEFAULT_COLUMNS_TO_REMOVE,
        default=DEFAULT_COLUMNS_TO_REMOVE
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** Standard Scopus exports often include non-essential metadata. Removing them reduces file size significantly.")

# --- HERO HEADER ---
st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">🔬 Scopus Format Modifier</h1>
        <p class="hero-subtitle">Upload, clean, and reformat Scopus export files in batch effortlessly.</p>
    </div>
""", unsafe_allow_html=True)

# --- FILE UPLOAD AREA ---
st.subheader("1. Select & Upload Files")
uploaded_files = st.file_uploader(
    "Choose CSV files (Max 20 files at a time)",
    type=["csv"],
    accept_multiple_files=True,
    help="Drag and drop your raw Scopus export CSV files here."
)

if uploaded_files:
    total_files = len(uploaded_files)

    # File Limit Validation
    if total_files > 20:
        st.error(
            f"⚠️ **Limit Exceeded:** Maximum 20 files allowed at a time. You uploaded **{total_files}** files. "
            "Please remove extra files and try again."
        )
        st.stop()

    processed_files = {}

    # --- CSV PROCESSING ENGINE ---
    with st.spinner("Processing CSV files... Please wait."):
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
                "original_cols": len(df.columns) + len(cols_to_drop),
                "cleaned_cols": len(df.columns)
            }

    # ZIP File Generation
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, file_info in processed_files.items():
            zip_file.writestr(f"cleaned_{file_name}", file_info["csv_data"])

    # --- SUMMARY METRICS DASHBOARD ---
    st.markdown("---")
    st.subheader("2. Summary & Downloads")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Uploaded Files", value=total_files)
    with col2:
        st.metric(label="Processing Status", value="Complete ✅")
    with col3:
        st.metric(label="Target Columns Filtered", value=len(columns_to_remove))

    st.write("")

    # Bulk ZIP Download Button
    st.download_button(
        label=f"📦 Download All ({total_files}) Cleaned CSVs (ZIP Archive)",
        data=zip_buffer.getvalue(),
        file_name="cleaned_scopus_files.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True
    )

    st.markdown("---")

    # --- TABBED PREVIEW & INDIVIDUAL DOWNLOADS ---
    st.subheader("3. Preview & Individual Downloads")
    st.caption("Inspect the top 5 rows of each processed dataset below.")

    # Render files inside tabs to avoid clutter
    tab_labels = [f"📄 {name}" for name in processed_files.keys()]
    tabs = st.tabs(tab_labels)

    for tab, (file_name, file_info) in zip(tabs, processed_files.items()):
        with tab:
            st.markdown(f"**Filename:** `{file_name}`")
            
            # File info badges
            c1, c2 = st.columns([3, 1])
            with c1:
                st.caption(f"Original Columns: **{file_info['original_cols']}** | Cleaned Columns: **{file_info['cleaned_cols']}**")
            
            # Preview dataframe
            st.dataframe(file_info["df"].head(5), use_container_width=True)

            # Individual File Download Button
            st.download_button(
                label=f"⬇️ Download Cleaned {file_name}",
                data=file_info["csv_data"],
                file_name=f"cleaned_{file_name}",
                mime="text/csv",
                key=f"download_{file_name}",
                use_container_width=False
            )

else:
    # Empty State Guidance Card
    st.info("👆 Upload one or more Scopus CSV files to begin formatting.")
