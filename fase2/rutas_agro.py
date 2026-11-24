"""Zonas dentro del distrito y rutas de asesores itinerantes para el segmento agro.

Uso:
    python fase2/rutas_agro.py                 # distritos agro del top-15 sin agencia propia
    python fase2/rutas_agro.py --semanas 8 --visitas-dia 12 --cobertura 0.25 --radio-km 5

Qué hace:
1. Toma los distritos agro prioritarios del ranking (salidas/ranking_v1.csv) que no tienen agencia de
   Caja Trujillo y los asigna a su agencia más cercana ("hub": Otuzco, Huamachuco, ...).
2. Agrega los productores del CENAGRO por hexágono H3 (res 7 ≈ 5 km²) usando el centroide de su sector
   censal (SEA). Prioridad del hexágono = productores excluidos del crédito.
3. Para cada hub arma CIRCUITOS: parte del hexágono pendiente más valioso y suma los hexágonos a menos de
   `radio-km`. Días de campo del circuito = excluidos × `cobertura` / `visitas-dia` (un asesor visita ~12
   productores al día). Orden de visita por vecino más cercano desde la agencia.
4. Modalidad según el viaje de ida: ≤ 1,5 h → salida diaria desde la agencia; más → base de campo
   (pernocte del asesor / agencia móvil semanal / agente). Los circuitos se calendarizan por semanas
   (5 días de campo por asesor) hasta completar `semanas`.
5. Sugiere el mensaje comercial según la barrera dominante del hexágono (CENAGRO P096/P092).

Supuestos (ajustables): en sierra la distancia por carretera ≈ 2,5 × la línea recta y la velocidad media
≈ 25 km/h.

Salidas en salidas/: zonas_agro.csv, rutas_asesores.csv, mapa_rutas_agro.html
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import h3
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
MANUAL = ROOT / "data" / "manual"
OUT = ROOT / "salidas"
sys.path.insert(0, str(ROOT / "fase1"))
from indice import centroides, leaflet  # noqa: E402

FACTOR_CARRETERA = 2.5
VEL_KMH = 25
DIAS_MAX_CIRCUITO = 5  # un circuito = como máximo una semana de campo
MAX_IDA_DIARIA_H = 1.5  # más que esto de ida y no conviene ir y volver en el día
MENSAJES = {
    "intereses": "Tasa competitiva y cuota fija: comparar con prestamista/habilitador",
    "garantia": "Crédito sin garantía real (grupal / con aval) para pequeño productor",
    "autoexclusion": "Educación financiera: 'sí califica', requisitos simples",
    "tramites": "Evaluación en campo y desembolso rápido (asesor lleva todo)",
    "sin_oferta": "Presencia: visita periódica fija y agente cercano",
    "deudas": "Reprogramación / compra de deuda",
    "rechazado": "Segunda oportunidad: evaluación por flujo de la chacra, no solo historial",
}


def km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    h = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(h))


def hubs(ranking: pd.DataFrame, geo: dict) -> dict[str, tuple[float, float]]:
    """Ubicación de cada agencia hub. La web de Caja Trujillo no da coordenadas: se usa el promedio de las
    oficinas de la competencia en ese distrito (están en la plaza/centro urbano) o, si no hay, el centroide."""
    comp = pd.read_csv(MANUAL / "oficinas_competencia.csv", dtype={"ubigeo": str}, encoding="utf-8-sig")
    comp = comp.dropna(subset=["lat", "lng"])
    cen = centroides(geo).set_index("ubigeo")
    nombre_a_ubigeo = dict(zip(ranking["distrito"], ranking["ubigeo"]))
    out = {}
    for hub in ranking["agencia_cercana"].dropna().unique():
        ub = nombre_a_ubigeo[hub]
        c = comp[comp["ubigeo"] == ub]
        out[hub] = (c["lat"].astype(float).mean(), c["lng"].astype(float).mean()) if len(c) else \
            (cen.at[ub, "lat"], cen.at[ub, "lon"])
    return out


def zonas(ua: pd.DataFrame, objetivo: pd.DataFrame, res: int) -> pd.DataFrame:
    ua = ua[ua["ubigeo"].isin(objetivo["ubigeo"])].copy()
    ua["hex"] = [h3.latlng_to_cell(la, lo, res) for la, lo in zip(ua["LAT_DECI"], ua["LONG_DECI"])]
    ua["barrera_x"] = ua["barrera"].where(ua["barrera"].notna(), np.where(ua["rechazado"], "rechazado", None))
    z = ua.groupby("hex").agg(
        ubigeo=("ubigeo", lambda s: s.mode().iat[0]), productores=("NPRIN", "size"),
        pequenos=("pequeno", "sum"), excluidos=("excluido", "sum"), con_credito=("obtuvo", "sum"),
        sectores=("P007X", "nunique"),
    ).reset_index()
    dom = (ua.dropna(subset=["barrera_x"]).groupby(["hex", "barrera_x"]).size().rename("n").reset_index()
             .sort_values("n", ascending=False).drop_duplicates("hex"))
    tot_b = ua.dropna(subset=["barrera_x"]).groupby("hex").size()
    z = z.merge(dom.rename(columns={"barrera_x": "barrera_principal"}), on="hex", how="left")
    z["pct_barrera"] = (z.pop("n") / z["hex"].map(tot_b)).round(2)
    z["mensaje_sugerido"] = z["barrera_principal"].map(MENSAJES)
    z[["lat", "lng"]] = [h3.cell_to_latlng(h) for h in z["hex"]]
    z = z.merge(objetivo[["ubigeo", "distrito", "agencia_cercana"]].rename(columns={"agencia_cercana": "hub"}),
                on="ubigeo", how="left")
    return z.sort_values("excluidos", ascending=False).reset_index(drop=True)


def planificar(z: pd.DataFrame, hub_xy: dict, semanas: int, visitas_dia: int, cobertura: float,
               radio_km: float, asesores: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (circuitos, visitas). `asesores` por hub, 5 días de campo por semana.
    Los circuitos se asignan en orden de prioridad al asesor que se libera primero."""
    circs, visitas = [], []
    for hub, g in z.groupby("hub"):
        hlat, hlng = hub_xy[hub]
        pend, dia_cal, n = g.copy(), 0, 0
        while len(pend):
            n += 1
            semilla = pend.iloc[0]
            d = km(semilla["lat"], semilla["lng"], pend["lat"].to_numpy(), pend["lng"].to_numpy())
            cerca = pend.assign(_d=d)[d <= radio_km].sort_values("_d")
            dias_acum = (cerca["excluidos"] * cobertura / visitas_dia).cumsum()
            grupo = cerca[(dias_acum.shift(fill_value=0) < DIAS_MAX_CIRCUITO)].drop(columns="_d")  # máx. 1 semana
            pend = pend.drop(grupo.index)
            exc = int(grupo["excluidos"].sum())
            dias = max(1, int(np.ceil(exc * cobertura / visitas_dia)))
            clat = np.average(grupo["lat"], weights=grupo["excluidos"].clip(lower=1))
            clng = np.average(grupo["lng"], weights=grupo["excluidos"].clip(lower=1))
            ida_h = float(km(hlat, hlng, clat, clng)) * FACTOR_CARRETERA / VEL_KMH
            modalidad = "salida diaria desde la agencia" if ida_h <= MAX_IDA_DIARIA_H else \
                "base de campo (pernocte / agencia móvil / agente)"
            ini = dia_cal + 1
            dia_cal += dias
            cid = f"{hub[:3]}-{n:02d}"
            circs.append({"hub": hub, "circuito": cid, "distritos": ", ".join(grupo["distrito"].unique()),
                          "hexagonos": len(grupo), "excluidos": exc, "visitas_meta": int(round(exc * cobertura)),
                          "dias_campo": dias, "dia_inicio": ini, "dia_fin": dia_cal,
                          "semana_inicio": (ini - 1) // 5 + 1, "semana_fin": (dia_cal - 1) // 5 + 1,
                          "ida_horas_est": round(ida_h, 1), "modalidad": modalidad,
                          "lat": round(clat, 5), "lng": round(clng, 5),
                          "asesor": None})
            pos, resto, k = (hlat, hlng), grupo.copy(), 0
            while len(resto):
                dd = km(pos[0], pos[1], resto["lat"].to_numpy(), resto["lng"].to_numpy())
                f = resto.iloc[int(dd.argmin())]
                k += 1
                visitas.append({"hub": hub, "circuito": cid, "orden": k, "hex": f["hex"], "distrito": f["distrito"],
                                "lat": round(f["lat"], 5), "lng": round(f["lng"], 5), "excluidos": int(f["excluidos"]),
                                "productores": int(f["productores"]), "mensaje_sugerido": f["mensaje_sugerido"]})
                pos = (f["lat"], f["lng"])
                resto = resto.drop(f.name)
    c = pd.DataFrame(circs)
    out = []
    for hub, g in c.groupby("hub", sort=False):
        n_ases = asesores
        libre = [0] * n_ases
        for idx, r in g.iterrows():
            a = int(np.argmin(libre))
            ini = libre[a] + 1
            libre[a] += r["dias_campo"]
            g.loc[idx, ["asesor", "dia_inicio", "dia_fin"]] = [f"{hub[:3]}-A{a + 1}", ini, libre[a]]
        g["semana_inicio"] = (g["dia_inicio"].astype(int) - 1) // 5 + 1
        g["semana_fin"] = (g["dia_fin"].astype(int) - 1) // 5 + 1
        g["dentro_horizonte"] = g["dia_fin"].astype(int) <= semanas * 5
        g["asesores_para_todo"] = max(1, int(np.ceil(g["dias_campo"].sum() / (semanas * 5))))
        out.append(g)
    return pd.concat(out, ignore_index=True), pd.DataFrame(visitas)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15, help="distritos agro dentro de este puesto del ranking")
    ap.add_argument("--semanas", type=int, default=8, help="horizonte del plan (un asesor por agencia hub)")
    ap.add_argument("--visitas-dia", type=int, default=12, help="productores que un asesor visita por día de campo")
    ap.add_argument("--cobertura", type=float, default=0.25, help="fracción de excluidos a visitar en cada circuito")
    ap.add_argument("--asesores", type=int, default=2, help="asesores itinerantes por agencia hub")
    ap.add_argument("--radio-km", type=float, default=5, help="radio para agrupar hexágonos en un circuito")
    ap.add_argument("--res", type=int, default=7, help="resolución H3 (7 ≈ 5 km², 8 ≈ 0,7 km²)")
    args = ap.parse_args()

    ranking = pd.read_csv(OUT / "ranking_v1.csv", dtype={"ubigeo": str}, encoding="utf-8-sig")
    objetivo = ranking[(ranking["segmento"] == "agro") & (ranking["puesto"] <= args.top) & (ranking["agencias_ct"] == 0)]
    if objetivo.empty:
        print("No hay distritos agro prioritarios sin agencia propia con estos parámetros.")
        return 1
    geo = json.loads((INTERIM / "limites_piloto.geojson").read_text(encoding="utf-8"))
    ua = pd.read_parquet(INTERIM / "cenagro_ua_piloto.parquet")
    z = zonas(ua, objetivo, args.res)
    hub_xy = hubs(ranking, geo)
    z["km_hub_recta"] = [round(float(km(la, lo, *hub_xy[h])), 1) for la, lo, h in zip(z["lat"], z["lng"], z["hub"])]
    circs, visitas = planificar(z, hub_xy, args.semanas, args.visitas_dia, args.cobertura, args.radio_km, args.asesores)
    z = z.merge(visitas[["hex", "circuito"]], on="hex", how="left")

    z.round(4).to_csv(OUT / "zonas_agro.csv", index=False, encoding="utf-8-sig")
    circs.to_csv(OUT / "circuitos_asesores.csv", index=False, encoding="utf-8-sig")
    visitas.to_csv(OUT / "rutas_asesores.csv", index=False, encoding="utf-8-sig")
    mapa(z, circs, visitas, hub_xy, geo, objetivo)

    print(f"Distritos objetivo: {', '.join(objetivo['distrito'])}")
    print(f"Hexágonos con productores: {len(z)} · excluidos totales: {int(z['excluidos'].sum()):,} · "
          f"supuestos: {args.visitas_dia} visitas/día, cobertura {args.cobertura:.0%}, radio {args.radio_km} km")
    resumen = []
    for hub, c in circs.groupby("hub"):
        d = c[c["dentro_horizonte"]]
        base = d["modalidad"] != "salida diaria desde la agencia"
        tot = c["excluidos"].sum()
        resumen.append({"hub": hub, "asesores": args.asesores, "semanas": args.semanas, "circuitos": len(d),
                        "excluidos_alcanzados": int(d["excluidos"].sum()), "excluidos_total": int(tot),
                        "pct_alcanzado": round(d["excluidos"].sum() / tot, 3), "visitas": int(d["visitas_meta"].sum()),
                        "dias_base_campo": int(d.loc[base, "dias_campo"].sum()), "dias_campo": int(d["dias_campo"].sum()),
                        "asesores_para_todo": int(c["asesores_para_todo"].iat[0])})
        r = resumen[-1]
        print(f"\n== Hub {hub} con {args.asesores} asesores · {args.semanas} semanas: {r['circuitos']} circuitos · "
              f"{r['excluidos_alcanzados']:,} de {tot:,} excluidos en las zonas visitadas ({r['pct_alcanzado']:.0%}) · "
              f"{r['visitas']:,} visitas · {r['dias_base_campo']} de {r['dias_campo']} días con base de campo · "
              f"para cubrir todo: {r['asesores_para_todo']} asesores")
        for x in d.itertuples():
            print(f"  {x.circuito} {x.asesor} sem {x.semana_inicio}-{x.semana_fin} · {x.distritos:<24} {x.hexagonos:>2} hex · "
                  f"{x.excluidos:>4} excl · {x.dias_campo} días · ida ~{x.ida_horas_est} h · {x.modalidad}")
    pd.DataFrame(resumen).to_csv(OUT / "resumen_asesores.csv", index=False, encoding="utf-8-sig")
    print("\n-> salidas/resumen_asesores.csv, salidas/zonas_agro.csv, salidas/circuitos_asesores.csv, salidas/rutas_asesores.csv, salidas/mapa_rutas_agro.html")
    return 0


