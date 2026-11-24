# Reporte Fase 0 — calidad de datos públicos

Ámbito piloto: departamentos 13  ·  84 distritos  ·  sin fallas bloqueantes

## Fuentes descargadas

| fuente | bytes | sha256 (12) | fecha |
|---|---:|---|---|
| sunat_ruc | 395,550,127 | `faa05df253ea` | 2026-11-24T18:51:35 |
| reniec_poblacion | 144,296,957 | `ea1d300da3c6` | 2026-11-24T18:53:07 |
| cenama_mercados | 323,939 | `8dc418779a1d` | 2026-11-24T18:52:11 |
| cenama_diccionario | 1,863 | `0a195767f194` | 2026-11-24T18:52:12 |
| limites_distritales | 1,871,306 | `1eba0da33464` | 2026-11-24T18:50:57 |
| cenagro | 762,514,301 | `122a8a822823` | 2026-11-24T21:11:26 |

## Chequeos

| fuente | chequeo | resultado |
|---|---|---|
| limites | features > 1800 | ✅ 1834 distritos en el país |
| limites | distritos en ámbito piloto | ✅ 83 distritos |
| limites | todas las geometrías presentes | ✅ 0 sin geometría |
| sunat | zip íntegro | ✅  |
| sunat | esquema de 15 columnas | ✅ RUC | NOMBRE O RAZÓN SOCIAL | ESTADO DEL CONTRIBUYENTE | CONDICIÓN DE DOMICILIO | UBIGEO ... |
| sunat | filas totales > 10 M | ✅ 18,547,287 contribuyentes |
| sunat | % sin ubigeo | ✅ 85.2% sin ubigeo (no geolocalizables) |
| sunat | RUC de 11 dígitos | ✅  |
| sunat | RUC únicos | ✅ 0 duplicados |
| sunat | contribuyentes en ámbito piloto | ✅ 142,546 (31% activos y habidos, 98% con dirección) |
| sunat | ubigeos casan con polígonos | ✅ 1 ubigeos sin polígono: ['130112'] |
| reniec | columnas esperadas | ✅ [] |
| reniec | población nacional plausible (30-40 M) | ✅ 35,843,232 |
| reniec | edades válidas | ✅ 0 sin edad |
| reniec | población del ámbito piloto | ✅ 2,171,202 personas, 1,322,606 de 18-64 años |
| reniec | ubigeos casan con polígonos | ✅ 1 sin polígono: ['130112'] |
| cenama | filas > 2 000 | ✅ 2,612 mercados |
| cenama | mercados en ámbito piloto | ✅ 160 mercados, 17,705 puestos funcionando |
| cenagro | unidades agropecuarias en ámbito piloto | ✅ 130,181 UA |
| cenagro | módulo de crédito presente | ✅ 127,279 registros |
| cenagro | UA con respuesta de crédito | ✅ 97.8% |
| cenagro | coordenadas válidas (centroide SEA) | ✅ 100.0% |
| cenagro | productores con crédito (ámbito) | ✅ 5.4% obtuvieron; 55.4% excluidos (barrera o rechazo) |
| cenagro | ubigeos casan con polígonos | ✅ 0 sin polígono: [] |
| osm_peru | presente | ✅ ⚠ pendiente (optional): https://download.geofabrik.de/south-america/peru-latest.osm.pbf |
| sbs_oficinas | presente | ✅ ⚠ pendiente (manual): Abrir la URL en el navegador > Estadísticas por departamento/distrito > 'Número de oficinas' y 'Puntos de atención' (último mes). Guardar los Excel en data/raw/sbs/. |
| pcm_tipologia | presente | ✅ ⚠ pendiente (manual): El archivo está en Google Drive: abrir el dataset, botón 'Ir al recurso', descargar y guardar en data/raw/pcm/. |
| base | todos los distritos tienen población | ✅ 0 sin dato RENIEC |
| base | todos los distritos tienen RUC | ✅ 0 sin contribuyentes |

## Notas

- Los límites (juaneladio/peru-geojson) tienen 1 834 distritos; hoy existen ~1 890. Los distritos creados después no tienen polígono: se reportan abajo como 'sin polígono'.
- Padrón RUC: estados 'BAJA' y 'NUM. INTERNO IDENTIF' no son negocios operando; para señales de actividad usar solo activo_habido. No trae actividad económica (CIIU) ni coordenadas: la geolocalización fina requiere geocodificar la dirección (Fase 2).
- CENAMA es de 2016 y no trae coordenadas: sirve a nivel distrito, no hexágono.
- CENAGRO es de 2012: refleja la estructura agraria (estable) más que la oferta financiera actual. 'Excluido' = no pidió crédito por una barrera (trámites, intereses, falta de oferta o de garantía, deudas, creer que no se lo darían) o lo pidió y se lo negaron. Las coordenadas son del centroide del sector de empadronamiento (SEA), no de la chacra.

## Vista rápida: 15 distritos más poblados (18-64)

| ubigeo | pob 18-64 | RUC activos | RUC/1000 adultos | mercados |
|---|---:|---:|---:|---:|
| 130101 | 244,978 | 20,984 | 85.7 | 42 |
| 130105 | 124,230 | 3,182 | 25.6 | 19 |
| 130102 | 101,260 | 2,101 | 20.7 | 11 |
| 130104 | 53,278 | 2,259 | 42.4 | 8 |
| 130111 | 52,797 | 3,452 | 65.4 | 7 |
| 130901 | 46,722 | 1,799 | 38.5 | 2 |
| 130103 | 44,827 | 915 | 20.4 | 3 |
| 131201 | 43,123 | 703 | 16.3 | 4 |
| 130401 | 36,074 | 812 | 22.5 | 4 |
| 130107 | 29,395 | 973 | 33.1 | 4 |
| 130106 | 28,282 | 567 | 20.0 | 2 |
| 131202 | 28,121 | 463 | 16.5 | 3 |
| 130702 | 26,353 | 616 | 23.4 | 2 |
| 130704 | 21,126 | 694 | 32.9 | 4 |
| 130112 | 20,255 | 306 | 15.1 | 0 |
