import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from streamlit_ace import st_ace

import pandas as pd
from pathlib import Path

import re

from utils.py2latex import extract_return_expression, python_to_latex


default_x_code = """# Define the domain array x (1D)
x = np.linspace(-5, 5, 400)
"""

default_g_code = """# Define a function g(x) that accepts a NumPy array and returns an array
def g(x):
    return np.sin(x)
"""

# --- Page layout (wide) ---
st.set_page_config(layout="wide")



# -----------------------------
# Session state
# -----------------------------
if "x_arr" not in st.session_state:
    st.session_state.x_arr = np.linspace(-5, 5, 400)
if "last_good_x_code" not in st.session_state:
    st.session_state.last_good_x_code = default_x_code

if "g_func" not in st.session_state:
    st.session_state.g_func = lambda x: np.sin(x)
if "last_good_g_code" not in st.session_state:
    st.session_state.last_good_g_code = default_g_code



# -----------------------------
# Layout: left = code editors, right = output
# -----------------------------
left, right = st.columns([0.55, 0.45])

with left:

   # --- CSV upload  ---
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

    # --- Show column header "bubbles" when a CSV is present ---
    if csv_df is not None and csv_cols:
        st.markdown("**CSV Columns:**", help="Click-to-copy not wired; these are just visual labels.")
        badges = " ".join(
            [f"<span style='display:inline-block; padding:4px 10px; margin:2px; "
            f"background:#eef2ff; color:#1f3a8a; border:1px solid #c7d2fe; border-radius:999px; "
            f"font-size:12px; font-family:ui-sans-serif,system-ui;'>"
            f"{c}</span>" for c in csv_cols]
        )
        st.markdown(badges, unsafe_allow_html=True)

    
    if csv_df is not None and csv_cols:
        first_col = csv_cols[0]
        st.session_state.last_good_x_code = f"x = {upload_var}['{first_col}'].values"


    st.markdown("### Define the domain `x`")
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

    st.markdown("### Define the function `g(x)`")
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

# -----------------------------
# Evaluation / validation
# -----------------------------
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
    if csv_df is not None and upload_var:
        safe_globals_x[upload_var] = csv_df  # e.g. mydata = <DataFrame>
        safe_globals_x["df"] = csv_df        # optional convenience alias

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
    candidate_g = env_g["g"]    


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

# -----------------------------
# Right column: outputs
# -----------------------------
with right:
    st.markdown("### Output")
    st.latex(r"y = g(x)")
    st.latex(latex_text)

    # Plot
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(x, y, label="g(x)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", frameon=False)
    st.pyplot(fig)

    # Error banners below plot
    if error_x_message:
        st.error(f"[x] {error_x_message}")
    if error_g_message:
        st.error(f"[g(x)] {error_g_message}")
