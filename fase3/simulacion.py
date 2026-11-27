"""Simulación: prospección convencional frente a prospección dirigida por el índice.

Uso:
    python fase3/simulacion.py                      # 10 asesores × 40 días, 1 000 corridas
    python fase3/simulacion.py --asesores 10 --dias 40 --corridas 1000

TODO LO QUE PRODUCE ESTE SCRIPT ES SIMULADO. No son resultados reales de Caja Trujillo.

Mundo sintético (por distrito, construido con datos públicos + supuestos):
  - Personas de 18-64 (RENIEC). Una visita encuentra a un adulto al azar del distrito.
  - Tiene negocio o chacra (prospecto objetivo): productores CENAGRO / adultos + una fracción urbana
    con negocio (supuesto θ_negocio, mayor donde hay más puestos de mercado por adulto).
  - Ya es cliente de la Caja: crece con las agencias propias por adulto y baja con la distancia (supuesto).
  - Atendido por la competencia: crece con las oficinas de la competencia relevadas por adulto, más una
    base mayor en distritos densos (banca no relevada).
  - No bancarizado: agro = 1 − productores con crédito / productores (CENAGRO); urbano = supuesto.
  - Efecto oculto por distrito (lognormal): el índice no lo ve. Evita que el índice se evalúe a sí mismo.

Resultados de una visita a un prospecto que no es cliente de la Caja:
  - Consentimiento para contacto comercial: θ_consentimiento.
  - Primer crédito con la Caja (KPI principal): θ_conversion × efecto oculto × (1 − θ_competencia si ya lo
    atiende otra entidad) × (1 + θ_mensaje si el asesor lleva el mensaje según la barrera de la zona).
  - Nuevo en el sistema financiero: si convierte y no estaba bancarizado.

Capacidad: jornada de 8 h, 30 min por visita. El viaje se descuenta: en distritos con agencia, 0,5 h;
sin agencia, ida y vuelta diaria (2 × ida) si la ida es ≤ 1,5 h, o jornada concentrada con pernocte
(2 × ida repartido en 5 días + 0,5 h) si es más. Ida = km en línea recta × 2,5 / 25 km/h.

Escenarios con la MISMA cantidad de asesores-día:
  - Convencional: barrido en los distritos donde la Caja ya tiene agencia, en proporción a la población.
  - Propuesta: top-N del índice; `cupo-agro` de los días a los distritos agro (por productores excluidos)
    y el resto a los urbanos (por adultos), con el mensaje según la barrera.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "salidas"
SINT = ROOT / "data" / "sintetico"

# Rangos de los supuestos (cada corrida toma un valor uniforme dentro del rango).
SUPUESTOS = {
    "negocio_urbano": (0.15, 0.30, "fracción de adultos urbanos con negocio propio"),
    "ct_max": (0.15, 0.35, "techo de penetración de la Caja donde tiene agencia"),
    "comp_max": (0.20, 0.45, "techo de clientes de la competencia relevada"),
    "comp_base_densa": (0.05, 0.20, "clientes de banca no relevada en distritos densos"),
    "no_bancarizado_urbano": (0.30, 0.60, "no bancarizados entre los negocios urbanos"),
    "consentimiento": (0.25, 0.45, "prospectos que dan consentimiento en la visita"),
    "conversion": (0.04, 0.10, "prospectos no clientes que toman su primer crédito con la Caja"),
    "efecto_competencia": (0.30, 0.60, "cuánto baja la conversión si ya lo atiende otra entidad"),
    "efecto_mensaje": (0.00, 0.30, "mejora de conversión por llevar el mensaje según la barrera"),
    "ruido_distrito": (0.20, 0.50, "desviación del efecto oculto por distrito (lognormal)"),
}
HORAS_DIA, HORAS_VISITA = 8.0, 0.5
FACTOR_CARRETERA, VEL_KMH, MAX_IDA_DIARIA_H = 2.5, 25, 1.5


def pct(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, method="average")


def cargar() -> pd.DataFrame:
    r = pd.read_csv(OUT / "ranking_v1.csv", dtype={"ubigeo": str}, encoding="utf-8-sig")
    b = pd.read_parquet(INTERIM / "base_distrital.parquet")[["ubigeo", "prod_obtuvieron_credito"]]
    d = r.merge(b, on="ubigeo", how="left")
    for c in ["productores", "prod_excluidos", "prod_obtuvieron_credito", "puestos_mercado",
              "oficinas_competencia", "agencias_ct", "km_agencia"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d["puestos_x1000"] = 1000 * d["puestos_mercado"] / d["pob_18_64"]
    d["ida_h"] = d["km_agencia"] * FACTOR_CARRETERA / VEL_KMH
    return d


def visitas_por_dia(d: pd.DataFrame) -> pd.Series:
    viaje = np.where(d["agencias_ct"] > 0, 0.5,
                     np.where(d["ida_h"] <= MAX_IDA_DIARIA_H, 2 * d["ida_h"], 2 * d["ida_h"] / 5 + 0.5))
    return pd.Series(np.maximum(2, (HORAS_DIA - viaje) / HORAS_VISITA), index=d.index), pd.Series(viaje, index=d.index)


def mundo(d: pd.DataFrame, th: dict, efecto: np.ndarray) -> pd.DataFrame:
    """Probabilidades del mundo sintético por distrito para una corrida."""
    w = pd.DataFrame(index=d.index)
    agro = np.minimum(0.9, d["productores"] / d["pob_18_64"])
    urbano = th["negocio_urbano"] * (0.75 + 0.5 * pct(d["puestos_x1000"]))
    w["p_objetivo"] = np.minimum(0.95, agro + (1 - agro) * urbano)
    w["sh_agro"] = agro / w["p_objetivo"]  # de los prospectos, qué parte es agro
    ag10k = 1e4 * d["agencias_ct"] / d["pob_18_64"]
    w["p_cliente_ct"] = np.where(d["agencias_ct"] > 0, th["ct_max"] * (1 - np.exp(-ag10k)),
                                 th["ct_max"] * 0.15 * np.exp(-d["km_agencia"] / 30))
    comp10k = 1e4 * d["oficinas_competencia"] / d["pob_18_64"]
    w["p_comp"] = np.minimum(0.9, th["comp_max"] * (1 - np.exp(-comp10k))
                             + th["comp_base_densa"] * pct(d["densidad_hab_km2"]))
    nb_agro = np.where(d["productores"] > 0, 1 - d["prod_obtuvieron_credito"] / d["productores"].clip(lower=1), 0.9)
    nb_urb = th["no_bancarizado_urbano"] * (1 - 0.5 * pct(d["densidad_hab_km2"]))
    w["p_no_bancarizado"] = w["sh_agro"] * nb_agro + (1 - w["sh_agro"]) * nb_urb
    w["efecto"] = efecto
    return w


def resultado(d: pd.DataFrame, w: pd.DataFrame, dias: pd.Series, th: dict, con_mensaje: bool) -> dict:
    vpd, viaje = visitas_por_dia(d)
    visitas = dias * vpd
    prospectos = visitas * w["p_objetivo"] * (1 - w["p_cliente_ct"])
    p_conv_libre = th["conversion"] * w["efecto"]
    p_conv_comp = p_conv_libre * (1 - th["efecto_competencia"])
    mensaje = 1 + (th["efecto_mensaje"] * w["sh_agro"] if con_mensaje else 0)
    # entre los prospectos, los atendidos por la competencia convierten menos
    conv_comp = prospectos * w["p_comp"] * p_conv_comp * mensaje
    conv_libre = prospectos * (1 - w["p_comp"]) * p_conv_libre * mensaje
    nuevos = (conv_comp + conv_libre).clip(upper=prospectos)
    # nuevos en el sistema: solo entre los no atendidos por nadie
    nuevos_sistema = conv_libre * np.minimum(1, w["p_no_bancarizado"] / (1 - w["p_comp"]).clip(lower=0.05))
    return {"asesor_dias": dias.sum(), "visitas": visitas.sum(), "prospectos": prospectos.sum(),
            "consentimientos": (prospectos * th["consentimiento"]).sum(), "nuevos_clientes": nuevos.sum(),
            "nuevos_en_sistema": nuevos_sistema.clip(upper=nuevos).sum(), "horas_viaje": (dias * viaje).sum()}


def asignar(d: pd.DataFrame, presupuesto: float, top: int, cupo_agro: float) -> dict[str, pd.Series]:
    conv = d["pob_18_64"].where(d["agencias_ct"] > 0, 0)
    conv = presupuesto * conv / conv.sum()
    sel = d["puesto"] <= top
    agro, urb = sel & (d["segmento"] == "agro"), sel & (d["segmento"] == "urbano")
    prop = pd.Series(0.0, index=d.index)
    prop[agro] = presupuesto * cupo_agro * d.loc[agro, "prod_excluidos"] / d.loc[agro, "prod_excluidos"].sum()
    prop[urb] = presupuesto * (1 - cupo_agro) * d.loc[urb, "pob_18_64"] / d.loc[urb, "pob_18_64"].sum()
    return {"convencional": conv, "propuesta": prop}


def mundo_sintetico_muestra(d: pd.DataFrame, th: dict, efecto: np.ndarray, n: int, seed: int) -> pd.DataFrame:
    """Guarda una muestra de prospectos sintéticos (NO son personas reales) para inspección y demo."""
    rng = np.random.default_rng(seed)
    w = mundo(d, th, efecto)
    filas = []
    for i, r in d.iterrows():
        k = n
        es_obj = rng.random(k) < w.at[i, "p_objetivo"]
        es_agro = es_obj & (rng.random(k) < w.at[i, "sh_agro"])
        filas.append(pd.DataFrame({
            "dato": "SINTETICO", "ubigeo": r["ubigeo"], "distrito": r["distrito"],
            "segmento": np.where(es_agro, "agro", np.where(es_obj, "urbano", "sin negocio")),
            "cliente_caja_trujillo": rng.random(k) < w.at[i, "p_cliente_ct"],
            "cliente_competencia": rng.random(k) < w.at[i, "p_comp"],
            "no_bancarizado": rng.random(k) < w.at[i, "p_no_bancarizado"],
        }))
    return pd.concat(filas, ignore_index=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asesores", type=int, default=10)
    ap.add_argument("--dias", type=int, default=40, help="días de campo por asesor (40 = 8 semanas)")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--cupo-agro", type=float, default=0.4)
    ap.add_argument("--corridas", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    d = cargar()
    rng = np.random.default_rng(args.seed)
    presupuesto = args.asesores * args.dias
    plan = asignar(d, presupuesto, args.top, args.cupo_agro)
    filas = []
    for k in range(args.corridas):
        th = {c: rng.uniform(lo, hi) for c, (lo, hi, _) in SUPUESTOS.items()}
        efecto = rng.lognormal(0, th["ruido_distrito"], len(d))
        w = mundo(d, th, efecto)
        for esc, con_msg in [("convencional", False), ("propuesta", True), ("propuesta_sin_mensaje", False)]:
            r = resultado(d, w, plan["propuesta" if esc.startswith("propuesta") else "convencional"], th, con_msg)
            filas.append({"corrida": k, "escenario": esc, **r})
    sim = pd.DataFrame(filas)
    sim.to_csv(OUT / "simulacion_corridas.csv", index=False, encoding="utf-8-sig")

    SINT.mkdir(parents=True, exist_ok=True)
    th_med = {c: (lo + hi) / 2 for c, (lo, hi, _) in SUPUESTOS.items()}
    muestra = mundo_sintetico_muestra(d, th_med, np.ones(len(d)), 200, args.seed)
    muestra.to_csv(SINT / "prospectos_sinteticos.csv", index=False, encoding="utf-8-sig")

    reporte(sim, d, plan, args, presupuesto)
    return 0


def q(s: pd.Series) -> str:
    return f"{s.median():,.0f} ({s.quantile(.1):,.0f}–{s.quantile(.9):,.0f})"


def reporte(sim: pd.DataFrame, d: pd.DataFrame, plan: dict, args, presupuesto: float) -> None:
    piv = sim.pivot(index="corrida", columns="escenario")
    met = [("visitas", "Visitas"), ("prospectos", "Prospectos objetivo (no clientes de la Caja)"),
           ("consentimientos", "Prospectos con consentimiento"),
           ("nuevos_clientes", "**Nuevos clientes con primer crédito en la Caja**"),
           ("nuevos_en_sistema", "…de ellos, nuevos en el sistema financiero"), ("horas_viaje", "Horas de viaje")]
    L = ["# Simulación: prospección convencional frente a la propuesta", "",
         "> **Resultados SIMULADOS con datos sintéticos.** No son resultados reales de Caja Trujillo. "
         "Sirven para comparar estrategias bajo supuestos explícitos.", "",
         f"Misma capacidad en ambos escenarios: **{args.asesores} asesores × {args.dias} días = {presupuesto:,} asesores-día** · "
         f"{args.corridas:,} corridas con supuestos variables · valores: mediana (P10–P90).", "",
         "| indicador | convencional | propuesta | diferencia mediana | corridas en que gana la propuesta |",
         "|---|---:|---:|---:|---:|"]
    for c, nombre in met:
        a, b = piv[(c, "convencional")], piv[(c, "propuesta")]
        dif = (b / a - 1).replace([np.inf, -np.inf], np.nan)
        gana = (b < a).mean() if c == "horas_viaje" else (b > a).mean()
        L.append(f"| {nombre} | {q(a)} | {q(b)} | {dif.median():+.0%} | {gana:.0%} |")
    nc_a, nc_b = piv[("nuevos_clientes", "convencional")], piv[("nuevos_clientes", "propuesta")]
    nc_s = piv[("nuevos_clientes", "propuesta_sin_mensaje")]
    L += ["", "## Lectura", "",
          f"- Nuevos clientes por 100 visitas: convencional **{(nc_a / piv[('visitas', 'convencional')] * 100).median():.1f}**, "
          f"propuesta **{(nc_b / piv[('visitas', 'propuesta')] * 100).median():.1f}**.",
          f"- Nuevos clientes por asesor-día: convencional **{(nc_a / presupuesto).median():.2f}**, "
          f"propuesta **{(nc_b / presupuesto).median():.2f}**.",
          f"- Sin el efecto del mensaje según la barrera, la propuesta logra **{(nc_s / nc_a - 1).median():+.0%}** "
          f"nuevos clientes frente a la convencional (gana en {(nc_s > nc_a).mean():.0%} de las corridas): "
          "la ventaja no depende solo de ese supuesto.",
          "", "## Dónde trabaja cada escenario (asesores-día)", "",
          "| distrito | segmento | agencia CT | convencional | propuesta |", "|---|---|---:|---:|---:|"]
    t = d.assign(conv=plan["convencional"], prop=plan["propuesta"])
    t = t[(t["conv"] > 0.5) | (t["prop"] > 0.5)].sort_values(["prop", "conv"], ascending=False)
    L += [f"| {r.distrito} | {r.segmento} | {int(r.agencias_ct)} | {r.conv:.0f} | {r.prop:.0f} |" for r in t.itertuples()]
    L += ["", "## Supuestos (rango que se varía en cada corrida)", "", "| supuesto | rango |", "|---|---|"]
    L += [f"| {txt} | {lo:.0%}–{hi:.0%} |" for lo, hi, txt in SUPUESTOS.values()]
    L += ["", "## Limitaciones", "",
          "- El mundo sintético se construye con los mismos datos públicos que usa el índice. Para no evaluarlo contra sí "
          "mismo se agrega un efecto oculto por distrito y se varían todos los supuestos; aun así, la simulación muestra "
          "consistencia bajo supuestos razonables, no una prueba de campo.",
          "- La competencia relevada cubre ~31 % de las oficinas; la banca no relevada se aproxima con la densidad.",
          "- Las tasas de consentimiento y conversión son supuestos, no datos de la Caja: el piloto debe medirlas.",
          "- Los prospectos sintéticos de `data/sintetico/prospectos_sinteticos.csv` no son personas reales.",
          "- Distancias en línea recta × 2,5; el tiempo real de viaje en sierra puede ser mayor."]
    (OUT / "simulacion_reporte.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:16]))
    print("\n-> salidas/simulacion_reporte.md, salidas/simulacion_corridas.csv, data/sintetico/prospectos_sinteticos.csv")


if __name__ == "__main__":
    sys.exit(main())
