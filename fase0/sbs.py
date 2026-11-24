"""Lee los Excel de la SBS "Distribución de Oficinas por Zona Geográfica" (data/raw/sbs/).

Uso:
    python fase0/sbs.py

Estos reportes vienen por DEPARTAMENTO (solo Lima/Callao se abre por distrito), así que
no alimentan el factor de oferta distrital del índice. Sirven como contexto competitivo:
cuántas oficinas tiene cada entidad en el ámbito piloto.

Salida: data/interim/oficinas_sbs_departamento.csv (empresa, tipo, departamento, oficinas, fecha)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "sbs"
OUT = ROOT / "data" / "interim"

TIPOS = {"B": "banca múltiple", "C": "caja municipal", "F": "financiera", "CR": "caja rural", "ED": "edpyme"}
DEPARTAMENTOS = ["Amazonas", "Ancash", "Apurimac", "Arequipa", "Ayacucho", "Cajamarca", "Callao", "Cusco",
                 "Huancavelica", "Huanuco", "Ica", "Junin", "La Libertad", "Lambayeque", "Lima", "Loreto",
                 "Madre de Dios", "Moquegua", "Pasco", "Piura", "Puno", "San Martin", "Tacna", "Tumbes", "Ucayali"]
SIN_TILDE = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")


def leer(path: Path) -> pd.DataFrame:
    # La SBS mezcla .xlsx y .xls antiguos con la misma extensión .XLS: se detecta por contenido.
    engine = "openpyxl" if path.read_bytes()[:2] == b"PK" else "xlrd"
    filas = []
    for hoja, df in pd.read_excel(path, sheet_name=None, header=None, engine=engine).items():
        norm = df.map(lambda v: str(v).strip().translate(SIN_TILDE) if pd.notna(v) else v)
        cabecera = norm.apply(lambda r: r.isin(DEPARTAMENTOS).sum(), axis=1)
        if cabecera.max() < 20:  # hoja sin columnas por departamento (p. ej. distritos de Lima)
            continue
        h = cabecera.idxmax()
        cols = {c: norm.at[h, c] for c in df.columns if norm.at[h, c] in DEPARTAMENTOS}
        fecha = next((pd.Timestamp(v) for v in df.iloc[:h, 0] if isinstance(v, dt.datetime)), pd.NaT)
        for _, r in df.iloc[h + 1:].iterrows():
            empresa = str(r[0]).strip()
            if empresa in ("", "nan") or empresa.upper().startswith("TOTAL"):
                continue
            for c, dep in cols.items():
                n = pd.to_numeric(r[c], errors="coerce")
                if pd.notna(n):
                    filas.append({"empresa": empresa, "departamento": dep, "oficinas": int(n), "fecha": fecha})
    out = pd.DataFrame(filas)
    prefijo = path.stem.split("-")[0].upper()
    out["tipo"] = TIPOS.get(prefijo, prefijo)
    return out


def main() -> int:
    files = sorted(p for p in RAW.glob("*") if p.suffix.lower() in (".xls", ".xlsx"))
    if not files:
        print(f"No hay archivos en {RAW.relative_to(ROOT)}")
        return 1
    df = pd.concat([leer(p) for p in files], ignore_index=True)
    df.to_csv(OUT / "oficinas_sbs_departamento.csv", index=False, encoding="utf-8-sig")
    fecha = df["fecha"].max()
    print(f"{len(files)} archivos · {df['empresa'].nunique()} empresas · corte {fecha.date() if pd.notna(fecha) else 's/f'}\n")
    for dep in ["La Libertad"]:
        d = df[(df["departamento"] == dep) & (df["oficinas"] > 0)].sort_values("oficinas", ascending=False)
        tot = d["oficinas"].sum()
        print(f"== {dep}: {tot} oficinas")
        for r in d.itertuples():
            print(f"  {r.empresa:<55} {r.tipo:<15} {r.oficinas:>3}  ({r.oficinas / tot:.0%})")
    print(f"\n-> {(OUT / 'oficinas_sbs_departamento.csv').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
