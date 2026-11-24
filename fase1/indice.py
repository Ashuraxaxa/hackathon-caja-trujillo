"""Índice de oportunidad por distrito (solo datos públicos).

Uso:
    python fase1/indice.py            # alpha por defecto (0.6)
    python fase1/indice.py --alpha 0.3 --cupo-agro 0.5

Cada distrito se evalúa por SEGMENTO de cliente y se queda con su segmento más fuerte,
para no castigar a un distrito urbano por no tener agro ni a uno rural por no tener mercados:

  urbano  comercio y microempresa (adultos, mercados, empresas, brecha de formalidad)
  agro    pequeño productor sin acceso a crédito (CENAGRO)

Dentro de cada segmento hay dos lentes, en percentiles dentro del ámbito piloto (0-1):

  VOLUMEN    ¿cuántos clientes potenciales hay, en número absoluto?
  INTENSIDAD ¿qué tan grande es la brecha por habitante?

  score_seg = alpha * VOLUMEN_seg + (1 - alpha) * INTENSIDAD_seg
  score     = 100 * max(score_urbano, score_agro) * factor_oferta   (segmento dominante)

Comparar un distrito urbano con uno agro NO lo deciden los datos: es una decisión de
cartera (cuántos asesores a cada segmento). Por eso se rankea dentro de cada segmento y
la lista combinada intercala ambos rankings según --cupo-agro (fracción de la lista para agro).

alpha es una decisión de negocio (eficiencia comercial vs. inclusión), no técnica:
se discute con el owner. factor_oferta penaliza distritos ya saturados de puntos de
atención de la competencia, leídos de data/manual/oficinas_competencia.csv (fase0/competencia.py).
Sin competencia en el distrito, factor_oferta = 1.

Salidas en salidas/: ranking_{VERSION}.csv, reporte_indice_{VERSION}.md, mapa_indice_{VERSION}.html
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
VERSION = "v1"  # v0: urbano (SUNAT, RENIEC, CENAMA) · v1: + productores agro excluidos (CENAGRO)
# Componentes: clave -> (columna, etiqueta legible). Se convierten a percentil.
COMPONENTES = {
    "adultos": ("pob_18_64", "adultos 18-64"),
    "puestos": ("puestos_mercado", "puestos de mercado"),
    "empresas": ("ruc_activos_habidos", "empresas formales activas"),
    "brecha": ("brecha_formal", "brecha de formalidad (pocas empresas por adulto)"),
    "puestos_pc": ("puestos_x1000", "puestos de mercado por adulto"),
    "agro_excl": ("prod_excluidos", "productores agro sin acceso a crédito"),
    "agro_peq": ("productores_pequenos", "pequeños productores (<5 ha)"),
    "agro_excl_pc": ("agro_excl_x1000", "productores agro excluidos por adulto"),
    "agro_tasa": ("tasa_exclusion_agro_robusta", "% de productores excluidos del crédito"),
}
# Pesos por segmento y lente (cada lente suma 1).
SEGMENTOS = {
    "urbano": {"volumen": {"adultos": 0.55, "puestos": 0.25, "empresas": 0.20},
               "intensidad": {"brecha": 0.50, "puestos_pc": 0.50}},
    "agro": {"volumen": {"agro_excl": 0.70, "agro_peq": 0.30},
             "intensidad": {"agro_excl_pc": 0.60, "agro_tasa": 0.40}},
}
MIN_PRODUCTORES_TASA = 100  # con menos productores la tasa de exclusión es ruido
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
    ag = ROOT / "data" / "manual" / "agencias_caja_trujillo.csv"
    if ag.exists():
        cnt = pd.read_csv(ag, dtype={"ubigeo": str}).groupby("ubigeo").size()
        df["agencias_ct"] = df["ubigeo"].map(cnt).fillna(0).astype(int)
    else:
        df["agencias_ct"] = pd.NA
    df["densidad_hab_km2"] = df["pob"] / df["area_km2"]
    df["puestos_x1000"] = 1000 * df["puestos_mercado"] / df["pob_18_64"]
    df["empresas_x1000"] = 1000 * df["ruc_activos_habidos"] / df["pob_18_64"]
    df["agro_excl_x1000"] = 1000 * df["prod_excluidos"] / df["pob_18_64"]
    df["brecha_formal"] = -df["empresas_x1000"]  # menos empresas por adulto = más brecha
    df["tasa_exclusion_agro_robusta"] = df["tasa_exclusion_agro"].where(
        df["productores"] >= MIN_PRODUCTORES_TASA, 0).fillna(0)
    return df, geo


COMPETENCIA = ROOT / "data" / "manual" / "oficinas_competencia.csv"


def cargar_oferta() -> pd.DataFrame | None:
    """Oficinas de la competencia por distrito (fase0/competencia.py + filas manuales).
    Caja Trujillo no cuenta: su presencia se muestra aparte (agencias_ct)."""
    path = INTERIM / "oferta_por_distrito.parquet"
    if path.exists():
        return pd.read_parquet(path)[["ubigeo", "puntos_atencion"]]
    if not COMPETENCIA.exists():
        return None
    c = pd.read_csv(COMPETENCIA, dtype={"ubigeo": str}, encoding="utf-8-sig").dropna(subset=["ubigeo"])
    return c.groupby("ubigeo").size().rename("puntos_atencion").reset_index()


def entidades_relevadas() -> list[str]:
    if not COMPETENCIA.exists():
        return []
    return sorted(pd.read_csv(COMPETENCIA, encoding="utf-8-sig")["entidad"].dropna().unique())


def centroides(geo: dict) -> pd.DataFrame:
    """Centroide aproximado (promedio de vértices del anillo exterior más grande) sin dependencias GIS."""
    filas = []
    for f in geo["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        ring = max((p[0] for p in polys), key=len)
        lon, lat = np.mean(np.array(ring)[:, :2], axis=0)
        filas.append({"ubigeo": f["properties"]["IDDIST"], "lon": lon, "lat": lat})
    return pd.DataFrame(filas)


def agencia_cercana(df: pd.DataFrame, geo: dict) -> pd.DataFrame:
    """Para cada distrito: distrito con agencia CT más cercano (línea recta entre centroides, km).
    Es una aproximación para decidir si se atiende con asesores desde una agencia existente;
    la distancia por carretera en sierra puede ser 2-3 veces mayor."""
    c = centroides(geo).merge(df[["ubigeo", "distrito", "agencias_ct"]], on="ubigeo")
    con = c[c["agencias_ct"] > 0]
    if con.empty:
        return df.assign(agencia_cercana=pd.NA, km_agencia=np.nan)
    lat1, lon1 = np.radians(c[["lat"]].to_numpy()), np.radians(c[["lon"]].to_numpy())
    lat2, lon2 = np.radians(con["lat"].to_numpy()), np.radians(con["lon"].to_numpy())
    h = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    km = 2 * 6371 * np.arcsin(np.sqrt(h))
    idx = km.argmin(axis=1)
    c["agencia_cercana"] = np.where(c["agencias_ct"] > 0, c["distrito"], con["distrito"].to_numpy()[idx])
    c["km_agencia"] = np.where(c["agencias_ct"] > 0, 0, km.min(axis=1)).round(0)
    return df.merge(c[["ubigeo", "agencia_cercana", "km_agencia"]], on="ubigeo", how="left")


def oferta(df: pd.DataFrame, penalidad: float = PENALIDAD_OFERTA_MAX) -> tuple[pd.DataFrame, bool]:
    of = cargar_oferta()
    if of is None:
        df["factor_oferta"] = 1.0
        return df, False
    df = df.merge(of, on="ubigeo", how="left")
    df["oficinas_competencia"] = df["puntos_atencion"].fillna(0).astype(int)
    df["puntos_x1000"] = 1000 * df["oficinas_competencia"] / df["pob_18_64"]
    # sin competencia = sin penalidad; entre los que tienen, más oficinas por adulto = más penalidad
    con = df["puntos_x1000"] > 0
    df["factor_oferta"] = 1.0
    df.loc[con, "factor_oferta"] = 1 - penalidad * pct(df.loc[con, "puntos_x1000"])
    return df, True


def lentes(df: pd.DataFrame, pesos: dict = SEGMENTOS) -> dict[str, dict[str, pd.Series]]:
    """{segmento: {lente: serie 0-1}}"""
    return {seg: {lente: sum(w * df[k] for k, w in ws.items()) for lente, ws in d.items()}
            for seg, d in pesos.items()}


def puntuar(df: pd.DataFrame, alpha: float, pesos: dict = SEGMENTOS) -> tuple[pd.Series, pd.Series]:
    """Devuelve (score 0-100, segmento dominante)."""
    L = lentes(df, pesos)
    por_seg = pd.DataFrame({seg: alpha * d["volumen"] + (1 - alpha) * d["intensidad"] for seg, d in L.items()})
    return 100 * por_seg.max(axis=1) * df["factor_oferta"], por_seg.idxmax(axis=1)


def ordenar(score: pd.Series, segmento: pd.Series, cupo_agro: float) -> pd.Series:
    """Puesto combinado: intercala los rankings de cada segmento en proporción al cupo.
    Con cupo 0.4, de cada 5 puestos ~2 son agro y ~3 urbanos (los mejores de cada uno)."""
    cupo = {"agro": cupo_agro, "urbano": 1 - cupo_agro}
    r_seg = score.groupby(segmento).rank(ascending=False, method="first")
    clave = r_seg / segmento.map(cupo).clip(lower=1e-6)
    return pd.DataFrame({"c": clave, "s": -score}).apply(tuple, axis=1).rank(method="min").astype(int)


def explicar(row: pd.Series) -> str:
    """Segmento dominante, sus 2 componentes más fuertes y el más débil, con percentil."""
    seg = SEGMENTOS[row["segmento"]]
    comps = list(dict.fromkeys(k for ws in seg.values() for k in ws))
    orden = sorted(comps, key=lambda k: -row[k])
    fuertes = "; ".join(f"{COMPONENTES[k][1]} (p{row[k] * 100:.0f})" for k in orden[:2])
    k = orden[-1]
    return f"[{row['segmento']}] + {fuertes} | − {COMPONENTES[k][1]} (p{row[k] * 100:.0f})"


def sensibilidad(df: pd.DataFrame, alpha: float, cupo_agro: float, n: int = 1000, top: int = 10, seed: int = 7) -> pd.DataFrame:
    """Perturba los pesos de cada lente (Dirichlet centrado en los pesos base) y alpha (±0.15).
    Devuelve, por distrito, % de simulaciones en el top-N y rango intercuartil del puesto."""
    rng = np.random.default_rng(seed)
    ranks = np.empty((n, len(df)))
    for s in range(n):
        pesos = {seg: {lente: dict(zip(ws, rng.dirichlet(np.array(list(ws.values())) * 20)))
                       for lente, ws in d.items()} for seg, d in SEGMENTOS.items()}
        a = float(np.clip(alpha + rng.uniform(-0.15, 0.15), 0, 1))
        ranks[s] = ordenar(*puntuar(df, a, pesos), cupo_agro).to_numpy()
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
    agro_top = int(((df["puesto"] <= top) & (df["segmento"] == "agro")).sum())
    lines.append(f"- Distritos de segmento agro en el top-{top}: **{agro_top}** de {top} (fijado por el cupo agro).")
    if rural_top == 0:
        lines.append(f"- ⚠ Ningún distrito del tercil de menor densidad entra al top-{top}: los más remotos quedan fuera "
                     "aunque haya agro. Si importa llegar a ellos, bajar alpha o evaluar un canal distinto "
                     "(agentes, agencia móvil).")
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


def mapa(df: pd.DataFrame, geo: dict, alpha: float, cupo_agro: float, con_oferta: bool) -> None:
    cols = ["ubigeo", "distrito", "provincia", "segmento", "puesto", "score", "score_volumen", "score_intensidad",
            "pob_18_64", "ruc_activos_habidos", "empresas_x1000", "puestos_mercado", "productores", "prod_excluidos",
            "razones", "pct_en_top", "oficinas_competencia", "agencias_ct", "agencia_cercana", "km_agencia"]
    props = df[cols].round(2).set_index("ubigeo").to_dict(orient="index")
    feats = []
    for f in geo["features"]:
        p = props.get(f["properties"]["IDDIST"])
        if p:
            feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {"ubigeo": f["properties"]["IDDIST"], **p}})
    data = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False)
    html = MAPA_HTML.replace("__LEAFLET__", leaflet()).replace("__DATA__", data).replace("__ALPHA__", f"{alpha:.2f} · cupo agro {cupo_agro:.0%}").replace("__VERSION__", VERSION).replace(
        "__OFERTA__", "competencia relevada: " + ", ".join(entidades_relevadas()) if con_oferta else "pendiente")
    (OUT / f"mapa_indice_{VERSION}.html").write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.6, help="peso del lente VOLUMEN dentro de cada segmento (0-1)")
    ap.add_argument("--cupo-agro", type=float, default=0.4, help="fracción de la lista combinada para el segmento agro")
    ap.add_argument("--penalidad-competencia", type=float, default=PENALIDAD_OFERTA_MAX,
                    help="máximo descuento por oficinas de la competencia (0 = la competencia no resta)")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    df, geo = cargar()
    df, con_oferta = oferta(df, args.penalidad_competencia)
    if df["agencias_ct"].notna().all():
        df = agencia_cercana(df, geo)
    for k, (col, _) in COMPONENTES.items():
        df[k] = pct(df[col])
    df["score_volumen"] = puntuar(df, 1.0)[0] / df["factor_oferta"]
    df["score_intensidad"] = puntuar(df, 0.0)[0] / df["factor_oferta"]
    df["score"], df["segmento"] = puntuar(df, args.alpha)
    df["puesto"] = ordenar(df["score"], df["segmento"], args.cupo_agro)
    df["puesto_segmento"] = df.groupby("segmento")["score"].rank(ascending=False, method="first").astype(int)
    df["razones"] = df.apply(explicar, axis=1)
    df = df.merge(sensibilidad(df, args.alpha, args.cupo_agro, top=args.top), on="ubigeo")
    df = df.sort_values("puesto")

    salida = ["puesto", "ubigeo", "distrito", "provincia", "segmento", "puesto_segmento", "score", "score_volumen", "score_intensidad",
              "factor_oferta", "pct_en_top", "puesto_p25", "puesto_p75", "pob_18_64", "mujeres_18_64",
              "ruc_activos_habidos", "empresas_x1000", "mercados", "puestos_mercado", "productores", "prod_excluidos",
              "tasa_exclusion_agro", "prod_credito_cmac", "densidad_hab_km2", "agencias_ct", "oficinas_competencia", "agencia_cercana", "km_agencia", "razones"]
    df[salida].round(3).to_csv(OUT / f"ranking_{VERSION}.csv", index=False, encoding="utf-8-sig")  # sig: abre bien en Excel
    reporte(df, args.alpha, args.cupo_agro, args.top, con_oferta)
    mapa(df, geo, args.alpha, args.cupo_agro, con_oferta)

    print(f"alpha={args.alpha}  cupo agro={args.cupo_agro:.0%}  penalidad competencia={args.penalidad_competencia:.0%}  competencia: {', '.join(entidades_relevadas()) if con_oferta else 'NO (correr fase0/competencia.py)'}\n")
    print(df[["puesto", "distrito", "provincia", "segmento", "score", "pct_en_top"]].head(args.top).to_string(index=False))
    print(f"\n-> salidas/ranking_{VERSION}.csv, salidas/reporte_indice_{VERSION}.md, salidas/mapa_indice_{VERSION}.html")
    return 0


def reporte(df: pd.DataFrame, alpha: float, cupo_agro: float, top: int, con_oferta: bool) -> None:
    L = [f"# Índice de oportunidad {VERSION} — La Libertad", "",
         f"alpha (peso de VOLUMEN) = **{alpha}** · cupo agro = **{cupo_agro:.0%}** · competencia relevada: **{', '.join(entidades_relevadas()) if con_oferta else 'pendiente'}** · "
         f"{len(df)} distritos", "",
         "## Cómo se calcula", "",
         "Cada variable se convierte a percentil dentro de La Libertad (0 a 1) y se pondera:", "",
         "| segmento · lente | variable | peso dentro del lente |", "|---|---|---:|"]
    L += [f"| {seg} · {lente} | {COMPONENTES[k][1]} (`{COMPONENTES[k][0]}`) | {w:.0%} |"
          for seg, d in SEGMENTOS.items() for lente, ws in d.items() for k, w in ws.items()]
    L += ["", "`score_seg = α·volumen_seg + (1−α)·intensidad_seg` · `score = 100 × max(score_urbano, score_agro) × factor_oferta`", "",
          "Cada distrito compite con su segmento más fuerte: un distrito urbano no pierde puntos por no tener agro, "
          "ni uno andino por no tener mercados.", "",
          f"La lista combinada intercala el ranking de cada segmento: {cupo_agro:.0%} de los puestos para agro y "
          f"{1 - cupo_agro:.0%} para urbano. Ese reparto es una decisión de cartera del owner, no un resultado del modelo.", "",
          "| segmento dominante | distritos | productores excluidos | adultos 18-64 |", "|---|---:|---:|---:|"]
    L += [f"| {seg} | {len(g)} | {g['prod_excluidos'].sum():,.0f} | {g['pob_18_64'].sum():,.0f} |"
          for seg, g in df.groupby("segmento")]
    L += ["",
          f"## Top {top}", "",
          f"`estabilidad` = % de 1 000 simulaciones (pesos y α perturbados) en que el distrito sigue en el top-{top}.", "",
          "| # | distrito | provincia | segmento | score | estabilidad | por qué |", "|---:|---|---|---|---:|---:|---|"]
    L += [f"| {r.puesto} | {r.distrito} | {r.provincia} | {r.segmento} | {r.score:.1f} | {r.pct_en_top:.0%} | {r.razones} |"
          for r in df.head(top).itertuples()]
    if df["agencias_ct"].notna().all():
        L += ["", "## Espacios en blanco: prioridades sin agencia de Caja Trujillo", "",
              f"De los {top} primeros, **{int((df.head(top)['agencias_ct'] == 0).sum())}** no tienen agencia propia "
              "(fuente: web de Caja Trujillo). Son candidatos a otro canal (asesores itinerantes, agentes, agencia móvil) "
              "o a apertura; en los que sí tienen agencia, la acción es prospección desde la agencia existente.", "",
              "`agencia más cercana`: distrito con agencia propia más cercano en línea recta (en sierra, por carretera puede ser 2-3 veces más).", "",
              "| # | distrito | segmento | agencias CT | agencia más cercana | km (recta) | adultos 18-64 | productores excluidos |",
              "|---:|---|---|---:|---|---:|---:|---:|"]
        L += [f"| {r.puesto} | {r.distrito} | {r.segmento} | {r.agencias_ct} | "
              f"{'—' if r.agencias_ct else r.agencia_cercana} | {'—' if r.agencias_ct else f'{r.km_agencia:.0f}'} | "
              f"{r.pob_18_64:,.0f} | {r.prod_excluidos:,.0f} |"
              for r in df.head(top).itertuples()]
    L += ["", "## Auditoría de sesgo urbano/rural", ""] + auditoria(df, top)
    L += ["", "## Limitaciones (decirlas en el pitch)", "",
          "- El padrón RUC reducido solo trae ubigeo para personas jurídicas (RUC 20); las personas naturales "
          "con negocio (RUC 10) casi nunca lo tienen. `ruc_activos_habidos` mide **empresas formales**, no microempresarios.",
          "- CENAMA es de 2016 y CENAGRO de 2012: la estructura es estable, pero los montos pueden haber cambiado.",
          "- La competencia por distrito cubre solo las entidades que publican su red (Mibanco, Efectiva, cajas Arequipa, Del Santa y Paita: ~31 % de las oficinas de la competencia). Falta Compartamos, cajas Huancayo, Piura y Cusco, y la banca tradicional (concentrada en Trujillo metropolitano). No incluye agentes corresponsales.",
          "- Es un índice de priorización territorial, no evalúa a personas ni su riesgo crediticio.",
          "- Alto Trujillo (130112) no tiene polígono en el mapa base: aparece en el ranking pero no en el mapa."]
    (OUT / f"reporte_indice_{VERSION}.md").write_text("\n".join(L) + "\n", encoding="utf-8")


MAPA_HTML = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Índice de oportunidad __VERSION__</title>
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
  li b{font-weight:600}.seg{font-size:11px;padding:1px 6px;border-radius:8px;background:var(--card);border:1px solid var(--line)}
  .seg.agro{border-color:#3d9a50;color:#3d9a50}.seg.sin{border-color:#c2410c;color:#c2410c}.seg.urbano{border-color:#2f6fde;color:#2f6fde}.why{color:var(--muted);font-size:12px}
  .legend{background:var(--bg);color:var(--fg);padding:8px 10px;border-radius:6px;font-size:12px;box-shadow:0 1px 4px #0003}
  .legend i{display:inline-block;width:14px;height:10px;margin-right:4px}
  @media (max-width:800px){.wrap{grid-template-columns:1fr;grid-template-rows:55vh auto;height:auto}aside{border-left:0}}
</style></head><body>
<div class="wrap"><div id="map"></div><aside>
<h1>Índice de oportunidad __VERSION__ · La Libertad</h1>
<div class="sub">α = __ALPHA__ · __OFERTA__ · datos públicos (SUNAT, RENIEC, CENAMA, CENAGRO)</div>
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
  onEachFeature:(f,l)=>{const p=f.properties;l.bindPopup(`<b>${p.distrito}</b> (${p.provincia})<br>Segmento: ${p.segmento} · puesto #${p.puesto} · score ${p.score.toFixed(1)}<br>Volumen ${p.score_volumen.toFixed(1)} · Intensidad ${p.score_intensidad.toFixed(1)}<br>Adultos 18-64: ${fmt(p.pob_18_64)}<br>Empresas activas: ${fmt(p.ruc_activos_habidos)} (${p.empresas_x1000.toFixed(1)}/1000)<br>Puestos de mercado: ${fmt(p.puestos_mercado)}<br>Productores agro: ${fmt(p.productores)} (${fmt(p.prod_excluidos)} sin acceso a crédito)<br>Oficinas competencia relevada: ${p.oficinas_competencia ?? "s/d"}<br>Agencias Caja Trujillo: <b>${p.agencias_ct ?? "s/d"}</b>${p.agencias_ct===0?` (la más cercana: ${p.agencia_cercana}, ~${p.km_agencia} km en recta)`:""}<br>Estabilidad en top: ${Math.round(p.pct_en_top*100)}%<br><i>${p.razones}</i>`);}}).addTo(map);
map.fitBounds(layer.getBounds());
const legend = L.control({position:"bottomleft"});
legend.onAdd = () => { const d=L.DomUtil.create("div","legend"); d.id="lg"; return d; };
legend.addTo(map);
function render(){
  br = breaks(); layer.setStyle(f=>({fillColor:col(f.properties[key])}));
  document.getElementById("lg").innerHTML = "<b>"+({score:"Final",score_volumen:"Volumen",score_intensidad:"Intensidad"})[key]+"</b><br>"+
    colors.map((c,i)=>`<i style="background:${c}"></i>${i?"≥ "+br[i-1].toFixed(0):"menor"}`).join("<br>");
  // "Final" sigue el orden combinado (con cupo por segmento); las otras pestañas, el puntaje del lente.
  const ord = key==="score" ? (a,b)=>a.properties.puesto-b.properties.puesto : (a,b)=>b.properties[key]-a.properties[key];
  const top = [...data.features].sort(ord).slice(0,20);
  document.getElementById("list").innerHTML = top.map(f=>`<li data-u="${f.properties.ubigeo}"><b>${f.properties.distrito}</b> · <span class="seg ${f.properties.segmento}">${f.properties.segmento}</span>${f.properties.agencias_ct===0?' <span class="seg sin">sin agencia CT</span>':''} · ${f.properties[key].toFixed(1)}<div class="why">${f.properties.provincia} · ${f.properties.razones}</div></li>`).join("");
}
document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tabs button").forEach(x=>x.classList.remove("on"));b.classList.add("on");key=b.dataset.k;render();});
document.getElementById("list").onclick = e => { const li=e.target.closest("li"); if(!li) return;
  layer.eachLayer(l=>{ if(l.feature.properties.ubigeo===li.dataset.u){ map.fitBounds(l.getBounds(),{maxZoom:11}); l.openPopup(); }}); };
render();
</script></body></html>
"""

if __name__ == "__main__":
    sys.exit(main())
