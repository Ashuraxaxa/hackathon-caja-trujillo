"""Valida las fuentes descargadas y genera tablas limpias del ámbito piloto.

Uso:
    python fase0/validate.py

Salidas:
    data/interim/*.parquet / *.geojson   tablas filtradas al ámbito piloto
    data/interim/reporte_fase0.md        reporte legible de calidad y cobertura
Devuelve código 1 si falla algún chequeo bloqueante.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from sources import DEPARTAMENTOS_PILOTO, SOURCES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "interim"
OUT.mkdir(parents=True, exist_ok=True)

checks: list[tuple[str, str, bool, str]] = []  # (fuente, chequeo, ok, detalle)
notes: list[str] = []


def check(fuente: str, nombre: str, ok: bool, detalle: str = "", blocking: bool = True) -> bool:
    status = "OK " if ok else ("FAIL" if blocking else "WARN")
    print(f"  [{status}] {fuente}: {nombre} {('- ' + detalle) if detalle else ''}")
    checks.append((fuente, nombre, ok if blocking else True, f"{'' if ok else '⚠ '}{detalle}"))
    return ok


def in_piloto(ubigeo: pd.Series) -> pd.Series:
    return ubigeo.str[:2].isin(DEPARTAMENTOS_PILOTO)


# ---------------------------------------------------------------- límites
def limites() -> set[str]:
    print("\n== Límites distritales")
    gj = json.loads((RAW / SOURCES["limites_distritales"]["dest"]).read_text())
    feats = gj["features"]
    check("limites", "features > 1800", len(feats) > 1800, f"{len(feats)} distritos en el país")
    piloto = [f for f in feats if f["properties"]["IDDPTO"] in DEPARTAMENTOS_PILOTO]
    ubigeos = {f["properties"]["IDDIST"] for f in piloto}
    check("limites", "distritos en ámbito piloto", len(ubigeos) > 0, f"{len(ubigeos)} distritos")
    bad_geom = [f["properties"]["IDDIST"] for f in piloto if not f.get("geometry")]
    check("limites", "todas las geometrías presentes", not bad_geom, f"{len(bad_geom)} sin geometría")
    (OUT / "limites_piloto.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": piloto}, ensure_ascii=False)
    )
    notes.append(
        "Los límites (juaneladio/peru-geojson) tienen 1 834 distritos; hoy existen ~1 890. "
        "Los distritos creados después no tienen polígono: se reportan abajo como 'sin polígono'."
    )
    return ubigeos


# ---------------------------------------------------------------- SUNAT RUC
RUC_COLS = ["ruc", "razon_social", "estado", "condicion", "ubigeo", "tipo_via", "nombre_via",
            "cod_zona", "tipo_zona", "numero", "interior", "lote", "dpto", "manzana", "km"]


def sunat(ubigeos_geo: set[str]) -> pd.DataFrame:
    print("\n== SUNAT padrón RUC (lectura en bloques, ~1.6 GB)")
    zpath = RAW / SOURCES["sunat_ruc"]["dest"]
    check("sunat", "zip íntegro", zipfile.ZipFile(zpath).testzip() is None)
    total = sin_ubigeo = 0
    parts = []
    with zipfile.ZipFile(zpath) as z, z.open(z.namelist()[0]) as fh:
        header = fh.readline().decode("latin-1").strip().rstrip("|").split("|")
        check("sunat", "esquema de 15 columnas", len(header) == 15, " | ".join(header[:5]) + " ...")
        reader = pd.read_csv(
            fh, sep="|", header=None, names=RUC_COLS + ["_extra"], usecols=range(15),
            dtype=str, encoding="latin-1", quoting=3, chunksize=1_000_000,
            on_bad_lines="skip", na_values=["-"], keep_default_na=False,
        )
        for chunk in reader:
            chunk = chunk.replace(r"^-+$", pd.NA, regex=True)  # '-', '----' = vacío
            total += len(chunk)
            sin_ubigeo += chunk["ubigeo"].isna().sum()
            ch = chunk[chunk["ubigeo"].notna() & in_piloto(chunk["ubigeo"].fillna(""))]
            parts.append(ch)
    df = pd.concat(parts, ignore_index=True)
    check("sunat", "filas totales > 10 M", total > 10_000_000, f"{total:,} contribuyentes")
    check("sunat", "% sin ubigeo", True, f"{sin_ubigeo / total:.1%} sin ubigeo (no geolocalizables)", blocking=False)
    check("sunat", "RUC de 11 dígitos", df["ruc"].str.fullmatch(r"\d{11}").all())
    check("sunat", "RUC únicos", df["ruc"].is_unique, f"{df['ruc'].duplicated().sum()} duplicados")

    df["tipo_persona"] = df["ruc"].str[:2].map(
        {"10": "natural", "15": "natural_otro", "17": "natural_otro", "20": "juridica"}).fillna("otro")
    df["activo_habido"] = (df["estado"] == "ACTIVO") & (df["condicion"] == "HABIDO")
    df["tiene_direccion"] = df["nombre_via"].notna() | df["cod_zona"].notna()
    notes.append("Padrón RUC: estados 'BAJA' y 'NUM. INTERNO IDENTIF' no son negocios operando; "
                 "para señales de actividad usar solo activo_habido. No trae actividad económica (CIIU) "
                 "ni coordenadas: la geolocalización fina requiere geocodificar la dirección (Fase 2).")
    check("sunat", "contribuyentes en ámbito piloto", len(df) > 0,
          f"{len(df):,} ({df['activo_habido'].mean():.0%} activos y habidos, "
          f"{df['tiene_direccion'].mean():.0%} con dirección)")
    sin_geo = set(df["ubigeo"]) - ubigeos_geo
    check("sunat", "ubigeos casan con polígonos", len(sin_geo) <= 5,
          f"{len(sin_geo)} ubigeos sin polígono: {sorted(sin_geo)[:8]}", blocking=False)
    df.to_parquet(OUT / "ruc_piloto.parquet", index=False)

    dist = (df.groupby("ubigeo")
              .agg(ruc_total=("ruc", "size"),
                   ruc_activos_habidos=("activo_habido", "sum"),
                   ruc_pn_activos=("activo_habido", lambda s: (s & (df.loc[s.index, "tipo_persona"] == "natural")).sum()),
                   ruc_pj_activos=("activo_habido", lambda s: (s & (df.loc[s.index, "tipo_persona"] == "juridica")).sum()))
              .reset_index())
    dist.to_parquet(OUT / "ruc_por_distrito.parquet", index=False)
    return dist


# ---------------------------------------------------------------- RENIEC
def reniec(ubigeos_geo: set[str]) -> pd.DataFrame:
    print("\n== RENIEC población identificada")
    path = RAW / SOURCES["reniec_poblacion"]["dest"]
    df = pd.read_csv(path, dtype={"UBIGEO_INEI": str, "UBIGEO_RENIEC": str}, encoding="utf-8-sig")
    need = {"Residencia", "UBIGEO_INEI", "Sexo", "Edad", "Cantidad"}
    check("reniec", "columnas esperadas", need <= set(df.columns), str(sorted(need - set(df.columns))))
    nac = df[df["Residencia"] == "Nacional"].copy()
    total_pe = nac["Cantidad"].sum()
    check("reniec", "población nacional plausible (30-40 M)", 30e6 < total_pe < 40e6, f"{total_pe:,.0f}")
    nac["Edad"] = pd.to_numeric(nac["Edad"], errors="coerce")
    p = nac[in_piloto(nac["UBIGEO_INEI"].fillna(""))]
    check("reniec", "edades válidas", p["Edad"].between(0, 120).mean() > 0.99,
          f"{p['Edad'].isna().sum()} sin edad")
    p = p.assign(adulto=p["Edad"] >= 18, adulto_18_64=p["Edad"].between(18, 64),
                 mujer=p["Sexo"].str.lower().str.startswith("muj"))
    dist = (p.assign(pob=p["Cantidad"],
                     pob_18_64=p["Cantidad"] * p["adulto_18_64"],
                     pob_adulta=p["Cantidad"] * p["adulto"],
                     mujeres_18_64=p["Cantidad"] * (p["adulto_18_64"] & p["mujer"]))
             .groupby("UBIGEO_INEI")[["pob", "pob_adulta", "pob_18_64", "mujeres_18_64"]].sum()
             .reset_index().rename(columns={"UBIGEO_INEI": "ubigeo"}))
    check("reniec", "población del ámbito piloto", True,
          f"{dist['pob'].sum():,.0f} personas, {dist['pob_18_64'].sum():,.0f} de 18-64 años")
    sin_geo = set(dist["ubigeo"]) - ubigeos_geo
    check("reniec", "ubigeos casan con polígonos", len(sin_geo) <= 5,
          f"{len(sin_geo)} sin polígono: {sorted(sin_geo)[:8]}", blocking=False)
    dist.to_parquet(OUT / "poblacion_por_distrito.parquet", index=False)
    return dist


# ---------------------------------------------------------------- CENAMA
def cenama() -> pd.DataFrame:
    print("\n== CENAMA mercados de abastos")
    df = pd.read_csv(RAW / SOURCES["cenama_mercados"]["dest"], sep="|", dtype={"ubigeo": str},
                     encoding="utf-8", encoding_errors="replace")
    check("cenama", "filas > 2 000", len(df) > 2000, f"{len(df):,} mercados")
    p = df[in_piloto(df["ubigeo"].str.zfill(6))].copy()
    p["ubigeo"] = p["ubigeo"].str.zfill(6)
    check("cenama", "mercados en ámbito piloto", len(p) > 0,
          f"{len(p)} mercados, {pd.to_numeric(p['nro_puestos_funcionando'], errors='coerce').sum():,.0f} puestos funcionando")
    dist = (p.assign(puestos=pd.to_numeric(p["nro_puestos_funcionando"], errors="coerce"))
              .groupby("ubigeo").agg(mercados=("ubigeo", "size"), puestos_mercado=("puestos", "sum"))
              .reset_index())
    dist.to_parquet(OUT / "mercados_por_distrito.parquet", index=False)
    notes.append("CENAMA es de 2016 y no trae coordenadas: sirve a nivel distrito, no hexágono.")
    return dist


# ---------------------------------------------------------------- opcionales / manuales
def opcionales() -> None:
    print("\n== Fuentes opcionales y manuales")
    for key, src in SOURCES.items():
        if src["mode"] == "auto":
            continue
        dest = RAW / src["dest"]
        files = [f for f in dest.glob("*") if f.is_file()] if src["dest"].endswith("/") else ([dest] if dest.exists() else [])
        ok = any(f.stat().st_size >= src["min_bytes"] for f in files)
        check(key, "presente", ok, "listo" if ok else f"pendiente ({src['mode']}): {src.get('how', src['url'])}",
              blocking=False)


# ---------------------------------------------------------------- main
def main() -> int:
    ubigeos = limites()
    ruc = sunat(ubigeos)
    pob = reniec(ubigeos)
    mer = cenama()
    opcionales()

    print("\n== Tabla base por distrito")
    base = (pd.DataFrame({"ubigeo": sorted(ubigeos | set(pob["ubigeo"]))})
              .merge(pob, on="ubigeo", how="left").merge(ruc, on="ubigeo", how="left")
              .merge(mer, on="ubigeo", how="left"))
    base[["mercados", "puestos_mercado"]] = base[["mercados", "puestos_mercado"]].fillna(0)
    base["tiene_poligono"] = base["ubigeo"].isin(ubigeos)
    base["ruc_activos_x1000_adultos"] = (1000 * base["ruc_activos_habidos"] / base["pob_18_64"]).round(1)
    check("base", "todos los distritos tienen población", base["pob"].notna().all(),
          f"{base['pob'].isna().sum()} sin dato RENIEC")
    check("base", "todos los distritos tienen RUC", base["ruc_total"].notna().all(),
          f"{base['ruc_total'].isna().sum()} sin contribuyentes")
    base.to_parquet(OUT / "base_distrital.parquet", index=False)
    base.to_csv(OUT / "base_distrital.csv", index=False)

    fails = [c for c in checks if not c[2]]
    write_report(base, fails)
    print(f"\n{'TODO OK' if not fails else f'{len(fails)} chequeos fallidos'} -> data/interim/reporte_fase0.md")
    return 1 if fails else 0


def write_report(base: pd.DataFrame, fails: list) -> None:
    manifest = json.loads((RAW / "manifest.json").read_text()) if (RAW / "manifest.json").exists() else {}
    lines = ["# Reporte Fase 0 — calidad de datos públicos", "",
             f"Ámbito piloto: departamentos {', '.join(DEPARTAMENTOS_PILOTO)}  ·  "
             f"{len(base)} distritos  ·  {'sin fallas bloqueantes' if not fails else f'{len(fails)} fallas bloqueantes'}", "",
             "## Fuentes descargadas", "", "| fuente | bytes | sha256 (12) | fecha |", "|---|---:|---|---|"]
    for k, m in manifest.items():
        lines.append(f"| {k} | {m['bytes']:,} | `{m['sha256'][:12]}` | {m['downloaded_at']} |")
    lines += ["", "## Chequeos", "", "| fuente | chequeo | resultado |", "|---|---|---|"]
    lines += [f"| {f} | {n} | {'✅' if ok else '❌'} {d} |" for f, n, ok, d in checks]
    lines += ["", "## Notas", ""] + [f"- {n}" for n in notes]
    top = base.sort_values("pob_18_64", ascending=False).head(15)
    lines += ["", "## Vista rápida: 15 distritos más poblados (18-64)", "",
              "| ubigeo | pob 18-64 | RUC activos | RUC/1000 adultos | mercados |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {r.ubigeo} | {r.pob_18_64:,.0f} | {r.ruc_activos_habidos:,.0f} | {r.ruc_activos_x1000_adultos} | {r.mercados:.0f} |"
              for r in top.itertuples()]
    (OUT / "reporte_fase0.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
