import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
from streamlit_ace import st_ace
import re


def python_to_latex(expr: str) -> str:
    expr = expr.strip()
    expr = expr.replace("np.", "").replace("math.", "")

    # exponentiation a**b → a^{b}
    expr = re.sub(r"(\w+)\*\*(\w+)", r"\1^{\2}", expr)

    # exp(x) → e^{x}
    expr = re.sub(r"exp\((.*?)\)", r"e^{\1}", expr)

    # Trig + log functions
    func_map = {
        "sin": r"\sin",
        "cos": r"\cos",
        "tan": r"\tan",
        "log": r"\log",
    }
    for key, val in func_map.items():
        expr = re.sub(
            rf"{key}\((.*?)\)",
            lambda m: f"{val}({m.group(1)})",
            expr
        )

    # Case 1: number * variable → number variable
    expr = re.sub(
        r"(\d+)\s*\*\s*([A-Za-z]\w*)",
        r"\1\2",
        expr
    )

    # Case 2: number * function_call → number function_call
    expr = re.sub(
        r"(\d+)\s*\*\s*(\\[A-Za-z]+)\(",
        r"\1\2(",
        expr
    )

    # Case 3: variable * variable → ab
    expr = re.sub(
        r"([A-Za-z]\w*)\s*\*\s*([A-Za-z]\w*)",
        r"\1\2",
        expr
    )

    # Everything else: a*b → a \times b
    expr = re.sub(
        r"(\S+)\s*\*\s*(\S+)",
        r"\1 \times \2",
        expr
    )

    return expr
    
def extract_return_expression(code_text):
    for line in code_text.splitlines():
        line = line.strip()
        if line.startswith("return "):
            return line[len("return "):]
    return None

st.latex(r"y = g(x)")

# --- Default editable code shown in the editor ---
default_code = """# Define a function g(x) that accepts a NumPy array and returns an array
def g(x):
    return np.sin(x)
"""

# --- Session state (last good function & code) ---
if "g_func" not in st.session_state:
    st.session_state.g_func = lambda x: np.sin(x)
if "last_good_code" not in st.session_state:
    st.session_state.last_good_code = default_code

# --- Editable code editor with line numbers & syntax highlighting ---
user_code = st_ace(
    value=st.session_state.last_good_code,
    language="python",                # Python syntax highlighting
    theme="tomorrow_night_bright",    # Ace theme (pick any you like)
    keybinding="vscode",              # Familiar keybindings
    show_gutter=True,                 # ← Line numbers
    show_print_margin=False,
    wrap=False,
    font_size=14,
    tab_size=4,
    min_lines=8,
    max_lines=30,
    auto_update=True,                 # Rerun on edits for "real-time" updates
    key="ace-editor",
)

# --- Domain for plotting ---
x = np.linspace(-5, 5, 400)
error_message = None

# --- If the editor is empty (rare), keep previous code ---
if not user_code:
    user_code = st.session_state.last_good_code

# --- Try to exec the code, and only commit if evaluation on x works ---
try:
    # Safe-ish globals: expose only what g(x) needs (no builtins/imports)
    safe_globals = {"np": np, "math": math, "__builtins__": {}}
    local_env = {}

    # Compile the user code
    exec(user_code, safe_globals, local_env)

    # Ensure g exists and is callable
    if "g" not in local_env or not callable(local_env["g"]):
        raise ValueError("No function named g(x) was defined.")

    candidate_g = local_env["g"]

    # Test-evaluate on x to validate before committing
    y_test = candidate_g(x)
    y_test = np.asarray(y_test)

    # Ensure output is broadcast-compatible with x
    if y_test.shape != x.shape:
        try:
            y_test = y_test + 0 * x
        except Exception:
            raise ValueError(
                f"g(x) returned shape {y_test.shape}, which is not compatible with x shape {x.shape}."
            )

    # If we got here, the function works → commit as the new "last good" state
    st.session_state.g_func = candidate_g
    st.session_state.last_good_code = user_code
    y = y_test

except Exception as e:
    # Keep the last good function/plot and show the error
    error_message = str(e)
    try:
        y = st.session_state.g_func(x)
    except Exception as e2:
        # Final fallback to sine if even the stored function fails
        y = np.sin(x)
        if not error_message:
            error_message = str(e2)

# --- Try to infer LaTeX from the function body ---
return_expr = extract_return_expression(st.session_state.last_good_code)

if return_expr:
    latex_expr = python_to_latex(return_expr)
    st.latex(rf"g(x) = {latex_expr}")
else:
    st.latex(r"g(x) = \text{[unable to parse]}")

# --- Plot ---
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(x, y, label="g(x)")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.grid(True, alpha=0.3)
ax.legend(loc="upper right", frameon=False)
st.pyplot(fig)

# --- Error banner (red) ---
if error_message:
    st.error(error_message)
