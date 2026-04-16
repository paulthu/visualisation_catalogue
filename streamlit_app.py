import streamlit as st
import folium
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import defaultdict, Counter
from streamlit_folium import st_folium

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Stelliant — Carte Bas Carbone",
    page_icon="🗺️",
    layout="wide",
)

# ── Stelliant palette ──────────────────────────────────────────
NAVY   = "#002D62"
ORANGE = "#F47920"
SKY    = "#00AEEF"
GREEN  = "#4CAF7D"
MUTED  = "#5A6E84"
BG     = "#F4F7FB"
BORDER = "#D2DCE8"

NAVY_MID  = "#1A3A6B"
NAVY_LT   = "#D0E2F3"
ORANGE_LT = "#FDEBD8"
SKY_LT    = "#D0F0FC"
GRAPE     = "#7C5CBF"
TEXT      = "#0D1B2A"
GRID_COL  = "#E8EEF5"

PALETTE = [NAVY, ORANGE, SKY, GREEN, GRAPE, "#F4A922"]

TYPE_COLORS = {
    "matériaux bas carbone":                 NAVY,
    "matériel bas carbone":                  SKY,
    "gestion et revalorisation des déchets": GREEN,
    "solutions réparatoires":                ORANGE,
    "solution de financement":               GRAPE,
}

ETAT_COLORS = {
    "ok":                 GREEN,
    "en cours":           SKY,
    "en attente de test": "#F4A922",
}

BASE_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor=BG,
    font=dict(family="Barlow, Arial, sans-serif", color=TEXT, size=11),
    margin=dict(l=10, r=10, t=44, b=10),
)

AXIS_STYLE = dict(
    gridcolor=GRID_COL,
    zeroline=False,
    linecolor=BORDER,
    tickfont=dict(color=MUTED, family="Barlow, Arial, sans-serif", size=10),
)

