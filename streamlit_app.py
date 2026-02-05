# app.py — Refactored with brand styling and header (site-logo.png)
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from streamlit_ace import st_ace

import pandas as pd
from pathlib import Path
import re
from base64 import b64encode

from utils.py2latex import extract_return_expression, python_to_latex
from utils.js_renderer import render_copy_bubbles

# -----------------------------------------------------------------------------
# Defaults (logic unchanged)
# -----------------------------------------------------------------------------
default_x_code = """# Define the domain array x (1D)
x = np.linspace(-5, 5, 400)
"""

default_g_code = """# Define a function g(x) that accepts a NumPy array and returns an array
def g(x):
    return np.sin(x)
"""

# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="g(x) Explorer",
    layout="wide",
    page_icon="📈",
)

# -----------------------------------------------------------------------------
# Brand CSS (derived from design_styleguide.yaml)
# - Colours, type, spacing, buttons, links, alerts, cards, selection etc.
# -----------------------------------------------------------------------------
BRAND_CSS = """
<style>
:root{
  /* Core brand palette */
  --plum: #29004A;         /* structural, headings, buttons */
  --purple: #7142FF;       /* primary: links, borders, header */
  --amber: #FFAC00;        /* accent: hovers, highlights */
  --white: #FFFFFF;
  --text: #29004A;

  /* Neutrals */
  --grey-1: #F7F5F8;       /* panels, filters, cards */
  --grey-2: #d5d2dc;       /* dividers */
  --grey-3: #78717d;       /* metadata */

  /* Typography */
  --font-body: "Century Gothic", sans-serif;
  --font-headings: "Century Gothic", sans-serif;
  --size-body: 1.0125rem;
  --h1: 1.944rem;
  --h2: 1.8rem;
  --h3: 1.647rem;

  /* Spacing & radii */
  --radius-sm: 4px;
  --content-max: 1260px;

  /* Shadows */
  --shadow-card: 0 2px 3px rgba(0,0,0,0.3);
}

/* Constrain content width while preserving Streamlit wide layout */
.main > div {
  max-width: var(--content-max);
  margin: 0 auto;
}

/* Body & headings */
html, body, [class*="st-"] {
  font-family: var(--font-body);
  color: var(--text);
  font-size: var(--size-body);
}

h1, h2, h3, .cc-h1, .cc-h2, .cc-h3 {
  font-family: var(--font-headings);
  font-weight: 700;
  color: var(--purple);
  letter-spacing: 0.01em;
}
.cc-h1 { font-size: var(--h1); margin-bottom: 0.75rem; }
.cc-h2 { font-size: var(--h2); margin-top: 1.25rem; margin-bottom: 0.5rem; }
.cc-h3 { font-size: var(--h3); margin-top: 1rem; margin-bottom: 0.5rem; }

/* Masthead */
.cc-header {
  position: sticky; top: 0; z-index: 9999;
  display: flex; align-items: center; gap: 1rem;
  background: var(--purple);
  color: var(--white);
  padding: 0.75rem 1rem;
  border-bottom: 4px solid var(--amber);
}
.cc-header .logo {
  height: 36px; width: auto; display: block;
}
.cc-header .title {
  font-size: 1.2rem; font-weight: 700; margin: 0;
}

/* Cards/panels (wrapping the editors and outputs) */
.cc-card {
  background: var(--grey-1);
  border: 1px solid var(--purple);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
  padding: 1rem;
  margin-bottom: 1rem;
}

/* Links */
a, .stMarkdown a {
  color: var(--purple);
  text-decoration: none;
  border-bottom: 2px solid transparent;
}
a:hover, .stMarkdown a:hover, a:focus-visible {
  text-decoration: underline;
  text-decoration-thickness: 3px; /* thicker for clarity */
}

/* Buttons (primary) */
div.stButton > button[kind="primary"], div.stDownloadButton > button {
  background: var(--plum);
  color: var(--white);
  border-radius: var(--radius-sm);
  border: 1px solid var(--plum);
}
div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button:hover {
  background: var(--purple);
  border-color: var(--purple);
}
div.stButton > button[kind="primary"]:active,
div.stDownloadButton > button:active {
  background: var(--amber) !important;
  border-color: var(--amber) !important;
  color: var(--plum) !important;
}

/* Alerts (st.error etc.) – add brand left border & subtle bg */
.stAlert > div {
  border-left: 6px solid var(--amber);
}

/* File uploader and ACE editor wrapper */
.cc-card .upload, .cc-card .editor {
  background: var(--white);
  border: 1px solid var(--grey-2);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
}

/* Tables & multiselect chips */
.css-1y4p8pa, .stMultiSelect, .stDataFrame { /* selector fallbacks as Streamlit evolves */
  border-radius: var(--radius-sm);
}

/* Selection & Focus for accessibility */
::selection {
  background: var(--plum);
  color: var(--white);
}
*:focus-visible {
  outline: 3px solid var(--amber);
  outline-offset: 2px;
}
</style>
"""
st.markdown(BRAND_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Helper: embed logo as base64 for reliable delivery in header
# -----------------------------------------------------------------------------
def get_base64_logo(path="site-logo.png"):
    try:
        with open(path, "rb") as f:
            return b64encode(f.read()).decode("utf-8")
    except Exception:
        return None

logo_b64 = get_base64_logo()

# -----------------------------------------------------------------------------
# Header (masthead with logo)
# -----------------------------------------------------------------------------
if logo_b64:
    header_html = f"""
    <header class="cc-header">
      <img class="logo" alt="Site logo" src="data:image/png;base64,{logo_b64}" />
      <p class="title">g(x) Explorer</p>
    </header>
    """
else:
    header_html = """
    <header class="cc-header">
      <p class="title">g(x) Explorer</p>
    </header>
    """
st.markdown(header_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Session state (logic preserved)
# -----------------------------------------------------------------------------
if "x_arr" not in st.session_state:
    st.session_state.x_arr = np.linspace(-5, 5, 400)
if "last_good_x_code" not in st.session_state:
    st.session_state.last_good_x_code = default_x_code

if "g_func" not in st.session_state:
    st.session_state.g_func = lambda x: np.sin(x)
if "last_good_g_code" not in st.session_state:
    st.session_state.last_good_g_code = default_g_code

# -----------------------------------------------------------------------------
# Layout: left = code editors & data, right = output (wrapped in branded cards)
# -----------------------------------------------------------------------------
left, right = st.columns([0.55, 0.45])

with left:
    with st.container():
        st.markdown('<div class="cc-card">', unsafe_allow_html=True)

        # --- CSV upload  ---
        st.markdown("### Define your data", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"], key="csv_uploader")

        csv_df = None
        csv_cols = []
        upload_var = None  # name to expose the DataFrame in the editor's namespace

        if uploaded is not None:
            try:
                csv_df = pd.read_csv(uploaded)
                csv_cols = list(csv_df.columns)
                upload_var = Path(uploaded.name).stem  # e.g. "mydata" from "mydata.csv"

                # Store so we keep it if reruns happen
                st.session_state["_csv_df"] = csv_df
                st.session_state["_csv_cols"] = csv_cols
                st.session_state["_upload_var"] = upload_var

            except Exception as e:
                st.error(f"CSV error: {e}")

        # In case of reruns without a new upload, restore
        if uploaded is None and "_csv_df" in st.session_state:
            csv_df = st.session_state["_csv_df"]
            csv_cols = st.session_state["_csv_cols"]
            upload_var = st.session_state["_upload_var"]

        if csv_df is not None and csv_cols:
            st.markdown("Click to copy column names into the editor below:")
            render_copy_bubbles(csv_cols, upload_var)

        if csv_df is not None and csv_cols:
            first_col = csv_cols[0]
            st.session_state.last_good_x_code = f"x = {upload_var}['{first_col}'].values"

        st.markdown('<div class="cc-h3">Define the domain <code>x</code></div>', unsafe_allow_html=True)
        user_x_code = st_ace(
            value=st.session_state.last_good_x_code,
            language="python",
            theme="solarized_light",
            keybinding="vscode",
            show_gutter=True,
            show_print_margin=False,
            wrap=False,
            font_size=14,
            tab_size=4,
            min_lines=6,
            max_lines=20,
            auto_update=True,
            key="ace-editor-x",
        )

        st.markdown('<div class="cc-h3">Define the function <code>g(x)</code></div>', unsafe_allow_html=True)
        user_g_code = st_ace(
            value=st.session_state.last_good_g_code,
            language="python",
            theme="solarized_light",
            keybinding="vscode",
            show_gutter=True,
            show_print_margin=False,
            wrap=False,
            font_size=14,
            tab_size=4,
            min_lines=8,
            max_lines=30,
            auto_update=True,
            key="ace-editor-g",
        )

        st.markdown('</div>', unsafe_allow_html=True)  # end .cc-card

# -----------------------------------------------------------------------------
# Evaluation / validation (logic preserved)
# -----------------------------------------------------------------------------
error_x_message = None
error_g_message = None

# --- If editors are empty, keep previous code ---
if not user_x_code:
    user_x_code = st.session_state.last_good_x_code
if not user_g_code:
    user_g_code = st.session_state.last_good_g_code

# --- Evaluate x code ---
try:
    safe_globals_x = {"np": np, "math": math, "pd": pd, "__builtins__": {}}
    local_env_x = {}

    # If a CSV is present, inject it so user can refer to it by <upload_var>
    if 'csv_df' in locals() and csv_df is not None and upload_var:
        safe_globals_x[upload_var] = csv_df  # e.g. mydata = <DataFrame>
        safe_globals_x["df"] = csv_df        # convenience alias

    exec(user_x_code, safe_globals_x, local_env_x)

    if "x" not in local_env_x:
        raise ValueError("No variable named x was defined.")
 
    x_candidate = local_env_x["x"]
    x = x_candidate
    st.session_state.x_arr = x_candidate
    st.session_state.last_good_x_code = user_x_code

except Exception as e:
    error_x_message = str(e)
    x = st.session_state.x_arr

# --- Evaluate g(x) code ---
try:
    env_g = {"np": np, "math": math, "__builtins__": {}}
    exec(user_g_code, env_g)

    if "g" not in env_g or not callable(env_g["g"]):
        raise ValueError("No function named g(x) was defined.")

    candidate_g = env_g["g"]

    # Test on current x
    y_test = candidate_g(x)
    y_test = np.asarray(y_test)

    if y_test.shape != x.shape:
        try:
            y_test = y_test + 0 * x  # attempt to broadcast to shape of x
        except Exception:
            raise ValueError(
                f"g(x) returned shape {y_test.shape}, which is not compatible with x shape {x.shape}."
            )

    # Commit g
    st.session_state.g_func = candidate_g
    st.session_state.last_good_g_code = user_g_code
    y = y_test

except Exception as e:
    error_g_message = str(e)
    try:
        y = st.session_state.g_func(x)
        y = np.asarray(y)
        if y.shape != x.shape:
            y = y + 0 * x
    except Exception as e2:
        # Final fallback to sine
        y = np.sin(x)
        if not error_g_message:
            error_g_message = str(e2)

# --- Prepare LaTeX for g(x) ---
return_expr = extract_return_expression(st.session_state.last_good_g_code)
if return_expr:
    latex_expr = python_to_latex(return_expr)
    latex_text = rf"g(x) = {latex_expr}"
else:
    latex_text = r"g(x) = \text{[unable to parse]}"

# -----------------------------------------------------------------------------
# Right column: outputs (branded card + themed plot)
# -----------------------------------------------------------------------------
with right:
    st.markdown('<div class="cc-card">', unsafe_allow_html=True)
    st.markdown("### Output")

    st.latex(r"y = g(x)")
    st.latex(latex_text)

    # --- Matplotlib theming (brand colours & legible grid)
    plt.rcParams.update({
        "axes.facecolor": "#FFFFFF",
        "axes.edgecolor": "#d5d2dc",             # grey-2
        "axes.labelcolor": "#29004A",            # text/plum
        "text.color": "#29004A",
        "xtick.color": "#29004A",
        "ytick.color": "#29004A",
        "grid.color": "#d5d2dc",
        "grid.alpha": 0.6,
        "axes.grid": True,
        "legend.frameon": False,
        "font.family": "sans-serif",
        "font.sans-serif": ["Century Gothic", "DejaVu Sans", "Arial"],
    })

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(x, y, label="g(x)", color="#7142FF", linewidth=2.25)  # purple
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(loc="upper right")
    st.pyplot(fig, clear_figure=True)

    # Error banners below plot (kept; styled via CSS)
    if error_x_message:
        st.error(f"[x] {error_x_message}")
    if error_g_message:
        st.error(f"[g(x)] {error_g_message}")

    # --- Build exportable DataFrame ---
    try:
        if isinstance(x, pd.DataFrame):
            df_out = x.copy()
            df_out["g(x)"] = y
        elif 'csv_df' in locals() and csv_df is not None:
            csv_df = csv_df.copy()
            csv_df['x'] = x
            csv_df['g(x)'] = y
            df_out = csv_df
        else:
            df_out = pd.DataFrame({"x": x, "g(x)": y})
    except Exception as e:
        st.error(f"Could not prepare CSV output: {e}")
        df_out = None

    if df_out is not None:
        st.markdown("### Select columns to include in export")
        out_cols = list(df_out.columns)
        csv_cols = list(df_out.columns) if 'csv_cols' not in locals() else csv_cols
        all_cols = list(dict.fromkeys(csv_cols + out_cols))

        selected_cols = st.multiselect(
            "Columns:",
            options=all_cols,
            default=all_cols,
        )

        # Apply selection
        df_export = df_out[selected_cols]
        csv_bytes = df_export.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download selected data as CSV",
            data=csv_bytes,
            file_name="processed_data.csv",
            mime="text/csv",
            type="primary",
        )

    st.markdown('</div>', unsafe_allow_html=True)  