def mapa(z, circs, visitas, hub_xy, geo, objetivo) -> None:
    hexes = [{"type": "Feature",
              "geometry": {"type": "Polygon", "coordinates": [[[lng, lat] for lat, lng in h3.cell_to_boundary(r.hex)]]},
              "properties": {"hex": r.hex, "distrito": r.distrito, "hub": r.hub, "excluidos": int(r.excluidos),
                             "productores": int(r.productores), "pequenos": int(r.pequenos),
                             "barrera": r.barrera_principal if isinstance(r.barrera_principal, str) else "",
                             "pct_barrera": float(r.pct_barrera) if pd.notna(r.pct_barrera) else 0,
                             "mensaje": r.mensaje_sugerido if isinstance(r.mensaje_sugerido, str) else "",
                             "circuito": r.circuito if isinstance(r.circuito, str) else ""}} for r in z.itertuples()]
    limites = [f for f in geo["features"] if f["properties"]["IDDIST"] in set(objetivo["ubigeo"])]
    circuitos = {}
    for c in circs.itertuples():
        v = visitas[visitas["circuito"] == c.circuito]
        h = hub_xy[c.hub]
        circuitos.setdefault(c.hub, []).append({
            "id": c.circuito, "distritos": c.distritos, "hex": int(c.hexagonos), "excluidos": int(c.excluidos),
            "visitas": int(c.visitas_meta), "dias": int(c.dias_campo), "sem": [int(c.semana_inicio), int(c.semana_fin)],
            "ida": float(c.ida_horas_est), "modalidad": c.modalidad, "asesor": c.asesor, "dentro": bool(c.dentro_horizonte),
            "puntos": [[float(h[0]), float(h[1])]] + v[["lat", "lng"]].values.tolist()})
    data = {"hex": {"type": "FeatureCollection", "features": hexes},
            "limites": {"type": "FeatureCollection", "features": limites},
            "hubs": {k: [float(v[0]), float(v[1])] for k, v in hub_xy.items() if k in circuitos}, "circ": circuitos}
    html = MAPA.replace("__LEAFLET__", leaflet()).replace("__DATA__", json.dumps(data, ensure_ascii=False))
    (OUT / "mapa_rutas_agro.html").write_text(html, encoding="utf-8")


