"""Índice de oportunidad v0 por distrito (solo datos públicos).

Uso:
    python fase1/indice_v0.py            # alpha por defecto (0.6)
    python fase1/indice_v0.py --alpha 0.3

Combina dos lentes, ambos en percentiles dentro del ámbito piloto (0 = peor, 1 = mejor):

  VOLUMEN    ¿dónde hay más clientes potenciales en número absoluto?
  INTENSIDAD ¿dónde la brecha por habitante es mayor? (favorece distritos chicos/rurales)

  score = 100 * (alpha * VOLUMEN + (1 - alpha) * INTENSIDAD) * factor_oferta

alpha es una decisión de negocio (eficiencia comercial vs. inclusión), no técnica:
se discute con el owner. factor_oferta penaliza distritos ya saturados de puntos de
atención financiera cuando existan datos SBS en data/interim/oferta_por_distrito.parquet
(columnas: ubigeo, puntos_atencion). Sin ellos, factor_oferta = 1 y se avisa.

Salidas en salidas/: ranking_v0.csv, reporte_indice_v0.md, mapa_indice_v0.html
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "salidas"
OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ configuración
# Cada componente: (columna, peso, etiqueta legible). Los pesos de cada lente suman 1.
VOLUMEN = {
    "v_adultos": ("pob_18_64", 0.50, "adultos 18-64"),
    "v_puestos": ("puestos_mercado", 0.25, "puestos de mercado"),
    "v_empresas": ("ruc_activos_habidos", 0.25, "empresas formales activas"),
}
INTENSIDAD = {
    "i_brecha": ("brecha_formal", 0.50, "brecha de formalidad (pocas empresas por adulto)"),
    "i_puestos_pc": ("puestos_x1000", 0.50, "puestos de mercado por adulto"),
}
PENALIDAD_OFERTA_MAX = 0.30  # un distrito en el percentil 100 de oferta pierde hasta 30 %

NOMBRES_FALTANTES = {"130112": ("ALTO TRUJILLO", "TRUJILLO")}  # creado en 2020, sin polígono


def pct(s: pd.Series) -> pd.Series:
    """Percentil 0-1 (empates promediados)."""
    return s.rank(pct=True, method="average")


def cargar() -> tuple[pd.DataFrame, dict]:
    base = pd.read_parquet(INTERIM / "base_distrital.parquet")
    geo = json.loads((INTERIM / "limites_piloto.geojson").read_text(encoding="utf-8"))
    meta = pd.DataFrame([{
        "ubigeo": f["properties"]["IDDIST"],
        "distrito": f["properties"]["NOMBDIST"],
        "provincia": f["properties"]["NOMBPROV"],
        "area_km2": f["properties"]["AREA_MINAM"] / 100,  # MINAM en hectáreas
    } for f in geo["features"]])
    df = base.merge(meta, on="ubigeo", how="left")
    for ub, (dist, prov) in NOMBRES_FALTANTES.items():
        df.loc[df["ubigeo"] == ub, ["distrito", "provincia"]] = [dist, prov]
    df["ruc_activos_habidos"] = df["ruc_activos_habidos"].fillna(0)
    df["densidad_hab_km2"] = df["pob"] / df["area_km2"]
    df["puestos_x1000"] = 1000 * df["puestos_mercado"] / df["pob_18_64"]
    df["empresas_x1000"] = 1000 * df["ruc_activos_habidos"] / df["pob_18_64"]
    df["brecha_formal"] = -df["empresas_x1000"]  # menos empresas por adulto = más brecha
    return df, geo


def oferta(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    path = INTERIM / "oferta_por_distrito.parquet"
    if not path.exists():
        df["factor_oferta"] = 1.0
        return df, False
    of = pd.read_parquet(path)[["ubigeo", "puntos_atencion"]]
    df = df.merge(of, on="ubigeo", how="left")
    df["puntos_x1000"] = 1000 * df["puntos_atencion"].fillna(0) / df["pob_18_64"]
    df["factor_oferta"] = 1 - PENALIDAD_OFERTA_MAX * pct(df["puntos_x1000"])
    return df, True


def puntuar(df: pd.DataFrame, alpha: float, wv: dict | None = None, wi: dict | None = None) -> pd.Series:
    wv = wv or {k: w for k, (_, w, _) in VOLUMEN.items()}
    wi = wi or {k: w for k, (_, w, _) in INTENSIDAD.items()}
    vol = sum(wv[k] * df[k] for k in VOLUMEN)
    inte = sum(wi[k] * df[k] for k in INTENSIDAD)
    return 100 * (alpha * vol + (1 - alpha) * inte) * df["factor_oferta"]


def explicar(row: pd.Series, alpha: float) -> str:
    """Fortalezas (percentil más alto) y debilidad (más bajo) del distrito, con su percentil."""
    comps = {**VOLUMEN, **INTENSIDAD}
    orden = sorted(comps, key=lambda k: -row[k])
    fuertes = [f"{comps[k][2]} (p{row[k] * 100:.0f})" for k in orden[:2]]
    k = orden[-1]
    return f"+ {'; '.join(fuertes)} | − {comps[k][2]} (p{row[k] * 100:.0f})"


def sensibilidad(df: pd.DataFrame, alpha: float, n: int = 1000, top: int = 10, seed: int = 7) -> pd.DataFrame:
    """Perturba pesos (Dirichlet centrado en los pesos base) y alpha (±0.15).
    Devuelve, por distrito, % de simulaciones en el top-N y rango intercuartil del puesto."""
    rng = np.random.default_rng(seed)
    kv, ki = list(VOLUMEN), list(INTENSIDAD)
    base_v = np.array([VOLUMEN[k][1] for k in kv])
    base_i = np.array([INTENSIDAD[k][1] for k in ki])
    ranks = np.empty((n, len(df)))
    for s in range(n):
        wv = dict(zip(kv, rng.dirichlet(base_v * 20)))
        wi = dict(zip(ki, rng.dirichlet(base_i * 20)))
        a = float(np.clip(alpha + rng.uniform(-0.15, 0.15), 0, 1))
        ranks[s] = puntuar(df, a, wv, wi).rank(ascending=False, method="min").to_numpy()
    return pd.DataFrame({
        "ubigeo": df["ubigeo"].to_numpy(),
        "pct_en_top": (ranks <= top).mean(axis=0),
        "puesto_p25": np.percentile(ranks, 25, axis=0),
        "puesto_p75": np.percentile(ranks, 75, axis=0),
    })


def auditoria(df: pd.DataFrame, top: int = 15) -> list[str]:
    """¿El índice margina a los distritos rurales/de baja densidad?"""
    df = df.copy()
    df["tercil_densidad"] = pd.qcut(df["densidad_hab_km2"], 3, labels=["baja (rural)", "media", "alta (urbana)"])
    t = df.groupby("tercil_densidad", observed=True).agg(
        distritos=("ubigeo", "size"),
        score_volumen=("score_volumen", "mean"),
        score_intensidad=("score_intensidad", "mean"),
        score_final=("score", "mean"),
        en_top=("puesto", lambda s: (s <= top).sum()),
    ).round(1)
    rho = df[["score", "densidad_hab_km2"]].corr(method="spearman").iloc[0, 1]
    lines = ["| tercil de densidad | distritos | volumen | intensidad | final | en top-%d |" % top,
             "|---|---:|---:|---:|---:|---:|"]
    lines += [f"| {i} | {r.distritos} | {r.score_volumen} | {r.score_intensidad} | {r.score_final} | {r.en_top} |"
              for i, r in t.iterrows()]
    rural_top = int(t.loc["baja (rural)", "en_top"])
    lines += ["", f"- Correlación de Spearman entre puntaje final y densidad: **{rho:+.2f}**.",
              f"- Distritos rurales (tercil bajo) en el top-{top}: **{rural_top}** de {top}."]
    if rural_top == 0:
        lines.append("- ⚠ Con este alpha el top queda 100 % urbano: bajar alpha o agregar un cupo rural.")
    return lines


def leaflet() -> str:
    """Leaflet incrustado (vendor/) para que el mapa funcione sin internet; si falta, CDN."""
    v = ROOT / "vendor" / "leaflet"
    if (v / "leaflet.js").exists():
        css = (v / "leaflet.css").read_text(encoding="utf-8")
        js = (v / "leaflet.js").read_text(encoding="utf-8")
        return f"<style>{css}</style>\n<script>{js}</script>"
    return ('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">\n'
            '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>')


def mapa(df: pd.DataFrame, geo: dict, alpha: float, con_oferta: bool) -> None:
    cols = ["ubigeo", "distrito", "provincia", "puesto", "score", "score_volumen", "score_intensidad",
            "pob_18_64", "ruc_activos_habidos", "empresas_x1000", "puestos_mercado", "razones", "pct_en_top"]
    props = df[cols].round(2).set_index("ubigeo").to_dict(orient="index")
    feats = []
    for f in geo["features"]:
        p = props.get(f["properties"]["IDDIST"])
        if p:
            feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {"ubigeo": f["properties"]["IDDIST"], **p}})
    data = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False)
    html = MAPA_HTML.replace("__LEAFLET__", leaflet()).replace("__DATA__", data).replace("__ALPHA__", f"{alpha:.2f}").replace(
        "__OFERTA__", "incluida" if con_oferta else "pendiente (sin datos SBS)")
    (OUT / "mapa_indice_v0.html").write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.6, help="peso del lente VOLUMEN (0-1)")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    df, geo = cargar()
    df, con_oferta = oferta(df)
    for k, (col, _, _) in {**VOLUMEN, **INTENSIDAD}.items():
        df[k] = pct(df[col])
    df["score_volumen"] = puntuar(df, 1.0) / df["factor_oferta"]
    df["score_intensidad"] = puntuar(df, 0.0) / df["factor_oferta"]
    df["score"] = puntuar(df, args.alpha)
    df["puesto"] = df["score"].rank(ascending=False, method="min").astype(int)
    df["razones"] = df.apply(explicar, axis=1, alpha=args.alpha)
    df = df.merge(sensibilidad(df, args.alpha, top=args.top), on="ubigeo")
    df = df.sort_values("puesto")

    salida = ["puesto", "ubigeo", "distrito", "provincia", "score", "score_volumen", "score_intensidad",
              "factor_oferta", "pct_en_top", "puesto_p25", "puesto_p75", "pob_18_64", "mujeres_18_64",
              "ruc_activos_habidos", "empresas_x1000", "mercados", "puestos_mercado", "densidad_hab_km2", "razones"]
    df[salida].round(3).to_csv(OUT / "ranking_v0.csv", index=False, encoding="utf-8-sig")  # sig: abre bien en Excel
    reporte(df, args.alpha, args.top, con_oferta)
    mapa(df, geo, args.alpha, con_oferta)

    print(f"alpha={args.alpha}  oferta SBS: {'sí' if con_oferta else 'NO (pendiente)'}\n")
    print(df[["puesto", "distrito", "provincia", "score", "pct_en_top"]].head(args.top).to_string(index=False))
    print("\n-> salidas/ranking_v0.csv, salidas/reporte_indice_v0.md, salidas/mapa_indice_v0.html")
    return 0


def reporte(df: pd.DataFrame, alpha: float, top: int, con_oferta: bool) -> None:
    L = ["# Índice de oportunidad v0 — La Libertad", "",
         f"alpha (peso de VOLUMEN) = **{alpha}** · oferta financiera SBS: **{'incluida' if con_oferta else 'pendiente'}** · "
         f"{len(df)} distritos", "",
         "## Cómo se calcula", "",
         "Cada variable se convierte a percentil dentro de La Libertad (0 a 1) y se pondera:", "",
         "| lente | variable | peso dentro del lente |", "|---|---|---:|"]
    L += [f"| volumen | {txt} (`{col}`) | {w:.0%} |" for col, w, txt in VOLUMEN.values()]
    L += [f"| intensidad | {txt} (`{col}`) | {w:.0%} |" for col, w, txt in INTENSIDAD.values()]
    L += ["", f"`score = 100 × (α·volumen + (1−α)·intensidad) × factor_oferta`", "",
          f"## Top {top}", "",
          f"`estabilidad` = % de 1 000 simulaciones (pesos y α perturbados) en que el distrito sigue en el top-{top}.", "",
          "| # | distrito | provincia | score | estabilidad | por qué |", "|---:|---|---|---:|---:|---|"]
    L += [f"| {r.puesto} | {r.distrito} | {r.provincia} | {r.score:.1f} | {r.pct_en_top:.0%} | {r.razones} |"
          for r in df.head(top).itertuples()]
    L += ["", "## Auditoría de sesgo urbano/rural", ""] + auditoria(df, top)
    L += ["", "## Limitaciones (decirlas en el pitch)", "",
          "- El padrón RUC reducido solo trae ubigeo para personas jurídicas (RUC 20); las personas naturales "
          "con negocio (RUC 10) casi nunca lo tienen. `ruc_activos_habidos` mide **empresas formales**, no microempresarios.",
          "- CENAMA es de 2016; los puestos de mercado pueden haber cambiado.",
          "- Sin datos SBS el índice no sabe dónde ya hay agencias/agentes: puede priorizar zonas ya atendidas.",
          "- Es un índice de priorización territorial, no evalúa a personas ni su riesgo crediticio.",
          "- Alto Trujillo (130112) no tiene polígono en el mapa base: aparece en el ranking pero no en el mapa."]
    (OUT / "reporte_indice_v0.md").write_text("\n".join(L) + "\n", encoding="utf-8")


MAPA_HTML = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Índice de oportunidad v0</title>
__LEAFLET__
<style>
  :root{--bg:#fff;--fg:#1d2330;--muted:#5b6475;--card:#f6f7f9;--line:#dde1e7}
  @media (prefers-color-scheme:dark){:root{--bg:#14171d;--fg:#e8eaee;--muted:#9aa3b2;--card:#1d2129;--line:#2c323d}}
  *{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
  .wrap{display:grid;grid-template-columns:1fr 380px;height:100vh}
  #map{height:100%}
  aside{overflow:auto;padding:16px;border-left:1px solid var(--line)}
  h1{font-size:17px;margin:0 0 4px}.sub{color:var(--muted);font-size:12px;margin-bottom:12px}
  .tabs{display:flex;gap:4px;margin-bottom:12px}.tabs button{flex:1;padding:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px;cursor:pointer;font:inherit;font-size:12px}
  .tabs button.on{background:#2f6fde;color:#fff;border-color:#2f6fde}
  ol{padding-left:22px;margin:0}li{padding:6px 0;border-bottom:1px solid var(--line);cursor:pointer}
  li b{font-weight:600}.why{color:var(--muted);font-size:12px}
  .legend{background:var(--bg);color:var(--fg);padding:8px 10px;border-radius:6px;font-size:12px;box-shadow:0 1px 4px #0003}
  .legend i{display:inline-block;width:14px;height:10px;margin-right:4px}
  @media (max-width:800px){.wrap{grid-template-columns:1fr;grid-template-rows:55vh auto;height:auto}aside{border-left:0}}
</style></head><body>
<div class="wrap"><div id="map"></div><aside>
<h1>Índice de oportunidad v0 · La Libertad</h1>
<div class="sub">α = __ALPHA__ · oferta SBS: __OFERTA__ · datos públicos (SUNAT, RENIEC, CENAMA)</div>
<div class="tabs"><button data-k="score" class="on">Final</button><button data-k="score_volumen">Volumen</button><button data-k="score_intensidad">Intensidad</button></div>
<ol id="list"></ol></aside></div>
<script>
const data = __DATA__;
const colors = ["#f1eef6","#d0d1e6","#a6bddb","#74a9cf","#2b8cbe","#045a8d"];
let key = "score";
const map = L.map("map").setView([-7.9,-78.6], 8);
L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",{attribution:"© OpenStreetMap © CARTO",maxZoom:18}).addTo(map);
function breaks(){const v=data.features.map(f=>f.properties[key]).sort((a,b)=>a-b);return [1,2,3,4,5].map(i=>v[Math.floor(i*v.length/6)]);}
let br = breaks();
const col = x => colors[br.filter(b=>x>=b).length];
const fmt = n => Math.round(n).toLocaleString("es-PE");
const layer = L.geoJSON(data,{style:f=>({fillColor:col(f.properties[key]),weight:.6,color:"#555",fillOpacity:.8}),
  onEachFeature:(f,l)=>{const p=f.properties;l.bindPopup(`<b>${p.distrito}</b> (${p.provincia})<br>Puesto #${p.puesto} · score ${p.score.toFixed(1)}<br>Volumen ${p.score_volumen.toFixed(1)} · Intensidad ${p.score_intensidad.toFixed(1)}<br>Adultos 18-64: ${fmt(p.pob_18_64)}<br>Empresas activas: ${fmt(p.ruc_activos_habidos)} (${p.empresas_x1000.toFixed(1)}/1000)<br>Puestos de mercado: ${fmt(p.puestos_mercado)}<br>Estabilidad en top: ${Math.round(p.pct_en_top*100)}%<br><i>${p.razones}</i>`);}}).addTo(map);
map.fitBounds(layer.getBounds());
const legend = L.control({position:"bottomleft"});
legend.onAdd = () => { const d=L.DomUtil.create("div","legend"); d.id="lg"; return d; };
legend.addTo(map);
function render(){
  br = breaks(); layer.setStyle(f=>({fillColor:col(f.properties[key])}));
  document.getElementById("lg").innerHTML = "<b>"+({score:"Final",score_volumen:"Volumen",score_intensidad:"Intensidad"})[key]+"</b><br>"+
    colors.map((c,i)=>`<i style="background:${c}"></i>${i?"≥ "+br[i-1].toFixed(0):"menor"}`).join("<br>");
  const top = [...data.features].sort((a,b)=>b.properties[key]-a.properties[key]).slice(0,20);
  document.getElementById("list").innerHTML = top.map(f=>`<li data-u="${f.properties.ubigeo}"><b>${f.properties.distrito}</b> · ${f.properties[key].toFixed(1)}<div class="why">${f.properties.provincia} · ${f.properties.razones}</div></li>`).join("");
}
document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tabs button").forEach(x=>x.classList.remove("on"));b.classList.add("on");key=b.dataset.k;render();});
document.getElementById("list").onclick = e => { const li=e.target.closest("li"); if(!li) return;
  layer.eachLayer(l=>{ if(l.feature.properties.ubigeo===li.dataset.u){ map.fitBounds(l.getBounds(),{maxZoom:11}); l.openPopup(); }}); };
render();
</script></body></html>
"""

if __name__ == "__main__":
    sys.exit(main())
