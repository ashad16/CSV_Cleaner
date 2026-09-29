import io
import zipfile
import pandas as pd
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CSV Link & Address Isolator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- USER CREDENTIALS ---
USER_CREDENTIALS = {
    "admin": "admin123",
    "user": "password123",
    "noor": "noor123",
    "safdar": "safdar123",
}

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- LOGIN & LOGOUT HELPERS ---
def login():
    username_input = st.session_state.get("login_username", "").strip()
    password_input = st.session_state.get("login_password", "").strip()
    
    if username_input in USER_CREDENTIALS and USER_CREDENTIALS[username_input] == password_input:
        st.session_state.authenticated = True
        st.session_state.username = username_input
        st.session_state.login_error = False
    else:
        st.session_state.login_error = True

def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.pop("login_username", None)
    st.session_state.pop("login_password", None)


# --- LOGIN INTERFACE ---
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .login-card {
            max-width: 420px;
            margin: 5rem auto 2rem auto;
            padding: 2.5rem;
            border-radius: 12px;
            background-color: #ffffff;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid #e0e0e0;
        }
        .login-title {
            text-align: center;
            color: #1e3c72;
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            text-align: center;
            color: #6c757d;
            font-size: 0.95rem;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">🔒 Dashboard Access</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Please enter your credentials to proceed.</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.text_input("Username", key="login_username")
            st.text_input("Password", type="password", key="login_password")
            submit_button = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submit_button:
                login()

        if st.session_state.get("login_error", False):
            st.error("❌ Invalid username or password.")
            
    st.stop()


# --- DASHBOARD APP (AUTHENTICATED USERS) ---

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
    </style>
""", unsafe_allow_html=True)


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
    st.markdown(f"**Logged in as:** `{st.session_state.username}`")
    st.button("Logout", on_click=logout, type="secondary")
    st.markdown("---")
    st.title("Processing Rules")
    st.info("""
    ℹ️ **Applied Rules:**
    1. Only **Link** (Empty) and **Correspondence Address** retained.
    2. All completely blank rows & empty address lines removed.
    3. Extra spacing between rows cleared.
    """)

# --- HERO HEADER ---
st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">🔬 CSV Format Modifier</h1>
        <p class="hero-subtitle">Retain Link & Address columns and purge all blank lines automatically.</p>
    </div>
""", unsafe_allow_html=True)

# --- FILE UPLOAD AREA ---
st.subheader("1. Select & Upload Files")
uploaded_files = st.file_uploader(
    "Choose CSV files (Max 20 files at a time)",
    type=["csv"],
    accept_multiple_files=True,
    help="Drag and drop your raw CSV files here."
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
    with st.spinner("Processing CSV files and purging blank lines... Please wait."):
        for uploaded_file in uploaded_files:
            df = load_csv_safely(uploaded_file)
            original_cols_count = len(df.columns)
            original_rows_count = len(df)

            target_col = "Correspondence Address"

            # Check if target column exists
            if target_col in df.columns:
                corr_data = df[target_col]
            else:
                corr_data = pd.Series([""] * len(df))

            # Reconstruct DataFrame with ONLY 'Link' and 'Correspondence Address'
            df_cleaned = pd.DataFrame({
                "Link": [""] * len(df),
                "Correspondence Address": corr_data
            })

            # --- BLANK ROW & SPACING CLEANUP ---
            # 1. Clean whitespace from strings
            df_cleaned["Correspondence Address"] = df_cleaned["Correspondence Address"].astype(str).str.strip()

            # 2. Replace empty strings / 'nan' with actual NaN for dropping
            df_cleaned["Correspondence Address"].replace(["", "nan", "None", "NaN"], pd.NA, inplace=True)

            # 3. Drop all rows where 'Correspondence Address' is blank/NaN
            df_cleaned.dropna(subset=["Correspondence Address"], inplace=True)

            # 4. Reset index for seamless continuity
            df_cleaned.reset_index(drop=True, inplace=True)

            cleaned_rows_count = len(df_cleaned)

            # Convert cleaned df to CSV string
            csv_buffer = io.StringIO()
            df_cleaned.to_csv(csv_buffer, index=False, encoding="utf-8")

            # Save result to dictionary
            processed_files[uploaded_file.name] = {
                "df": df_cleaned,
                "csv_data": csv_buffer.getvalue(),
                "original_cols": original_cols_count,
                "cleaned_cols": len(df_cleaned.columns),
                "original_rows": original_rows_count,
                "cleaned_rows": cleaned_rows_count,
                "removed_blanks": original_rows_count - cleaned_rows_count
            }

    # ZIP File Generation
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, file_info in processed_files.items():
            zip_file.writestr(f"cleaned_{file_name}", file_info["csv_data"])

    # --- SUMMARY METRICS DASHBOARD ---
    st.markdown("---")
    st.subheader("2. Summary & Downloads")
    
    total_removed_blanks = sum(info["removed_blanks"] for info in processed_files.values())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Uploaded Files", value=total_files)
    with col2:
        st.metric(label="Status", value="Complete ✅")
    with col3:
        st.metric(label="Columns Retained", value="2 (Link & Address)")
    with col4:
        st.metric(label="Blank Rows Removed", value=total_removed_blanks)

    st.write("")

    # Bulk ZIP Download Button
    st.download_button(
        label=f"📦 Download All ({total_files}) Cleaned CSVs (ZIP Archive)",
        data=zip_buffer.getvalue(),
        file_name="cleaned_csv_files.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True
    )

    st.markdown("---")

    # --- TABBED PREVIEW & INDIVIDUAL DOWNLOADS ---
    st.subheader("3. Preview & Individual Downloads")
    st.caption("Inspect the cleaned datasets (empty lines removed).")

    # Render files inside tabs to avoid clutter
    tab_labels = [f"📄 {name}" for name in processed_files.keys()]
    tabs = st.tabs(tab_labels)

    for tab, (file_name, file_info) in zip(tabs, processed_files.items()):
        with tab:
            st.markdown(f"**Filename:** `{file_name}`")
            st.caption(
                f"Original Rows: **{file_info['original_rows']}** | "
                f"Cleaned Rows: **{file_info['cleaned_rows']}** | "
                f"Blank Lines Removed: **{file_info['removed_blanks']}**"
            )
            
            # Preview dataframe
            st.dataframe(file_info["df"].head(10), use_container_width=True)

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
    st.info("👆 Upload one or more CSV files to clean empty lines and isolate Link & Address columns.")
