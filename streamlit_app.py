# app.py — Dark mode, no boxes, single header, corrected CSS/HTML
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from streamlit_ace import st_ace

import pandas as pd
from pathlib import Path
import re
import base64  # <-- use this (you can remove `from base64 import b64encode`)

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
#load CSS
# -----------------------------------------------------------------------------

def load_css():
    with open("style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ----------------------------------------------------------------------------- 
# Header with logo (single masthead)
# -----------------------------------------------------------------------------
def header_with_logo():
    try:
        with open("site-logo.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{encoded}" alt="Site logo" />'
    except Exception:
        logo_html = '<strong>g(x) Explorer</strong>'

    st.markdown(
        f"""
        <div class="cc-header">
            {logo_html}
            <span style="font-size:1.4rem;font-weight:700;">g(x) Explorer</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

header_with_logo()

# ----------------------------------------------------------------------------- 
# Session state (original logic)
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
# Layout: left = editors & data, right = output  (no decorative wrappers)
# -----------------------------------------------------------------------------
left, right = st.columns([0.55, 0.45])

with left:
    st.markdown("### Define your data")
    uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"], key="csv_uploader")

    csv_df, csv_cols, upload_var = None, [], None

    if uploaded is not None:
        try:
            csv_df = pd.read_csv(uploaded)
            csv_cols = list(csv_df.columns)
            upload_var = Path(uploaded.name).stem  # "mydata" from "mydata.csv"
            st.session_state["_csv_df"] = csv_df
            st.session_state["_csv_cols"] = csv_cols
            st.session_state["_upload_var"] = upload_var
        except Exception as e:
            st.error(f"CSV error: {e}")

    # Restore on rerun
    if uploaded is None and "_csv_df" in st.session_state:
        csv_df = st.session_state["_csv_df"]
        csv_cols = st.session_state["_csv_cols"]
        upload_var = st.session_state["_upload_var"]

    if csv_df is not None and csv_cols:
        st.markdown("Click to copy column names into the editor below:")
        render_copy_bubbles(csv_cols, upload_var)
        # Auto-set x to first column
        st.session_state.last_good_x_code = f"x = {upload_var}['{csv_cols[0]}'].values"

    # ---- Editors (use a dark ACE theme)
    st.markdown("#### Define the domain `x`")
    user_x_code = st_ace(
        value=st.session_state.last_good_x_code,
        language="python",
        theme="monokai",                 # dark theme
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

    st.markdown("#### Define the function `g(x)`")
    user_g_code = st_ace(
        value=st.session_state.last_good_g_code,
        language="python",
        theme="monokai",                 # dark theme
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

# ----------------------------------------------------------------------------- 
# Evaluation / validation (original logic)
# -----------------------------------------------------------------------------
error_x_message = None
error_g_message = None

if not user_x_code:
    user_x_code = st.session_state.last_good_x_code
if not user_g_code:
    user_g_code = st.session_state.last_good_g_code

# Evaluate x
try:
    safe_globals_x = {"np": np, "math": math, "pd": pd, "__builtins__": {}}
    local_env_x = {}
    if 'csv_df' in locals() and csv_df is not None and upload_var:
        safe_globals_x[upload_var] = csv_df
        safe_globals_x["df"] = csv_df

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

# Evaluate g(x)
try:
    env_g = {"np": np, "math": math, "__builtins__": {}}
    exec(user_g_code, env_g)
    if "g" not in env_g or not callable(env_g["g"]):
        raise ValueError("No function named g(x) was defined.")

    candidate_g = env_g["g"]
    y_test = np.asarray(candidate_g(x))

    if y_test.shape != x.shape:
        try:
            y_test = y_test + 0 * x
        except Exception:
            raise ValueError(
                f"g(x) returned shape {y_test.shape}, which is not compatible with x shape {x.shape}."
            )

    st.session_state.g_func = candidate_g
    st.session_state.last_good_g_code = user_g_code
    y = y_test
except Exception as e:
    error_g_message = str(e)
    try:
        y = np.asarray(st.session_state.g_func(x))
        if y.shape != x.shape:
            y = y + 0 * x
    except Exception as e2:
        y = np.sin(x)
        if not error_g_message:
            error_g_message = str(e2)

# LaTeX
return_expr = extract_return_expression(st.session_state.last_good_g_code)
latex_text = rf"g(x) = {python_to_latex(return_expr)}" if return_expr else r"g(x) = \text{[unable to parse]}"

# ----------------------------------------------------------------------------- 
# Right column: outputs (no box; dark plot theme)
# -----------------------------------------------------------------------------
with right:
    st.markdown("### Output")
    st.latex(r"y = g(x)")
    st.latex(latex_text)

    # Dark plot theme aligned to app background
    plt.rcParams.update({
        "figure.facecolor": "#29004A",   # plum
        "axes.facecolor":   "#29004A",   # plum
        "axes.edgecolor":   "#d5d2dc",   # grey-2
        "axes.labelcolor":  "#FFFFFF",
        "text.color":       "#FFFFFF",
        "xtick.color":      "#FFFFFF",
        "ytick.color":      "#FFFFFF",
        "grid.color":       "#78717d",   # grey-3
        "grid.alpha":       0.5,
        "axes.grid":        True,
        "legend.frameon":   False,
        "font.family":      "sans-serif",
        "font.sans-serif":  ["Century Gothic", "DejaVu Sans", "Arial"],
    })

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(x, y, label="g(x)", color="#FFAC00", linewidth=2.25)  # amber line pops on plum
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(loc="upper right")
    st.pyplot(fig, clear_figure=True)

    if error_x_message:
        st.error(f"[x] {error_x_message}")
    if error_g_message:
        st.error(f"[g(x)] {error_g_message}")

    # Export
    try:
        if isinstance(x, pd.DataFrame):
            df_out = x.copy()
            df_out["g(x)"] = y
        elif 'csv_df' in locals() and csv_df is not None:
            csv_df = csv_df.copy()
            csv_df["x"] = x
            csv_df["g(x)"] = y
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

        selected_cols = st.multiselect("Columns:", options=all_cols, default=all_cols)
        df_export = df_out[selected_cols]
        csv_bytes = df_export.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download selected data as CSV",
            data=csv_bytes,
            file_name="processed_data.csv",
            mime="text/csv",
            type="primary",
        )