MAPA = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rutas de asesores agro</title>
__LEAFLET__
<style>
  :root{--bg:#fff;--fg:#1d2330;--muted:#5b6475;--card:#f6f7f9;--line:#dde1e7;--acc:#2f6fde}
  @media (prefers-color-scheme:dark){:root{--bg:#14171d;--fg:#e8eaee;--muted:#9aa3b2;--card:#1d2129;--line:#2c323d;--acc:#6b9cff}}
  *{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
  .wrap{display:grid;grid-template-columns:1fr 380px;height:100vh}#map{height:100%}
  aside{overflow:auto;padding:16px;border-left:1px solid var(--line)}
  h1{font-size:17px;margin:0 0 4px}.sub{color:var(--muted);font-size:12px;margin-bottom:12px}
  select{width:100%;padding:6px;margin-bottom:10px;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;font:inherit}
  .day{padding:8px 10px;border:1px solid var(--line);border-radius:8px;margin-bottom:8px;cursor:pointer;background:var(--card)}
  .day.on{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc)}.day b{font-weight:600}.muted{color:var(--muted);font-size:12px}
  .warn{color:#c2410c;font-size:12px}
  .legend{background:var(--bg);color:var(--fg);padding:8px 10px;border-radius:6px;font-size:12px;box-shadow:0 1px 4px #0003}
  .legend i{display:inline-block;width:14px;height:10px;margin-right:4px}
  @media (max-width:800px){.wrap{grid-template-columns:1fr;grid-template-rows:55vh auto;height:auto}aside{border-left:0}}
</style></head><body>
<div class="wrap"><div id="map"></div><aside>
<h1>Rutas de asesores itinerantes · agro</h1>
<div class="sub">Hexágonos H3 con productores excluidos del crédito (CENAGRO). Cada circuito agrupa zonas cercanas; línea continua = salida diaria desde la agencia, punteada = requiere base de campo. Distancias en línea recta (por carretera ≈ 2,5×).</div>
<select id="hub"></select>
<div id="days"></div>
</aside></div>
<script>
const D = __DATA__;
const colors = ["#f1eef6","#d0d1e6","#a6bddb","#74a9cf","#2b8cbe","#045a8d"];
const vals = D.hex.features.map(f=>f.properties.excluidos).sort((a,b)=>a-b);
const br = [1,2,3,4,5].map(i=>vals[Math.floor(i*vals.length/6)]);
const col = x => colors[br.filter(b=>x>=b).length];
const map = L.map("map");
L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",{attribution:"© OpenStreetMap © CARTO",maxZoom:18}).addTo(map);
L.geoJSON(D.limites,{style:{fill:false,color:"#555",weight:1.2,dashArray:"4 3"}}).addTo(map);
const hexL = L.geoJSON(D.hex,{style:f=>({fillColor:col(f.properties.excluidos),weight:.5,color:"#666",fillOpacity:.75}),
  onEachFeature:(f,l)=>{const p=f.properties;l.bindPopup(`<b>${p.distrito}</b> · hub ${p.hub}<br>Productores: ${p.productores} (${p.pequenos} &lt;5 ha)<br>Excluidos del crédito: <b>${p.excluidos}</b><br>Barrera principal: ${p.barrera||"—"} ${p.barrera?`(${Math.round(p.pct_barrera*100)}%)`:""}<br><i>${p.mensaje||""}</i><br>${p.circuito?`Circuito ${p.circuito}`:""}`);}}).addTo(map);
map.fitBounds(hexL.getBounds());
const lg = L.control({position:"bottomleft"}); lg.onAdd=()=>{const d=L.DomUtil.create("div","legend");
  d.innerHTML="<b>Excluidos por hexágono</b><br>"+colors.map((c,i)=>`<i style="background:${c}"></i>${i?"≥ "+br[i-1]:"menos"}`).join("<br>");return d;}; lg.addTo(map);
for (const [h,xy] of Object.entries(D.hubs)) L.circleMarker(xy,{radius:8,color:"#fff",weight:2,fillColor:"#1d4ed8",fillOpacity:1}).addTo(map).bindTooltip("Agencia "+h,{permanent:true,direction:"top",offset:[0,-6]});
const sel = document.getElementById("hub");
sel.innerHTML = Object.keys(D.circ).map(h=>`<option>${h}</option>`).join("");
let routeL = L.layerGroup().addTo(map);
function show(hub, id){
  routeL.clearLayers();
  const cs = D.circ[hub].filter(c=>c.dentro);
  document.getElementById("days").innerHTML = cs.map(c=>`<div class="day ${c.id===id?"on":""}" data-c="${c.id}">
    <b>${c.id}</b> · ${c.asesor} · semana ${c.sem[0]}${c.sem[1]>c.sem[0]?"–"+c.sem[1]:""} · ${c.distritos}
    <div class="muted">${c.hex} ${c.hex===1?"zona":"zonas"} · ${c.excluidos} excluidos · meta ${c.visitas} visitas · ${c.dias} días de campo · ida ~${c.ida} h</div>
    <div class="${c.modalidad.startsWith("salida")?"muted":"warn"}">${c.modalidad}</div></div>`).join("");
  cs.filter(c=>!id||c.id===id).forEach(c=>{
    L.polyline(c.puntos,{color:"#c2410c",weight:id?3:1.5,opacity:id?.95:.45,dashArray:c.modalidad.startsWith("salida")?null:"6 5"}).addTo(routeL);
    if(id) c.puntos.slice(1).forEach((p,i)=>L.circleMarker(p,{radius:9,color:"#c2410c",fillColor:"#fff",fillOpacity:1,weight:2})
      .bindTooltip(String(i+1),{permanent:true,direction:"center"}).addTo(routeL));
  });
  hexL.setStyle(f=>({weight: id && f.properties.circuito===id ? 2.5 : .5, color: id && f.properties.circuito===id ? "#c2410c" : "#666"}));
}
sel.onchange = ()=>show(sel.value, null);
document.getElementById("days").onclick = e=>{const d=e.target.closest(".day"); if(d) show(sel.value, d.dataset.c);};
show(sel.value, null);
</script></body></html>
"""

if __name__ == "__main__":
    sys.exit(main())
