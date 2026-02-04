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
