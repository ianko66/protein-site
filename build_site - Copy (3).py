import os
import json
import pandas as pd
import plotly.graph_objects as go

# ---------- Site constants for SEO (safe defaults; tweak if you have your URL) ----------
SITE_NAME = os.environ.get("SITE_NAME", "Protein Visualizer")
SITE_URL  = os.environ.get("SITE_URL",  "https://example.com")  # set to your real domain later

# ---------- Paths ----------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_PATH = os.path.join(DATA_DIR, "foods.csv")

# ---------- Load & validate ----------
if not os.path.exists(DATA_PATH):
    raise SystemExit(f"❌ Data file not found: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

# Clean
df["Food"] = df["Food"].astype(str).str.strip()
for col in ["Calories_per_gram", "Protein_per_gram", "Cost_per_gram"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df["Category"] = df["Category"].astype(str).str.strip()

df = df.dropna(subset=["Food", "Calories_per_gram", "Protein_per_gram", "Cost_per_gram", "Category"])
df = df[df["Protein_per_gram"] > 0]
if df.empty:
    raise SystemExit("❌ No valid rows after cleaning. Check your CSV values.")

# ---------- Normalize to 10g protein ----------
df["Grams_for_10g_protein"]    = 10.0 / df["Protein_per_gram"]
df["Calories_for_10g_protein"] = df["Grams_for_10g_protein"] * df["Calories_per_gram"]
df["Cost_for_10g_protein"]     = df["Grams_for_10g_protein"] * df["Cost_per_gram"]

# ---------- Ranges ----------
x_max = float(df["Calories_for_10g_protein"].max() * 1.1)
y_max = float(df["Cost_for_10g_protein"].max() * 1.1)
z_max = float(df["Grams_for_10g_protein"].max() * 1.1)

# ---------- Colors ----------
fixed_colors = {
    "Vegetables": "#32CD32",
    "Grains": "#D2B48C",
    "Animal Protein": "#FF4500",
    "Plant Protein": "#228B22",
    "Supplement Protein": "#1E90FF",
    "Dairy": "#9370DB",

    # Expanded categories you added
    "Poultry": "#FF7F0E",
    "Fish & Seafood": "#1F77B4",
    "Red Meat & Game": "#8C564B",
    "Eggs": "#9467BD",
    "Legumes": "#2CA02C",
    "Soy": "#17BECF",
    "Nuts & Seeds": "#BCBD22",
    "Supplements": "#1E90FF",
}
fallback_palette = [
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF"
]
categories = sorted(df["Category"].unique().tolist())
color_map = {}
p = 0
for cat in categories:
    color_map[cat] = fixed_colors.get(cat, fallback_palette[p % len(fallback_palette)])
    if cat not in fixed_colors:
        p += 1

# =========================================================
# 3D PLOT
# =========================================================
fig3d = go.Figure()

# Points (one trace per category) — size 5 + black outline width 2
for cat in categories:
    sub = df[df["Category"] == cat]
    if sub.empty:
        continue
    fig3d.add_trace(go.Scatter3d(
        x=sub["Calories_for_10g_protein"],
        y=sub["Cost_for_10g_protein"],
        z=sub["Grams_for_10g_protein"],
        mode="markers",
        marker=dict(
            size=5,
            color=color_map[cat],
            opacity=0.9,
            line=dict(color="rgba(0,0,0,0.8)", width=2)
        ),
        text=sub["Food"],
        hovertemplate="<b>%{text}</b><br>"
                      "<b>Calories (per 10g protein):</b> %{x:.2f}<br>"
                      "<b>Cost (per 10g protein):</b> $%{y:.2f}<br>"
                      "<b>Weight, in grams (per 10g protein):</b> %{z:.2f}<br>"
                      "<extra></extra>",
        name=cat, legendgroup=cat
    ))

base_eye = dict(x=1.6, y=1.6, z=1.2)

fig3d.update_layout(
    # no visible title (cards on index provide titles)
    scene=dict(
        xaxis=dict(title="Calories (per 10g protein)", range=[0, x_max], ticks="outside"),
        yaxis=dict(title="Cost (per 10g protein)",     range=[0, y_max], tickprefix="$", tickformat=".2f", ticks="outside"),
        zaxis=dict(title="Weight, in grams (per 10g protein)", range=[0, z_max], ticks="outside"),
        camera=dict(eye=base_eye),
        aspectmode="cube"
    ),
    legend=dict(
        title="Categories",
        x=1.05, y=1,
        traceorder="normal",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(255,255,255,0.8)",
        borderwidth=2
    ),
    margin=dict(r=0, t=5, l=25, b=50)
)

# =========================================================
# Chart page writers (NO visible H1/intro inside iframes to avoid duplication)
# =========================================================
def write_custom_3d_html(fig, filename: str, base_eye_val: dict):
    """3D page for iframing: no visible H1/intro; has SEO head, hover box, and Reset that re-enables categories."""
    page_title = "3D — Calories vs Cost vs Weight (per 10g protein)"
    page_desc  = "Interactive 3D chart comparing weight (grams), cost, and calories per 10g protein across many foods and categories."

    fig.update_layout(height=740, width=850, showlegend=True)
    inner = fig.to_html(include_plotlyjs=False, full_html=False, div_id="plot3d",
                        config={"scrollZoom": True, "displaylogo": False})
    BASE_EYE_JSON = json.dumps(base_eye_val)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{page_title} — {SITE_NAME}</title>
<link rel="canonical" href="{SITE_URL}/3d_plot.html">
<meta name="description" content="{page_desc}">
<meta name="robots" content="index,follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{page_title} — {SITE_NAME}">
<meta property="og:description" content="{page_desc}">
<meta property="og:url" content="{SITE_URL}/3d_plot.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{page_title} — {SITE_NAME}">
<meta name="twitter:description" content="{page_desc}">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  html,body{{margin:0;padding:0;background:#fff;font-family:system-ui,Segoe UI,Roboto,Arial;}}
  .page{{max-width:1100px;margin:0 auto;padding:10px;}}
  .plot-wrapper{{}}
  .info-row{{display:flex;gap:12px;align-items:flex-start;margin-top:10px;}}
  .reset button{{
    background:#111;color:#fff;border:none;border-radius:8px;padding:8px 12px;
    font-size:14px;cursor:pointer;opacity:0.95;
  }}
  .reset button:hover{{opacity:1}}
  .infobox{{border:1px solid #e3e3e3;background:#fafafa;border-radius:8px;padding:10px;font-size:14px;
           width:520px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
  .kv{{display:grid;grid-template-columns:300px 1fr;gap:6px 10px;margin-top:6px;}}
  .k{{color:#666;}}
  noscript p{{font-size:14px;color:#444}}
</style>
</head>
<body>
  <div class="page">
    <div class="plot-wrapper">
      {inner}
      <noscript><p>JavaScript is required to view this interactive chart. See the <a href="/data_table.html">data table</a>.</p></noscript>
      <div class="info-row">
        <div class="infobox" id="selBox">Hover over a point to see values.</div>
        <div class="reset"><button id="resetBtn">Reset view</button></div>
      </div>
    </div>
  </div>
<script>
  const selBox = document.getElementById('selBox');
  const plotDiv = document.getElementById('plot3d');
  const BASE_EYE = {BASE_EYE_JSON};
  function fmtMoney(n){{ return '$' + Number(n).toFixed(2); }}
  function fmtNum(n){{ return Number(n).toFixed(2); }}

  // Reset via button (camera + categories)
  document.getElementById('resetBtn').addEventListener('click', function(){{
    Plotly.relayout('plot3d', {{'scene.camera.eye': BASE_EYE}});
    const traceIdxs = (plotDiv.data || [])
      .map((tr, i) => (tr && tr.type === 'scatter3d' ? i : null))
      .filter(i => i !== null);
    if (traceIdxs.length) {{
      Plotly.restyle('plot3d', {{ visible: true }}, traceIdxs);
    }}
  }});

  // Reset via double-click (camera + categories)
  plotDiv.on('plotly_doubleclick', function() {{
    Plotly.relayout('plot3d', {{'scene.camera.eye': BASE_EYE}});
    const traceIdxs = (plotDiv.data || [])
      .map((tr, i) => (tr && tr.type === 'scatter3d' ? i : null))
      .filter(i => i !== null);
    if (traceIdxs.length) {{
      Plotly.restyle('plot3d', {{ visible: true }}, traceIdxs);
    }}
  }});

  // Hover info
  plotDiv.on('plotly_hover', function(ev){{
    if(!ev || !ev.points || !ev.points.length) return;
    const p = ev.points[0];
    const name = p.text || '(unknown)';
    const cal = p.x, cost = p.y, grams = p.z;
    selBox.innerHTML =
      '<div><strong>' + name + '</strong></div>' +
      '<div class="kv">' +
        '<div class="k">Calories (per 10g protein):</div><div>' + fmtNum(cal) + '</div>' +
        '<div class="k">Cost (per 10g protein):</div><div>' + fmtMoney(cost) + '</div>' +
        '<div class="k">Weight, in grams (per 10g protein):</div><div>' + fmtNum(grams) + '</div>' +
      '</div>';
  }});
</script>
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


def write_custom_2d_html(fig, filename: str, xlabel: str, ylabel: str,
                         x_range=None, y_range=None,
                         money_x: bool=False, money_y: bool=False):
    """
    2D page for iframing: no visible H1/intro (to avoid duplication in index card),
    with SEO head, clamped axes, and Reset (also re-enables all categories).
    """
    title_map = {
        "2d_plot1.html": ("2D — Calories vs Cost (per 10g protein)",
                          "Interactive chart comparing calories vs cost per 10g protein across many foods and categories."),
        "2d_plot2.html": ("2D — Calories vs Weight (per 10g protein)",
                          "Interactive chart comparing calories per 10g protein vs grams required for 10g protein across many foods."),
        "2d_plot3.html": ("2D — Cost vs Weight (per 10g protein)",
                          "Interactive chart comparing cost per 10g protein vs grams required for 10g protein across many foods.")
    }
    page_title, page_desc = title_map.get(filename, (f"2D — {xlabel} vs {ylabel}", f"Interactive chart of {xlabel} vs {ylabel}."))

    plot_height = 490
    fig.update_layout(height=plot_height, width=800, showlegend=True, legend=dict(title="Category"),
                      margin=dict(t=5, l=50, r=0, b=50))

    if x_range is not None:
        fig.update_xaxes(range=x_range, autorange=False)
    if y_range is not None:
        fig.update_yaxes(range=y_range, autorange=False)

    x_fmt = "$%{x:.2f}" if money_x else "%{x:.2f}"
    y_fmt = "$%{y:.2f}" if money_y else "%{y:.2f}"
    hovertemplate = (
        "<b>%{text}</b><br>"
        + "<b>" + xlabel + ":</b> " + x_fmt + "<br>"
        + "<b>" + ylabel + ":</b> " + y_fmt
        + "<extra></extra>"
    )
    fig.update_traces(hovertemplate=hovertemplate)

    inner = fig.to_html(include_plotlyjs=False, full_html=False, div_id="plot2d",
                        config={"scrollZoom": True, "displaylogo": False})

    X_LABEL = json.dumps(xlabel)
    Y_LABEL = json.dumps(ylabel)
    MONEY_X = str(money_x).lower()
    MONEY_Y = str(money_y).lower()
    INIT_X_RANGE = json.dumps(x_range if x_range is not None else [0, None])
    INIT_Y_RANGE = json.dumps(y_range if y_range is not None else [0, None])

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{page_title} — {SITE_NAME}</title>
<link rel="canonical" href="{SITE_URL}/{filename}">
<meta name="description" content="{page_desc}">
<meta name="robots" content="index,follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{page_title} — {SITE_NAME}">
<meta property="og:description" content="{page_desc}">
<meta property="og:url" content="{SITE_URL}/{filename}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{page_title} — {SITE_NAME}">
<meta name="twitter:description" content="{page_desc}">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  html,body{{margin:0;padding:0;background:#fff;font-family:system-ui,Segoe UI,Roboto,Arial;}}
  .page{{max-width:1100px;margin:0 auto;padding:10px;}}
  .plot-wrapper{{}}
  .info-row{{display:flex;gap:12px;align-items:flex-start;margin-top:10px;}}
  .reset button{{
    background:#111;color:#fff;border:none;border-radius:8px;padding:8px 12px;
    font-size:14px;cursor:pointer;opacity:0.95;
  }}
  .reset button:hover{{opacity:1}}
  .infobox{{border:1px solid #e3e3e3;background:#fafafa;border-radius:8px;padding:10px;font-size:14px;
           width:520px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
  .kv{{display:grid;grid-template-columns:300px 1fr;gap:6px 10px;margin-top:6px;}}
  .k{{color:#666;}}
  noscript p{{font-size:14px;color:#444}}
</style>
</head>
<body>
  <div class="page">
    <div class="plot-wrapper">
      {inner}
      <noscript><p>JavaScript is required to view this interactive chart. See the <a href="/data_table.html">data table</a>.</p></noscript>
      <div class="info-row">
        <div class="infobox" id="selBox">Hover over a point to see values.</div>
        <div class="reset"><button id="resetBtn">Reset view</button></div>
      </div>
    </div>
  </div>
<script>
  const selBox = document.getElementById('selBox');
  const plotDiv = document.getElementById('plot2d');
  const HOV_X_LABEL = {X_LABEL};
  const HOV_Y_LABEL = {Y_LABEL};
  const MONEY_X = {MONEY_X};
  const MONEY_Y = {MONEY_Y};
  const INIT_X_RANGE = {INIT_X_RANGE};
  const INIT_Y_RANGE = {INIT_Y_RANGE};

  function fmtMoney(n){{ return '$' + Number(n).toFixed(2); }}
  function fmtNum(n){{ return Number(n).toFixed(2); }}

  // Reset View: restore ranges AND re-enable all categories
  document.getElementById('resetBtn').addEventListener('click', function(){{
    const relayout = {{}};
    if (INIT_X_RANGE) relayout['xaxis.range'] = INIT_X_RANGE;
    if (INIT_Y_RANGE) relayout['yaxis.range'] = INIT_Y_RANGE;
    Plotly.relayout('plot2d', relayout);

    const traceIdxs = (plotDiv.data || [])
      .map((tr, i) => (tr && tr.type === 'scatter' ? i : null))
      .filter(i => i !== null);
    if (traceIdxs.length) {{
      Plotly.restyle('plot2d', {{ visible: true }}, traceIdxs);
    }}
  }});

  // Clamp ranges so lower bound never goes below 0 (zoom AND pan)
  let clampGuard = false;
  plotDiv.on('plotly_relayout', function(e){{
    if (clampGuard) return;

    const wantsAutoX = (e && (e['xaxis.autorange'] === true));
    const wantsAutoY = (e && (e['yaxis.autorange'] === true));

    const xr = (plotDiv.layout.xaxis && plotDiv.layout.xaxis.range) ? plotDiv.layout.xaxis.range.slice() : null;
    const yr = (plotDiv.layout.yaxis && plotDiv.layout.yaxis.range) ? plotDiv.layout.yaxis.range.slice() : null;

    const initX = INIT_X_RANGE;
    const initY = INIT_Y_RANGE;

    let update = {{}};
    let changed = false;

    function currentMax(axisRange, layoutRange) {{
      if (axisRange && axisRange[1] != null) return axisRange[1];
      if (layoutRange && layoutRange.length === 2 && layoutRange[1] != null) return layoutRange[1];
      return 1;
    }}

    if (wantsAutoX) {{
      const xmax = currentMax(initX, xr);
      update['xaxis.range'] = [0, xmax];
      changed = true;
    }}
    if (wantsAutoY) {{
      const ymax = currentMax(initY, yr);
      update['yaxis.range'] = [0, ymax];
      changed = true;
    }}

    const xrNow = (update['xaxis.range'] ? update['xaxis.range'] : xr);
    const yrNow = (update['yaxis.range'] ? update['yaxis.range'] : yr);

    if (xrNow && xrNow.length === 2 && xrNow[0] < 0) {{
      const span = xrNow[1] - xrNow[0];
      update['xaxis.range'] = [0, Math.max(0 + span, 1e-9)];
      changed = true;
    }}
    if (yrNow && yrNow.length === 2 && yrNow[0] < 0) {{
      const span = yrNow[1] - yrNow[0];
      update['yaxis.range'] = [0, Math.max(0 + span, 1e-9)];
      changed = true;
    }}

    if (changed) {{
      clampGuard = true;
      Plotly.relayout('plot2d', update).then(function(){{ clampGuard = false; }});
    }}
  }});

  // Hover info
  plotDiv.on('plotly_hover', function(ev){{
    if(!ev || !ev.points || !ev.points.length) return;
    const p = ev.points[0];
    const name = p.text || '(unknown)';
    const xv = p.x, yv = p.y;
    const xStr = MONEY_X ? fmtMoney(xv) : fmtNum(xv);
    const yStr = MONEY_Y ? fmtMoney(yv) : fmtNum(yv);

    selBox.innerHTML =
      '<div><strong>' + name + '</strong></div>' +
      '<div class="kv">' +
        '<div class="k">' + HOV_X_LABEL + ':</div><div>' + xStr + '</div>' +
        '<div class="k">' + HOV_Y_LABEL + ':</div><div>' + yStr + '</div>' +
      '</div>';
  }});
</script>
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

# =========================================================
# Make 2D plots helper
# =========================================================
def make_2d(x, y, xlabel, ylabel, filename, xlim=None, ylim=None):
    """Create a 2D scatter per category, with proper money flags and axis money ticks."""
    fig = go.Figure()
    for cat in categories:
        sub = df[df["Category"] == cat]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub[x], y=sub[y], mode="markers",
            marker=dict(
                color=color_map[cat], size=9,
                line=dict(color="rgba(0,0,0,0.6)", width=1)
            ),
            name=cat, legendgroup=cat, text=sub["Food"]
        ))

    # Axis configs with conditional money tick formatting based on label text
    fig.update_xaxes(
        title_text=xlabel,
        range=xlim,
        autorange=False,
        showgrid=True, gridcolor="lightgray",
        zeroline=True, zerolinecolor="black", zerolinewidth=2,
        tickprefix="$" if "Cost" in xlabel else None,
        tickformat=".2f" if "Cost" in xlabel else None
    )
    fig.update_yaxes(
        title_text=ylabel,
        range=ylim,
        autorange=False,
        showgrid=True, gridcolor="lightgray",
        zeroline=True, zerolinecolor="black", zerolinewidth=2,
        tickprefix="$" if "Cost" in ylabel else None,
        tickformat=".2f" if "Cost" in ylabel else None
    )

    money_x = (x == "Cost_for_10g_protein")
    money_y = (y == "Cost_for_10g_protein")

    write_custom_2d_html(fig, filename, xlabel, ylabel,
                         x_range=xlim, y_range=ylim,
                         money_x=money_x, money_y=money_y)

# ---------- Build 2D pages ----------
make_2d("Calories_for_10g_protein","Cost_for_10g_protein",
        "Calories (per 10g protein)","Cost (per 10g protein)",
        "2d_plot1.html", xlim=[0, x_max], ylim=[0, 1])

make_2d("Calories_for_10g_protein","Grams_for_10g_protein",
        "Calories (per 10g protein)","Weight, in grams (per 10g protein)",
        "2d_plot2.html", xlim=[0, x_max], ylim=[0, z_max])

make_2d("Cost_for_10g_protein","Grams_for_10g_protein",
        "Cost (per 10g protein)","Weight, in grams (per 10g protein)",
        "2d_plot3.html", xlim=[0, 1], ylim=[0, z_max])

# ---------- Write 3D page ----------
write_custom_3d_html(fig3d, "3d_plot.html", base_eye)

# =========================================================
# Input Data Table page (sortable headers)
# =========================================================
def write_data_table_html(df: pd.DataFrame, filename: str = "data_table.html"):
    """Write a styled, sortable HTML table of the normalized per-10g protein data, with clean headers."""
    cols = ["Food", "Category", "Calories_for_10g_protein", "Cost_for_10g_protein", "Grams_for_10g_protein"]
    cols = [c for c in cols if c in df.columns]
    view = df[cols].copy()

    rename_map = {
        "Calories_for_10g_protein": "Calories",
        "Cost_for_10g_protein": "Cost",
        "Grams_for_10g_protein": "Weight (grams)"
    }
    view = view.rename(columns={k: v for k, v in rename_map.items() if k in view.columns})

    formatters = {}
    if "Calories" in view.columns:
        formatters["Calories"] = lambda v: f"{v:.2f}"
    if "Cost" in view.columns:
        formatters["Cost"] = lambda v: f"${v:.2f}"
    if "Weight (grams)" in view.columns:
        formatters["Weight (grams)"] = lambda v: f"{v:.2f}"

    table_html = view.to_html(
        index=False,
        escape=True,
        classes="datatable",
        border=0,
        justify="center",
        formatters=formatters
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Input Data — {SITE_NAME}</title>
<link rel="canonical" href="{SITE_URL}/data_table.html">
<meta name="description" content="Sortable table of calories, cost, and weight (grams) per 10g protein for foods and supplements.">
<meta name="robots" content="index,follow">
<meta property="og:type" content="website">
<meta property="og:title" content="Input Data — {SITE_NAME}">
<meta property="og:description" content="Sortable table of calories, cost, and weight (grams) per 10g protein for foods and supplements.">
<meta property="og:url" content="{SITE_URL}/data_table.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Input Data — {SITE_NAME}">
<meta name="twitter:description" content="Sortable table of calories, cost, and weight (grams) per 10g protein for foods and supplements.">
<style>
  html,body{{margin:0;padding:0;background:#fff;font-family:system-ui,Segoe UI,Roboto,Arial;}}
  .page{{max-width:1100px;margin:0 auto;padding:10px;}}
  .wrap{{background:#fff;border:1px solid #e2e2e2;border-radius:8px;padding:10px;}}
  table.datatable{{width:100%;border-collapse:collapse;font-size:14px;cursor:default;}}
  table.datatable thead th{{
    text-align:left;
    position:sticky; top:0;
    background:#fafafa; border-bottom:1px solid #ddd; padding:10px;
    cursor:pointer;
  }}
  table.datatable tbody td{{border-bottom:1px solid #f0f0f0;padding:10px;}}
  table.datatable tbody tr:nth-child(odd){{background:#fcfcfc;}}
  th.sort-asc::after{{content:" ▲";font-size:12px;}}
  th.sort-desc::after{{content:" ▼";font-size:12px;}}
</style>
</head>
<body>
  <div class="page">
    <div class="wrap">
      {table_html}
    </div>
  </div>
<script>
// Simple column sorting (numeric-aware; handles $)
document.querySelectorAll("table.datatable thead th").forEach((th, colIndex) => {{
  th.addEventListener("click", () => {{
    const table = th.closest("table");
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    const isAsc = !th.classList.contains("sort-asc");
    table.querySelectorAll("th").forEach(h => h.classList.remove("sort-asc","sort-desc"));
    th.classList.add(isAsc ? "sort-asc" : "sort-desc");

    rows.sort((a, b) => {{
      const rawA = a.cells[colIndex].innerText.trim();
      const rawB = b.cells[colIndex].innerText.trim();

      const numA = parseFloat(rawA.replace(/[^0-9.-]+/g,""));
      const numB = parseFloat(rawB.replace(/[^0-9.-]+/g,""));

      if (!isNaN(numA) && !isNaN(numB)) {{
        return isAsc ? numA - numB : numB - numA;
      }}
      return isAsc ? rawA.localeCompare(rawB) : rawB.localeCompare(rawA);
    }});

    rows.forEach(r => tbody.appendChild(r));
  }});
}});
</script>
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

# Build the table page
write_data_table_html(df, "data_table.html")

# =========================================================
# Homepage (cards supply visible titles/descriptions; iframed pages have SEO only)
# =========================================================
index_html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Protein Visualizer</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body{font-family:sans-serif;background:#fafafa;margin:0;}
  .container{max-width:900px;margin:auto;padding:20px;}
  .card{margin:20px 0;padding:10px;background:#fff;border:1px solid #ddd;border-radius:8px;}
  .card h2{margin-left:25px;} /* shift headers 25px to the right */
  .note{font-size:14px;color:#333;margin:5px 0 10px 25px;}
  .links{margin:8px 0 0 25px;font-size:14px;color:#555;}
  .links a{color:#0a58ca;text-decoration:none}
  .links a:hover{text-decoration:underline}
  iframe{width:100%;border:0;border-radius:8px;display:block;}
  footer{margin-top:24px;color:#666}
</style>
</head>
<body>
<div class="container">
  <h1>Protein Source Visualizer</h1>

  <!-- 3D -->
  <div class="card">
    <h2>Calories vs Cost vs Weight (per 10g protein)</h2>
    <p class="note">This graph shows the relationship between calories, cost, and food weight of various protein sources.</p>
    <iframe src="3d_plot.html" height="900" scrolling="no" title="3D Chart"></iframe>
    <p class="note"><i>(Scroll to zoom; Drag to orbit; Ctrl+drag to pan; Click legend items to filter; Double-click legend items to isolate.)</i></p>
    <p class="links">
      <a href="3d_plot.html" target="_blank" rel="noopener">Open this chart in a new tab</a>
      · <a href="data/foods.csv" download>Download data (CSV)</a>
    </p>
  </div>

  <!-- 2D: Calories vs Cost -->
  <div class="card">
    <h2>Calories vs Cost (per 10g protein)</h2>
    <p class="note">Comparing calories and cost for various protein sources, disregarding the weight of the amount of food required to total 10g protein.</p>
    <iframe src="2d_plot1.html" height="625" scrolling="no" title="Calories vs Cost"></iframe>
    <p class="note"><i>(Scroll to zoom; Shift+drag to pan; Click legend items to filter; Double-click legend items to isolate.)</i></p>
    <p class="links">
      <a href="2d_plot1.html" target="_blank" rel="noopener">Open this chart in a new tab</a>
      · <a href="data/foods.csv" download>Download data (CSV)</a>
    </p>
  </div>

  <!-- 2D: Calories vs Weight -->
  <div class="card">
    <h2>Calories vs Weight (per 10g protein)</h2>
    <p class="note">Comparing calories and weight for various protein sources, disregarding the cost for the amount of food required to total 10g protein.</p>
    <iframe src="2d_plot2.html" height="625" scrolling="no" title="Calories vs Weight"></iframe>
    <p class="note"><i>(Scroll to zoom; Shift+drag to pan; Click legend items to filter; Double-click legend items to isolate.)</i></p>
    <p class="links">
      <a href="2d_plot2.html" target="_blank" rel="noopener">Open this chart in a new tab</a>
      · <a href="data/foods.csv" download>Download data (CSV)</a>
    </p>
  </div>

  <!-- 2D: Cost vs Weight -->
  <div class="card">
    <h2>Cost vs Weight (per 10g protein)</h2>
    <p class="note">Comparing cost and weight for various protein sources, disregarding the calorie total for the amount of food required to total 10g protein.</p>
    <iframe src="2d_plot3.html" height="625" scrolling="no" title="Cost vs Weight"></iframe>
    <p class="note"><i>(Scroll to zoom; Shift+drag to pan; Click legend items to filter; Double-click legend items to isolate.)</i></p>
    <p class="links">
      <a href="2d_plot3.html" target="_blank" rel="noopener">Open this chart in a new tab</a>
      · <a href="data/foods.csv" download>Download data (CSV)</a>
    </p>
  </div>

  <!-- Data table -->
  <div class="card">
    <h2>Food Sources</h2>
    <p class="note">Current database of food source information. Values represent quantities per 10g protein.</p>
    <iframe src="data_table.html" height="600" scrolling="auto" title="Food Sources Table"></iframe>
    <p class="note"><i><br>(Click column headers to sort.)</i></p>
    <p class="links">
      <a href="data_table.html" target="_blank" rel="noopener">Open this table in a new tab</a>
      · <a href="data/foods.csv" download>Download data (CSV)</a>
    </p>
  </div>

  <footer><p>&copy; <span id="year"></span> Protein Visualizer</p></footer>
</div>
<script>document.getElementById('year').textContent=new Date().getFullYear();</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

print("✅ Site built: 3D + 2D charts and a sortable Input Data table card at the bottom. Reset buttons re-enable ALL categories, and iframed pages hide duplicate titles.")