# ── Logo (base64 embedded so it works without static file serving) ──────
LOGO_B64 = "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"

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] { font-family: 'Barlow', Arial, sans-serif; }
    .stSelectbox label { font-size: 11px !important; font-weight: 700 !important;
                         color: #5A6E84 !important; letter-spacing: 1px;
                         text-transform: uppercase; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────
st.markdown(f"""
<div style="
    background:white;border-radius:10px;padding:12px 20px;
    display:flex;align-items:center;gap:20px;
    border:1px solid #D2DCE8;margin-bottom:16px;
    overflow:visible;box-sizing:border-box;width:100%;
">
  <img src="data:image/png;base64,{LOGO_B64}"
       style="max-height:56px;width:auto;object-fit:contain;display:block;flex-shrink:0" />
  <span style="font-size:11px;color:#5A6E84;letter-spacing:1px;text-transform:uppercase">
    Catalogue Bas Carbone — Visualisation
  </span>
</div>
""", unsafe_allow_html=True)

# ── GeoJSON (cached independently of the catalog) ──────────────
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson"
    return requests.get(url).json()

geo_data = load_geojson()

# ── File upload ────────────────────────────────────────────────
st.title("Visualisation Catalogue Stelliant")
uploaded_file = st.file_uploader(
    "Pour accéder aux visualisations, chargez le catalogue en format Excel (.xlsx).",
    type=["xlsx", "xlsm"],
)

if uploaded_file is None:
    st.stop()

# ── Catalog loading & preparation ─────────────────────────────
@st.cache_data
def prepare_catalog(uploaded_file):
    catalog = pd.read_excel(uploaded_file, sheet_name="Catalogue Bas Carbone")
    # Strip whitespace from column names and normalize accented characters
    catalog.columns = catalog.columns.str.strip()

    # Normalize "État" / "Etat" → always "Etat"
    catalog.columns = [
        "Etat" if col.lower() in ("état", "etat") else col
        for col in catalog.columns
    ]

    catalog = catalog.drop(
        columns=["Sélection des filtres", "Rang Occupé?"],
        errors="ignore",
    )

    str_cols = catalog.select_dtypes(include="object").columns
    catalog[str_cols] = catalog[str_cols].apply(lambda col: col.str.strip())

    NATIONAL_REGIONS = (
        "Auvergne-Rhône-Alpes, Bourgogne-Franche-Comté, Bretagne, "
        "Centre-Val de Loire, Corse, Grand Est, Hauts-de-France, "
        "Île-de-France, Normandie, Nouvelle-Aquitaine, Occitanie, "
        "Pays de la Loire, Provence-Alpes-Côte d'Azur"
    )

    def get_region(x):
        if pd.isna(x) or str(x).strip() == "":
            return "none"
        x = str(x).strip()
        if x == "National":
            return NATIONAL_REGIONS
        return x

    catalog["Region"] = catalog["Secteur d'intervention /livraison"].apply(get_region)
    return catalog

catalog = prepare_catalog(uploaded_file)

# ── Sidebar filter ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="background:white;border-radius:8px;padding:8px 12px;margin-bottom:12px">
      <img src="data:image/png;base64,{LOGO_B64}"
           style="height:36px;width:auto;object-fit:contain" />
    </div>
    """, unsafe_allow_html=True)

    categories = ["Toutes"] + sorted(catalog["Catégorie"].dropna().unique().tolist())
    categorie_filter = st.selectbox("Filtrer par catégorie", categories)

    st.markdown("---")
    nb_total = (
        len(catalog)
        if categorie_filter == "Toutes"
        else len(catalog[catalog["Catégorie"] == categorie_filter])
    )
    st.metric("Solutions affichées", nb_total)

# ── Map builder ────────────────────────────────────────────────
def build_map(categorie_filter):
    logo_b64_var = LOGO_B64
    filtered = (
        catalog.copy()
        if categorie_filter == "Toutes"
        else catalog[catalog["Catégorie"] == categorie_filter]
    )

    rows = []
    for _, row in filtered.iterrows():
        if row["Region"] == "none":
            continue
        for region in [r.strip() for r in str(row["Region"]).split(",")]:
            rows.append({
                "region":     region,
                "entreprise": row["Entreprise"],
                "categorie":  row["Catégorie"],
                "etat":       row["Etat"],
                "fiche":      row.get("Fiche d'Informations", ""),
            })

    expanded = (
        pd.DataFrame(rows)
        if rows
        else pd.DataFrame(columns=["region", "entreprise", "categorie", "etat", "fiche"])
    )
    count_per_region = (
        expanded.groupby("region").size().reset_index(name="nb_solutions")
        if not expanded.empty
        else pd.DataFrame(columns=["region", "nb_solutions"])
    )

    popup_dict = defaultdict(list)
    for _, row in expanded.iterrows():
        etat_color = {
            "ok":                 GREEN,
            "en cours":           SKY,
            "en attente de test": "#F4A922",
        }.get(str(row["etat"]).lower(), MUTED)
        fiche = row.get("fiche", "")
        name_html = (
            f'<a href="{fiche}" target="_blank" '
            f'style="color:{NAVY};font-weight:600;font-size:12px;text-decoration:none;'
            f'border-bottom:1px solid {SKY}">{row["entreprise"]}</a>'
            if fiche and str(fiche).startswith("http")
            else f'<span style="color:{NAVY};font-weight:600;font-size:12px">{row["entreprise"]}</span>'
        )
        popup_dict[row["region"]].append(
            f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{etat_color};'
            f'flex-shrink:0;display:inline-block"></span>'
            f'{name_html}'
            f'<span style="color:{MUTED};font-size:11px">— {row["categorie"]}</span>'
            f'</div>'
        )

    m = folium.Map(
        location=[46.5, 2.5],
        zoom_start=6,
        tiles="cartodb positron",
        max_bounds=True,
        min_zoom=5,
    )
    m.fit_bounds([[41.0, -5.5], [51.5, 10.0]])

    if not count_per_region.empty:
        choropleth = folium.Choropleth(
            geo_data=geo_data,
            data=count_per_region,
            columns=["region", "nb_solutions"],
            key_on="feature.properties.nom",
            fill_color="Blues",
            fill_opacity=0.75,
            line_opacity=0.4,
            line_color="white",
            legend_name="Nombre de solutions bas carbone",
            nan_fill_color="#EEF3F8",
            nan_fill_opacity=0.5,
        )
        choropleth.add_to(m)
        for child in list(choropleth._children):
            if "color_map" in child:
                del choropleth._children[child]

    for feature in geo_data["features"]:
        nom = feature["properties"]["nom"]
        row = count_per_region[count_per_region["region"] == nom]
        nb  = int(row["nb_solutions"].values[0]) if not row.empty else 0
        details = (
            "".join(popup_dict[nom])
            if nom in popup_dict
            else f'<span style="color:{MUTED};font-size:12px">Aucune solution référencée</span>'
        )
        badge_color = NAVY if nb >= 40 else SKY if nb >= 10 else MUTED

        popup_html = f"""
        <div style="font-family:'Barlow',Arial,sans-serif;min-width:220px;max-width:300px">
          <div style="background:{NAVY};color:white;padding:10px 14px;
                      border-radius:8px 8px 0 0;margin:-1px -1px 0">
            <div style="font-size:14px;font-weight:700">{nom}</div>
            <div style="font-size:11px;opacity:.75;margin-top:2px">Région</div>
          </div>
          <div style="padding:10px 14px;border:1px solid {BORDER};border-top:none;
                      border-radius:0 0 8px 8px;background:white">
            <div style="margin-bottom:10px">
              <span style="background:{badge_color};color:white;padding:3px 10px;
                           border-radius:12px;font-size:12px;font-weight:700">
                {nb} solution{"s" if nb != 1 else ""}
              </span>
            </div>
            <div style="border-top:1px solid {BORDER};padding-top:8px">{details}</div>
          </div>
        </div>
        """

        tooltip_html = f"""
        <div style="font-family:'Barlow',Arial,sans-serif;background:{NAVY};color:white;
                    padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600">
          {nom} &nbsp;·&nbsp;
          <span style="color:{SKY}">{nb} solution{"s" if nb != 1 else ""}</span>
        </div>
        """

        folium.GeoJson(
            feature,
            style_function=lambda x: {"fillOpacity": 0, "color": "transparent", "weight": 0},
            highlight_function=lambda x: {
                "fillColor": ORANGE, "fillOpacity": 0.25, "color": ORANGE, "weight": 2
            },
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
            popup=folium.Popup(popup_html, max_width=320),
        ).add_to(m)

    legend_html = f"""
    <div style="position:fixed;bottom:28px;left:28px;background:white;
                border:1px solid {BORDER};border-radius:10px;padding:14px 18px;
                font-family:'Barlow',Arial,sans-serif;
                box-shadow:0 4px 16px rgba(0,45,98,.12);z-index:9999;min-width:180px">
      <div style="margin-bottom:10px;background:white;border-radius:6px;padding:5px 8px;display:inline-block">
        <img src="data:image/png;base64,{logo_b64_var}"
             style="height:28px;width:auto;object-fit:contain;display:block" />
      </div>
      <div style="font-size:10px;font-weight:700;color:{MUTED};letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:8px">Solutions par région</div>
      {''.join([
        f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
        f'<div style="width:14px;height:14px;border-radius:3px;background:{c}"></div>'
        f'<span style="font-size:11px;color:#0D1B2A">{label}</span></div>'
        for c, label in [
            ("#EBF4FC", "0 solution"),
            ("#7AB8E0", "1 – 10"),
            ("#1A5A9A", "11 – 40"),
            (NAVY,      "41 +"),
        ]
      ])}
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid {BORDER};
                  font-size:10px;color:{MUTED}">
        Filtre : <b style="color:{NAVY}">{categorie_filter}</b>
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


# ── Render map ─────────────────────────────────────────────────
st.markdown("### 🗺️ Carte — Couverture géographique")
st_folium(build_map(categorie_filter), use_container_width=True, height=640, returned_objects=[])


# ── TABLEAU DE BORD ────────────────────────────────────────────
def styled_bar(x, y, colors, orientation="v"):
    return go.Bar(
        x=x, y=y,
        orientation=orientation,
        marker=dict(color=colors, opacity=0.92, line=dict(color="white", width=1.5)),
        hovertemplate=(
            "<b>%{y}</b>: %{x}<extra></extra>" if orientation == "h"
            else "<b>%{x}</b>: %{y}<extra></extra>"
        ),
    )


st.markdown("---")
st.markdown("### 📊 Tableau de bord")

# ── Check required columns exist ──────────────────────────────
REQUIRED_COLS = {
    "Catégorie",
    "Etat",
    "Type de solution bas carbone",
    "Traditionnel ou bas carbone?",
    "Region",
}
missing = REQUIRED_COLS - set(catalog.columns)
if missing:
    st.error(
        f"❌ Colonnes introuvables dans le fichier : **{', '.join(sorted(missing))}**\n\n"
        f"Colonnes disponibles : `{', '.join(catalog.columns.tolist())}`"
    )
    st.stop()

# ── Apply the same category filter used for the map ───────────
df = (
    catalog.copy()
    if categorie_filter == "Toutes"
    else catalog[catalog["Catégorie"] == categorie_filter]
)

# ── KPI cards ─────────────────────────────────────────────────
total  = len(df)
n_cats = df["Catégorie"].nunique()
n_reg  = (
    df["Region"]
    .apply(lambda r: [x.strip() for x in r.split(",") if x.strip() != "none"] if r != "none" else [])
    .explode()
    .nunique()
)
pct_bc = round(100 * (df["Traditionnel ou bas carbone?"] == "Bas Carbone").mean()) if total > 0 else 0

k1, k2, k3, k4 = st.columns(4)
for col, val, label, color in [
    (k1, total,        "Solutions",   NAVY),
    (k2, n_cats,       "Catégories",  ORANGE),
    (k3, n_reg,        "Régions",     SKY),
    (k4, f"{pct_bc}%", "Bas Carbone", GREEN),
]:
    col.markdown(f"""
    <div style="background:white;border:1px solid {BORDER};border-top:4px solid {color};
                border-radius:10px;padding:14px 20px;text-align:center;
                box-shadow:0 2px 8px rgba(0,45,98,.07)">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:2.2em;
                  font-weight:700;color:{color};line-height:1">{val}</div>
      <div style="font-size:10px;color:{MUTED};margin-top:5px;
                  letter-spacing:1px;text-transform:uppercase">{label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:20px'></div>", unsafe_allow_html=True)

# ── Subplots ───────────────────────────────────────────────────
fig = make_subplots(
    rows=2, cols=3,
    subplot_titles=[
        "CATÉGORIES", "ÉTAT DES SOLUTIONS", "TYPES DE SOLUTION",
        "TOP RÉGIONS", "SECTEURS D'INTERVENTION", "TRAD. VS BAS CARBONE",
    ],
    specs=[
        [{"type": "bar"}, {"type": "bar"}, {"type": "pie"}],
        [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
    ],
    horizontal_spacing=0.08,
    vertical_spacing=0.18,
)

# Row 1, col 1 — Catégories (top 8)
cat = df["Catégorie"].value_counts().head(8)
fig.add_trace(styled_bar(cat.values.tolist(), cat.index.tolist(), NAVY, "h"), row=1, col=1)

# Row 1, col 2 — État
etat = df["Etat"].value_counts()
fig.add_trace(
    styled_bar(
        etat.index.tolist(), etat.values.tolist(),
        [ETAT_COLORS.get(str(e).lower(), MUTED) for e in etat.index],
    ),
    row=1, col=2,
)

# Row 1, col 3 — Type (donut)
typ = df["Type de solution bas carbone"].value_counts()
fig.add_trace(
    go.Pie(
        labels=typ.index,
        values=typ.values,
        marker=dict(
            colors=[TYPE_COLORS.get(str(t).lower(), NAVY) for t in typ.index],
            line=dict(color="white", width=3),
        ),
        textfont=dict(color=TEXT, family="Barlow, Arial, sans-serif", size=10),
        hole=0.5,
        hovertemplate="<b>%{label}</b><br>%{value} solution(s) (%{percent})<extra></extra>",
    ),
    row=1, col=3,
)

# Row 2, col 1 — Top régions
region_list = []
for r in df["Region"].dropna():
    if r != "none":
        region_list.extend([x.strip() for x in r.split(",")])
if region_list:
    rc = Counter(region_list).most_common(10)
    regs, counts = zip(*rc)
    fig.add_trace(styled_bar(list(counts), list(regs), SKY, "h"), row=2, col=1)

# Row 2, col 2 — Secteurs
sec = df["Secteur d'intervention /livraison"].value_counts()
fig.add_trace(
    styled_bar(
        sec.values.tolist(), sec.index.tolist(),
        [PALETTE[i % len(PALETTE)] for i in range(len(sec))], "h",
    ),
    row=2, col=2,
)

# Row 2, col 3 — Trad vs BC
trad = df["Traditionnel ou bas carbone?"].value_counts()
fig.add_trace(
    styled_bar(
        trad.index.tolist(), trad.values.tolist(),
        [ORANGE if "Bas" in str(v) else MUTED for v in trad.index],
    ),
    row=2, col=3,
)

# ── Layout polish ──────────────────────────────────────────────
fig.update_layout(
    **BASE_LAYOUT,
    height=680,
    showlegend=False,
    bargap=0.35,
)
fig.update_annotations(
    font=dict(color=NAVY_MID, size=10, family="Barlow, Arial, sans-serif"),
    bgcolor=NAVY_LT,
    borderpad=4,
)
fig.update_xaxes(**AXIS_STYLE)
fig.update_yaxes(**AXIS_STYLE)

st.plotly_chart(fig, use_container_width=True)
