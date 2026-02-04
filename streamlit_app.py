import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from streamlit_ace import st_ace
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
    st.markdown("### Define the domain `x`")
    user_x_code = st_ace(
        value=st.session_state.last_good_x_code,
        language="python",
        theme="tomorrow_night_bright",
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
        theme="tomorrow_night_bright",
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

# --- Evaluate x code first ---
try:
    safe_globals_x = {"np": np, "math": math, "__builtins__": {}}
    local_env_x = {}
    exec(user_x_code, safe_globals_x, local_env_x)

    if "x" not in local_env_x:
        raise ValueError("No variable named x was defined.")

    x_candidate = np.asarray(local_env_x["x"])
    # Flatten to 1D for plotting
    x_candidate = np.ravel(x_candidate)

    if x_candidate.size == 0:
        raise ValueError("x is empty. Please provide at least one point.")

    # Basic numeric check
    if not np.issubdtype(x_candidate.dtype, np.number):
        raise ValueError("x must be numeric (int/float).")

    # Commit x
    st.session_state.x_arr = x_candidate
    st.session_state.last_good_x_code = user_x_code
    x = x_candidate

except Exception as e:
    error_x_message = str(e)
    # Fallback to last good x
    x = st.session_state.x_arr

# --- Evaluate g(x) code next ---
try:
    safe_globals_g = {"np": np, "math": math, "__builtins__": {}}
    local_env_g = {}
    exec(user_g_code, safe_globals_g, local_env_g)

    if "g" not in local_env_g or not callable(local_env_g["g"]):
        raise ValueError("No function named g(x) was defined.")

    candidate_g = local_env_g["g"]

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
