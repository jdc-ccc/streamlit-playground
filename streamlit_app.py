# app.py — Dark mode, single masthead, no boxes, 3 editors (variables → ops → plot)
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import re
import base64
from io import BytesIO
from pathlib import Path

from streamlit_ace import st_ace

# Utilities you already have
from utils.js_renderer import render_copy_bubbles

# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Analytical Model Environment",
    layout="wide",
    page_icon="📈",
)

# -----------------------------------------------------------------------------
# Load CSS (dark mode / no boxes)
# -----------------------------------------------------------------------------
def load_css():
    with open("style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# -----------------------------------------------------------------------------
# Header with logo
# -----------------------------------------------------------------------------
def header_with_logo():
    with open("site-logo.png", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{encoded}" alt="The CCC logo" />'

    st.markdown(
        f"""
        <div class="cc-header">
            {logo_html}
            <span style="font-size:1.4rem;font-weight:700;">Sample Analytic Model Environment</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

header_with_logo()

# -----------------------------------------------------------------------------
# Session state setup
# -----------------------------------------------------------------------------
if "workspace" not in st.session_state:
    st.session_state.workspace = {}

if "last_good_e1" not in st.session_state:
    st.session_state.last_good_e1 = ""

if "last_good_e2" not in st.session_state:
    st.session_state.last_good_e2 = ""

if "last_good_e3" not in st.session_state:
    st.session_state.last_good_e3 = ""

if "plot_pdf_bytes" not in st.session_state:
    st.session_state.plot_pdf_bytes = None

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def get_safe_builtins():
    return {
        "len": len, "range": range, "min": min, "max": max, "sum": sum,
        "abs": abs, "enumerate": enumerate, "zip": zip, "sorted": sorted,
        "list": list, "dict": dict, "set": set, "tuple": tuple,
        "float": float, "int": int, "str": str, "print": print,
        "any": any, "all": all, "map": map, "filter": filter,
    }


def exec_user_code(code, seed_locals, allowed_globals, protect_names):
    if not code:
        return True, seed_locals, None

    safe_globals = dict(allowed_globals)
    safe_globals["__builtins__"] = get_safe_builtins()

    loc = dict(seed_locals)

    try:
        exec(code, safe_globals, loc)
        user_vars = {
            k: v for k, v in loc.items()
            if (k not in protect_names and not k.startswith("_"))
        }
        return True, user_vars, None
    except Exception as e:
        return False, seed_locals, str(e)


def collect_exportables(workspace):
    exportables = {}
    for name, val in workspace.items():
        try:
            if isinstance(val, pd.DataFrame):
                for col in val.columns:
                    s = val[col]
                    if not isinstance(s, pd.Series):
                        s = pd.Series(s)
                    exportables[f"{name}.{col}"] = s.rename(f"{name}.{col}")

            elif isinstance(val, pd.Series):
                exportables[name] = val

            elif isinstance(val, (list, tuple, np.ndarray)):
                arr = np.asarray(val)
                if arr.ndim == 1:
                    exportables[name] = pd.Series(arr, name=name)

        except Exception:
            pass
    return exportables

# -----------------------------------------------------------------------------
# Default editor text
# -----------------------------------------------------------------------------
def get_default_e1(upload_var, cols):
    if upload_var and cols:
        col1 = cols[0]
        col2 = cols[1] if len(cols) > 1 else cols[0]
        col3 = cols[2] if len(cols) > 2 else cols[0]
        return f"""# Editor 1 — Define variables from the uploaded DataFrame.
# You can access your CSV as `{upload_var}`.

{col1} = {upload_var}['{col1}'].values
{col2} = {upload_var}['{col2}'].values
{col3} = {upload_var}['{col3}'].values
"""

def get_default_e2(upload_var, cols):
    if upload_var and cols:
        col1 = cols[0]
        col2 = cols[1] if len(cols) > 1 else cols[0]
        col3 = cols[2] if len(cols) > 2 else cols[0]
        return f"""# Editor 2 — Operate on variables defined in Editor 1.

{col2}_normalised = {col2} - np.mean({col2})
{col3}_pct = {col3}/100
"""


def get_default_e3(upload_var, cols):
    if upload_var and cols:
        col1 = cols[0]
        col2 = cols[1] if len(cols) > 1 else cols[0]
        col3 = cols[2] if len(cols) > 2 else cols[0]
    return f"""# Editor 3 — Create a Matplotlib plot.
fig, ax = plt.subplots(figsize=(8, 3))

ax.plot({col1}, {col2}_normalised, label='{col2}')
ax.plot({col1}, {col3}_pct, label='{col3} %')

ax.set_xlabel('{col1}')
ax.set_ylabel('Normalised Demand')
ax.legend()

"""

# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------
left, right = st.columns([0.55, 0.45])

with left:
    st.markdown("### Data")

    uploaded = st.file_uploader("Upload a .csv data file", type=["csv"])

    # -------------------------------------------------------------------------
    # --- SAFE CSV UPLOAD BLOCK ----------------------------------------------
    # -------------------------------------------------------------------------
    csv_df, csv_cols, upload_var = None, [], None

    if uploaded is None:
        st.info("Upload a CSV to continue.")
        st.stop()

    try:
        csv_df = pd.read_csv(uploaded)
    except Exception:
        st.info("Reading CSV… waiting for upload to complete")
        st.stop()

    if csv_df.empty and len(csv_df.columns) == 0:
        st.info("CSV uploaded but contains no columns. Waiting…")
        st.stop()

    csv_cols = list(csv_df.columns)
    upload_var = Path(uploaded.name).stem
    # -------------------------------------------------------------------------

    st.markdown("Columns in uploaded file:")
    render_copy_bubbles(csv_cols, upload_var)

    # -------------------------------------------------------------------------
    # Initialise/edit editors
    # -------------------------------------------------------------------------
    st.markdown("### Data Sources")

    if (
        st.session_state.last_good_e1.startswith("# Editor 1 — Define variables (no CSV uploaded yet)")
        or not st.session_state.last_good_e1
    ):
        st.session_state.last_good_e1 = get_default_e1(upload_var, csv_cols)

    if not st.session_state.last_good_e2:
        st.session_state.last_good_e2 = get_default_e2(upload_var, csv_cols)

    if not st.session_state.last_good_e3:
        st.session_state.last_good_e3 = get_default_e3(upload_var, csv_cols)

    e1_code = st_ace(
        value=st.session_state.last_good_e1,
        language="python",
        theme="monokai",
        key="ace-editor-1",
        font_size=14,
        min_lines=12,
        max_lines=40,
    )

    st.markdown("### Edit Model")
    e2_code = st_ace(
        value=st.session_state.last_good_e2,
        language="python",
        theme="monokai",
        key="ace-editor-2",
        font_size=14,
        min_lines=10,
        max_lines=40,
    )

    st.markdown("### Visualise Model")
    e3_code = st_ace(
        value=st.session_state.last_good_e3,
        language="python",
        theme="monokai",
        key="ace-editor-3",
        font_size=14,
        min_lines=10,
        max_lines=40,
    )

# -----------------------------------------------------------------------------
# Evaluate Editor 1
# -----------------------------------------------------------------------------
error_e1 = None
error_e2 = None
error_e3 = None

allowed_globals = {"np": np, "pd": pd, "math": math, "re": re}
protect = set(allowed_globals.keys()) | {"__builtins__"}

seed_e1 = {upload_var: csv_df}
seed_e1.update(st.session_state.workspace)

ok1, new1, error_e1 = exec_user_code(
    e1_code, seed_e1, allowed_globals, protect
)

if ok1:
    st.session_state.workspace.update(new1)
    st.session_state.last_good_e1 = e1_code

# -----------------------------------------------------------------------------
# Evaluate Editor 2
# -----------------------------------------------------------------------------
seed_e2 = dict(st.session_state.workspace)
ok2, new2, error_e2 = exec_user_code(
    e2_code, seed_e2, allowed_globals, protect
)

if ok2:
    st.session_state.workspace.update(new2)
    st.session_state.last_good_e2 = e2_code

# -----------------------------------------------------------------------------
# Right pane: plotting + export
# -----------------------------------------------------------------------------
with right:
    st.markdown("### Output")

    plt.rcParams.update({
        "figure.facecolor": "#29004A",
        "axes.facecolor":   "#29004A",
        "axes.edgecolor":   "#d5d2dc",
        "axes.labelcolor":  "#FFFFFF",
        "text.color":       "#FFFFFF",
        "xtick.color":      "#FFFFFF",
        "ytick.color":      "#FFFFFF",
        "grid.color":       "#78717d",
        "grid.alpha":       0.5,
        "axes.grid":        True,
        "legend.frameon":   False,
    })

    seed_e3 = dict(st.session_state.workspace)
    plot_globals = dict(allowed_globals)
    plot_globals["plt"] = plt
    ok3, new3, error_e3 = exec_user_code(
        e3_code, seed_e3, plot_globals, set(plot_globals.keys())
    )

    fig = None
    if ok3:
        fig = new3.get("fig", plt.gcf())
        st.session_state.last_good_e3 = e3_code

    if fig:
        st.pyplot(fig)

        buf = BytesIO()
        try:
            fig.savefig(buf, format="pdf", bbox_inches="tight")
            buf.seek(0)
            st.session_state.plot_pdf_bytes = buf.getvalue()
        except:
            st.session_state.plot_pdf_bytes = None

    # Errors
    if error_e1:
        st.error(f"[Editor 1] {error_e1}")
    if error_e2:
        st.error(f"[Editor 2] {error_e2}")
    if error_e3:
        st.error(f"[Editor 3] {error_e3}")

    # Export
    st.markdown("### Export Data")
    exportables = collect_exportables(st.session_state.workspace)

    if not exportables:
        st.info("No exportable Series or DataFrames found.")
    else:
        opts = list(exportables.keys())
        selected = st.multiselect("Choose columns:", opts, default=opts)
        if selected:
            try:
                df_export = pd.concat([exportables[n] for n in selected], axis=1)
                st.download_button(
                    "Download CSV",
                    df_export.to_csv(index=False).encode("utf-8"),
                    "processed_data.csv",
                    "text/csv"
                )
            except Exception as e:
                st.error(f"Export error: {e}")

    if st.session_state.plot_pdf_bytes:
        st.download_button(
            "Download Plot PDF",
            st.session_state.plot_pdf_bytes,
            "plot.pdf",
            "application/pdf",
        )