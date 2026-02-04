from streamlit.components.v1 import html

def render_copy_bubbles(cols, upload_var, title="CSV Columns"):
    """
    Render clickable 'chips' for each column that copy a snippet to clipboard:
    <upload_var>['<col>'](.values)
    """
    if not cols:
        return

    chips = []
    for col in cols:
        snippet = f"'{col}'"

        # Escape single quotes for JS string
        snippet_js = snippet.replace("'", "\\'")
        label_js = str(col).replace("'", "\\'")
        chips.append(
            f"""
            <button class="chip"
                onclick="navigator.clipboard.writeText('{snippet_js}');
                         const old=this.innerText; this.innerText='Copied!';
                         this.classList.add('copied');
                         setTimeout(()=>{{this.innerText='{label_js}'; this.classList.remove('copied')}}, 900);">
                {col}
            </button>
            """
        )

    html_content = f"""
    <div class="chips-wrap">
      <div class="chips-title">{title}</div>
      {''.join(chips)}
    </div>
    <style>
      .chips-title {{
        font-weight: 600; margin-bottom: 6px; font-size: 0.9rem;
      }}
      .chips-wrap .chip {{
        display:inline-block; margin:4px; padding:6px 12px;
        border-radius:999px; border:1px solid #c7d2fe;
        background:#eef2ff; color:#1f3a8a;
        cursor:pointer; font-size:12px; line-height:1;
        transition: all .15s ease;
      }}
      .chips-wrap .chip:hover {{
        background:#e0e7ff;
      }}
      .chips-wrap .chip.copied {{
        background:#dcfce7; border-color:#86efac; color:#166534;
      }}
    </style>
    """
    html(html_content, height=80)  # bump height if you have many columns