"""Catálogo de fuentes públicas para la Fase 0.

mode:
  auto     -> download.py la descarga sola.
  manual   -> el sitio bloquea bots (Incapsula / Google Drive); alguien del equipo
              la baja en el navegador y la deja en `dest`. validate.py verifica que esté.
  optional -> se intenta; si falla no bloquea el pipeline.
"""

DATA_PORTAL = "https://www.datosabiertos.gob.pe/sites/default/files"

SOURCES = {
    "sunat_ruc": {
        "desc": "Padrón reducido RUC (SUNAT) - contribuyentes con ubigeo y dirección",
        "url": "https://www2.sunat.gob.pe/padron_reducido_ruc.zip",
        "dest": "sunat/padron_reducido_ruc.zip",
        "mode": "auto",
        "min_bytes": 300_000_000,
        "refresh": "diaria (SUNAT la regenera cada madrugada)",
    },
    "reniec_poblacion": {
        "desc": "Población identificada con DNI por distrito, sexo y edad (RENIEC)",
        "url": f"{DATA_PORTAL}/Poblacion_Identificada_RENIEC.csv",
        "dest": "reniec/Poblacion_Identificada_RENIEC.csv",
        "mode": "auto",
        "min_bytes": 50_000_000,
        "refresh": "trimestral",
    },
    "cenama_mercados": {
        "desc": "Censo Nacional de Mercados de Abastos 2016 (PRODUCE/INEI)",
        "url": f"{DATA_PORTAL}/dat_cenamav3.csv",
        "dest": "cenama/dat_cenamav3.csv",
        "mode": "auto",
        "min_bytes": 100_000,
        "refresh": "estática (2016)",
    },
    "cenama_diccionario": {
        "desc": "Diccionario de variables CENAMA",
        "url": f"{DATA_PORTAL}/Diccionario_CENAMA.csv",
        "dest": "cenama/Diccionario_CENAMA.csv",
        "mode": "auto",
        "min_bytes": 500,
        "refresh": "estática",
    },
    "cenagro": {
        "desc": "Censo Nacional Agropecuario 2012 (INEI) - productores agropecuarios con coordenadas",
        "url": "https://www.inei.gob.pe/media/DATOS_ABIERTOS/CENAGRO/DATA_NEW/2012.zip",
        "dest": "cenagro/2012.zip",
        "mode": "auto",
        "min_bytes": 500_000_000,
        "refresh": "estática (2012; el próximo CENAGRO aún no publica microdatos)",
    },
    "limites_distritales": {
        "desc": "Polígonos distritales INEI (GeoJSON simplificado)",
        "url": "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_distrital_simple.geojson",
        "dest": "limites/peru_distrital_simple.geojson",
        "mode": "auto",
        "min_bytes": 1_000_000,
        "refresh": "estática",
    },
    "osm_peru": {
        "desc": "OpenStreetMap Perú (PBF) - bancos, ATMs, agentes, mercados, comercios",
        "url": "https://download.geofabrik.de/south-america/peru-latest.osm.pbf",
        "dest": "osm/peru-latest.osm.pbf",
        "mode": "optional",
        "min_bytes": 100_000_000,
        "refresh": "diaria",
    },
    "sbs_oficinas": {
        "desc": "SBS - Número de oficinas / cajeros / agentes por distrito (Excel)",
        "url": "https://www.sbs.gob.pe/estadisticas-y-publicaciones/estadisticas-/sistema-financiero",
        "dest": "sbs/",  # cualquier .xls/.xlsx dentro de esta carpeta
        "mode": "manual",
        "min_bytes": 10_000,
        "refresh": "mensual",
        "how": "Abrir la URL en el navegador > Estadísticas por departamento/distrito > "
               "'Número de oficinas' y 'Puntos de atención' (último mes). Guardar los "
               "Excel en data/raw/sbs/.",
    },
}

# Descartada: PCM "Tipología de distritos" (los archivos en Google Drive ya no están disponibles).
# La ruralidad se aproxima con densidad (RENIEC / área) y el segmento agro con CENAGRO.

# Departamento piloto: La Libertad (ubigeo INEI 13). Cambiar aquí si el owner amplía alcance.
DEPARTAMENTOS_PILOTO = ["13"]
