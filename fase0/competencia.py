"""Oficinas de la competencia por distrito, tomadas de las webs públicas de cada entidad.

Uso:
    python fase0/competencia.py            # descarga (con caché en data/raw/competencia/) y procesa
    python fase0/competencia.py --offline  # solo procesa lo ya descargado

Salida: data/manual/oficinas_competencia.csv (una fila por oficina):
    entidad, tipo, nombre, direccion, distrito, ubigeo, lat, lng, fuente, url, fecha_consulta

Las filas con fuente = "manual" (agregadas a mano por el equipo, p. ej. Compartamos o Caja Huancayo)
se conservan al volver a correr el script; las de fuente = "web" se regeneran.

Cobertura: solo entidades que publican su red en una página o documento público. BCP, BBVA,
Interbank y Caja Piura bloquean el acceso automatizado; Compartamos, Caja Huancayo y Caja Cusco
cargan su red desde servicios internos que no consultamos. El script compara lo encontrado con el
total de oficinas por entidad que reporta la SBS (data/interim/oficinas_sbs_departamento.csv).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "raw" / "competencia"
OUT = ROOT / "data" / "manual" / "oficinas_competencia.csv"
INTERIM = ROOT / "data" / "interim"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
DEP = "LA LIBERTAD"

FUENTES = {
    "mibanco": "https://www.mibanco.com.pe/centro-de-ayuda/ubicanos",
    "efectiva": "https://www.efectibank.pe/agencias/",
    "arequipa": "https://www.cajaarequipa.pe/wp-content/uploads/2026/07/Cajamarca-La-Libertad-Ancash-Piura-Lambayeque-Tumbes-junio-26.pdf",
    "delsanta": "https://www.cajadelsanta.pe/agencia-trujillo/",
    "paita": "https://www.cajapaita.pe/agencias/",
}
# Nombre en la SBS de cada entidad relevada (para comparar cobertura).
SBS_NOMBRE = {"Mibanco": "Mibanco", "Banco Efectiva": "B. Efectiva", "CMAC Arequipa": "CMAC AREQUIPA",
              "CMAC Del Santa": "CMAC DEL SANTA", "CMAC Paita": "CMAC PAITA"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


def bajar(clave: str, offline: bool) -> Path:
    url = FUENTES[clave]
    dest = CACHE / (clave + (".pdf" if url.endswith(".pdf") else ".html"))
    if not offline:
        CACHE.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=UA, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
    if not dest.exists():
        raise FileNotFoundError(dest)
    return dest


def distritos_ll() -> pd.DataFrame:
    geo = json.loads((INTERIM / "limites_piloto.geojson").read_text(encoding="utf-8"))
    d = pd.DataFrame([{"ubigeo": f["properties"]["IDDIST"], "distrito": norm(f["properties"]["NOMBDIST"]),
                       "provincia": norm(f["properties"]["NOMBPROV"])} for f in geo["features"]])
    extra = pd.DataFrame([{"ubigeo": "130112", "distrito": "ALTO TRUJILLO", "provincia": "TRUJILLO"}])
    return pd.concat([d, extra], ignore_index=True)


# ------------------------------------------------------------------ parsers
def p_mibanco(path: Path) -> list[dict]:
    t = path.read_text(encoding="utf-8", errors="replace")
    arr = json.loads(re.search(r"window\.__mbOficinas\s*=\s*(\[.*?\]);", t, re.S).group(1))
    return [{"entidad": "Mibanco", "tipo": "banca microfinanciera", "nombre": o["name"], "direccion": o["direccion"],
             "distrito": o["dist"], "lat": o["lat"], "lng": o["lng"]} for o in arr if norm(o["dep"]) == DEP]


def p_efectiva(path: Path) -> list[dict]:
    t = path.read_text(encoding="utf-8", errors="replace")
    objs = [json.loads(m.group(0)) for m in re.finditer(r'\{"id":"\d+","name":[^{}]*?"company_logo":"[^"]*"\}', t)]
    vistos, out = set(), []
    for o in objs:
        if norm(o.get("departamento")) != DEP or o.get("category_name") != "Agencias" or o.get("is_active") != "1":
            continue
        if o["id"] in vistos:
            continue
        vistos.add(o["id"])
        out.append({"entidad": "Banco Efectiva", "tipo": "banca consumo/micro (dentro de tiendas)",
                    "nombre": f'{o["name"]} ({o["company_name"]})', "direccion": o["address"],
                    "distrito": o["distrito"], "lat": o["lat"], "lng": o["lng"]})
    return out


def p_arequipa(path: Path, dist: pd.DataFrame) -> list[dict]:
    from pypdf import PdfReader
    texto = "\n".join(p.extract_text() for p in PdfReader(str(path)).pages)
    registros = re.split(r"\n(?=\d{2} )", texto)
    pares = [(norm(r.distrito).replace(" ", "") + norm(r.provincia).replace(" ", ""), r.distrito)
             for r in dist.itertuples()]
    out = []
    for reg in registros:
        plano = norm(reg).replace(" ", "")
        if "LALIBERTAD" not in plano:
            continue
        antes = plano.split("LALIBERTAD")[0]
        # el PDF parte palabras con espacios: se compara sin espacios "DISTRITOPROVINCIA" al final del tramo
        match = max((p for p in pares if antes.endswith(p[0])), key=lambda p: len(p[0]), default=None)
        if match is None:  # "La Libertad" aparece en el título del PDF y se pega al registro vecino
            continue
        nombre = re.match(r"\d{2} (.+?) (Av\.|Jr\.|Jirón|Calle|Centro|Esq|Prolong|Mz)", reg)
        out.append({"entidad": "CMAC Arequipa", "tipo": "caja municipal",
                    "nombre": nombre.group(1).strip() if nombre else reg[:30],
                    "direccion": re.sub(r"\s+", " ", reg)[:120], "distrito": match[1] if match else None,
                    "lat": None, "lng": None})
    return out


def p_estaticas() -> list[dict]:
    """Entidades con una sola oficina en La Libertad: dirección leída de su página pública."""
    return [
        {"entidad": "CMAC Del Santa", "tipo": "caja municipal", "nombre": "Agencia Trujillo",
         "direccion": "Calle Grau N° 359-B, Trujillo", "distrito": "TRUJILLO", "lat": None, "lng": None,
         "_fuente": "delsanta"},
        {"entidad": "CMAC Paita", "tipo": "caja municipal", "nombre": "Agencia Chepén",
         "direccion": "Calle Cajamarca N° 645, Chepén", "distrito": "CHEPEN", "lat": None, "lng": None,
         "_fuente": "paita"},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    dist = distritos_ll()
    hoy = dt.date.today().isoformat()
    filas = []
    for clave, fn in [("mibanco", p_mibanco), ("efectiva", p_efectiva),
                      ("arequipa", lambda p: p_arequipa(p, dist))]:
        try:
            rows = fn(bajar(clave, args.offline))
            for r in rows:
                r["_fuente"] = clave
            filas += rows
            print(f"[ok]    {clave}: {len(rows)} oficinas en La Libertad")
        except Exception as e:  # noqa: BLE001 - una web caída no debe frenar al resto
            print(f"[ERROR] {clave}: {e.__class__.__name__}: {e}")
    for r in p_estaticas():
        try:
            bajar(r["_fuente"], args.offline)  # verifica que la página siga publicada
            filas.append(r)
            print(f"[ok]    {r['_fuente']}: 1 oficina en La Libertad")
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] {r['_fuente']}: {e}")

    df = pd.DataFrame(filas)
    df["url"] = df.pop("_fuente").map(FUENTES)
    df["fuente"] = "web"
    df["fecha_consulta"] = hoy
    lookup = dict(zip(dist["distrito"], dist["ubigeo"]))
    df["ubigeo"] = df["distrito"].map(lambda d: lookup.get(norm(d)) if pd.notna(d) else None)
    sin = df[df["ubigeo"].isna()]
    if len(sin):
        print(f"\n⚠ {len(sin)} oficinas sin distrito reconocido (revisar a mano):")
        print(sin[["entidad", "nombre", "distrito"]].to_string(index=False))

    if OUT.exists():  # conservar lo cargado a mano
        prev = pd.read_csv(OUT, dtype=str, encoding="utf-8-sig")
        manual = prev[prev["fuente"] == "manual"]
        df = pd.concat([df, manual], ignore_index=True)
    cols = ["entidad", "tipo", "nombre", "direccion", "distrito", "ubigeo", "lat", "lng", "fuente", "url", "fecha_consulta"]
    df[cols].to_csv(OUT, index=False, encoding="utf-8-sig")

    sbs_path = INTERIM / "oficinas_sbs_departamento.csv"
    if sbs_path.exists():
        sbs = pd.read_csv(sbs_path, encoding="utf-8-sig")
        sbs = sbs[(sbs["departamento"] == "La Libertad") & (sbs["oficinas"] > 0) & (sbs["empresa"] != "CMAC TRUJILLO")]
        sbs_tot = sbs.set_index("empresa")["oficinas"]
        print("\nCobertura frente a la SBS (oficinas en La Libertad):")
        for ent, n in df.groupby("entidad").size().items():
            ref = sbs_tot.get(SBS_NOMBRE.get(ent, ent))
            print(f"  {ent:<18} web {n:>3} · SBS {ref if ref is not None else '?':>3}")
        print(f"  TOTAL relevado: {len(df)} de {int(sbs_tot.sum())} oficinas de la competencia "
              f"({len(df) / sbs_tot.sum():.0%}). Faltan: "
              + ", ".join(sorted(set(sbs_tot.index) - {SBS_NOMBRE.get(e, e) for e in df['entidad'].unique()})))
    print(f"\n-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
