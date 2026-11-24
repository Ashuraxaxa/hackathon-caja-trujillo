# Hackathon Caja Trujillo — Fase 0: datos públicos

```bash
pip install -r requirements.txt
python fase0/download.py     # ~1,3 GB, reanuda si se corta; escribe data/raw/manifest.json
python fase0/validate.py     # ~2 min; escribe data/interim/ + reporte_fase0.md
```

El ámbito piloto se define en `fase0/sources.py` (`DEPARTAMENTOS_PILOTO = ["13"]`, La Libertad).

## Fuentes

| fuente | modo | qué aporta | nivel |
|---|---|---|---|
| SUNAT padrón RUC | auto | negocios formales activos y habidos, dirección | distrito (dirección → Fase 2) |
| RENIEC población con DNI | auto | población por sexo y edad (actualizada, mejor que el censo 2017) | distrito |
| CENAMA 2016 | auto | mercados de abastos y puestos | distrito |
| CENAGRO 2012 (INEI) | auto | productores agro, acceso a crédito y barreras (~760 MB) | distrito + centroide SEA |
| Límites distritales | auto | polígonos para mapa y H3 | distrito |
| OpenStreetMap (Geofabrik) | opcional | bancos, ATMs, agentes, comercios con coordenadas | punto |
| SBS oficinas por zona geográfica | **manual** (antibot) | oficinas por entidad (contexto competitivo) | departamento |

La fuente manual (SBS) se descarga desde el navegador y se deja en `data/raw/sbs/`; `validate.py` detecta si está.
La tipología de distritos de la PCM se descartó porque ya no se puede descargar; la ruralidad se aproxima con densidad y CENAGRO.

## Salidas (`data/interim/`)

- `base_distrital.parquet|csv`: una fila por distrito con población, RUC activos, mercados y densidad de RUC.
- `ruc_piloto.parquet`: contribuyentes del ámbito con dirección (insumo para geocodificar).
- `limites_piloto.geojson`, `poblacion_por_distrito`, `ruc_por_distrito`, `mercados_por_distrito`.
- `reporte_fase0.md`: chequeos de calidad, hashes de las fuentes y notas.

# Fase 1 — Índice de oportunidad por distrito (v1)

```bash
python fase1/indice.py                               # alpha=0.6, cupo agro 40 %
python fase1/indice.py --alpha 0.3 --cupo-agro 0.5   # más inclusión, más agro
```

Salidas en `salidas/`: `ranking_v1.csv` (abre en Excel), `reporte_indice_v1.md` (método, top, auditoría de sesgo,
limitaciones) y `mapa_indice_v1.html` (se abre con doble clic y funciona sin internet, salvo el mapa de fondo).

**Cómo funciona**

- Cada distrito se evalúa en dos **segmentos** y se queda con el más fuerte:
  - **urbano**: adultos de 18-64, puestos de mercado, empresas formales y brecha de formalidad (SUNAT, RENIEC, CENAMA).
  - **agro**: pequeños productores y productores sin acceso a crédito (CENAGRO 2012).
- Dentro de cada segmento hay dos lentes: **volumen** (cuántos) e **intensidad** (qué tan grande es la brecha por
  habitante). `alpha` es el peso del volumen.
- Comparar un distrito urbano con uno agro es una decisión de cartera, no algo que decidan los datos. Por eso la lista
  final intercala los rankings de ambos segmentos según `--cupo-agro`.
- **Competencia por distrito**: `python fase0/competencia.py` lee las redes de agencias publicadas por Mibanco,
  Efectiva, Caja Arequipa, Caja Del Santa y Caja Paita (37 de las 121 oficinas de la competencia en La Libertad; las
  cifras por entidad cuadran con la SBS) y escribe `data/manual/oficinas_competencia.csv`. Filas agregadas a mano con
  `fuente = manual` (p. ej. Compartamos, Caja Huancayo) se conservan. El índice penaliza hasta un 30 % a los distritos
  con más oficinas de la competencia por adulto; sin competencia, no hay penalidad. `python fase0/sbs.py` resume las
  oficinas por entidad a nivel departamento (contexto competitivo).
- **Presencia de Caja Trujillo**: `data/manual/agencias_caja_trujillo.csv` (24 agencias de La Libertad tomadas de la web
  de la Caja, con distrito asignado por dirección; las marcadas "verificar" conviene confirmarlas). El reporte lista
  los **espacios en blanco** (distritos prioritarios sin agencia propia) y la agencia más cercana en línea recta.
- La estabilidad se mide con 1 000 simulaciones que mueven los pesos y alpha. La auditoría compara los resultados
  por tercil de densidad.

Agenda para la sesión con el owner: [`docs/agenda_owner.md`](docs/agenda_owner.md).
