# Índice de oportunidad v1 — La Libertad

alpha (peso de VOLUMEN) = **0.6** · cupo agro = **40%** · competencia relevada: **Banco Efectiva, CMAC Arequipa, CMAC Del Santa, CMAC Paita, Mibanco** · 84 distritos

## Cómo se calcula

Cada variable se convierte a percentil dentro de La Libertad (0 a 1) y se pondera:

| segmento · lente | variable | peso dentro del lente |
|---|---|---:|
| urbano · volumen | adultos 18-64 (`pob_18_64`) | 55% |
| urbano · volumen | puestos de mercado (`puestos_mercado`) | 25% |
| urbano · volumen | empresas formales activas (`ruc_activos_habidos`) | 20% |
| urbano · intensidad | brecha de formalidad (pocas empresas por adulto) (`brecha_formal`) | 50% |
| urbano · intensidad | puestos de mercado por adulto (`puestos_x1000`) | 50% |
| agro · volumen | productores agro sin acceso a crédito (`prod_excluidos`) | 70% |
| agro · volumen | pequeños productores (<5 ha) (`productores_pequenos`) | 30% |
| agro · intensidad | productores agro excluidos por adulto (`agro_excl_x1000`) | 60% |
| agro · intensidad | % de productores excluidos del crédito (`tasa_exclusion_agro_robusta`) | 40% |

`score_seg = α·volumen_seg + (1−α)·intensidad_seg` · `score = 100 × max(score_urbano, score_agro) × factor_oferta`

Cada distrito compite con su segmento más fuerte: un distrito urbano no pierde puntos por no tener agro, ni uno andino por no tener mercados.

La lista combinada intercala el ranking de cada segmento: 40% de los puestos para agro y 60% para urbano. Ese reparto es una decisión de cartera del owner, no un resultado del modelo.

| segmento dominante | distritos | productores excluidos | adultos 18-64 |
|---|---:|---:|---:|
| agro | 51 | 63,621 | 307,442 |
| urbano | 33 | 8,526 | 1,015,164 |

## Top 15

`estabilidad` = % de 1 000 simulaciones (pesos y α perturbados) en que el distrito sigue en el top-15.

| # | distrito | provincia | segmento | score | estabilidad | por qué |
|---:|---|---|---|---:|---:|---|
| 1 | LA ESPERANZA | TRUJILLO | urbano | 78.1 | 100% | [urbano] + adultos 18-64 (p99); puestos de mercado (p99) | − brecha de formalidad (pocas empresas por adulto) (p12) |
| 2 | JULCAN | JULCAN | agro | 93.1 | 100% | [agro] + productores agro sin acceso a crédito (p95); pequeños productores (<5 ha) (p94) | − % de productores excluidos del crédito (p89) |
| 3 | LAREDO | TRUJILLO | urbano | 77.1 | 100% | [urbano] + puestos de mercado por adulto (p98); puestos de mercado (p93) | − brecha de formalidad (pocas empresas por adulto) (p21) |
| 4 | CHUGAY | SANCHEZ CARRION | agro | 92.0 | 100% | [agro] + productores agro sin acceso a crédito (p96); pequeños productores (<5 ha) (p96) | − productores agro excluidos por adulto (p83) |
| 5 | FLORENCIA DE MORA | TRUJILLO | urbano | 76.9 | 100% | [urbano] + puestos de mercado (p94); adultos 18-64 (p93) | − brecha de formalidad (pocas empresas por adulto) (p20) |
| 6 | PAIJAN | ASCOPE | urbano | 72.7 | 99% | [urbano] + puestos de mercado por adulto (p94); puestos de mercado (p87) | − brecha de formalidad (pocas empresas por adulto) (p23) |
| 7 | USQUIL | OTUZCO | agro | 90.3 | 100% | [agro] + productores agro sin acceso a crédito (p99); pequeños productores (<5 ha) (p99) | − % de productores excluidos del crédito (p73) |
| 8 | CASA GRANDE | ASCOPE | urbano | 72.5 | 86% | [urbano] + puestos de mercado por adulto (p82); adultos 18-64 (p81) | − brecha de formalidad (pocas empresas por adulto) (p42) |
| 9 | SARTIMBAMBA | SANCHEZ CARRION | agro | 88.7 | 99% | [agro] + % de productores excluidos del crédito (p98); productores agro sin acceso a crédito (p94) | − productores agro excluidos por adulto (p77) |
| 10 | TRUJILLO | TRUJILLO | urbano | 72.2 | 84% | [urbano] + adultos 18-64 (p100); puestos de mercado (p100) | − brecha de formalidad (pocas empresas por adulto) (p1) |
| 11 | MOCHE | TRUJILLO | urbano | 71.9 | 81% | [urbano] + empresas formales activas (p93); adultos 18-64 (p89) | − brecha de formalidad (pocas empresas por adulto) (p7) |
| 12 | SALPO | OTUZCO | agro | 87.0 | 95% | [agro] + productores agro excluidos por adulto (p99); productores agro sin acceso a crédito (p88) | − % de productores excluidos del crédito (p65) |
| 13 | SANTIAGO DE CAO | ASCOPE | urbano | 71.9 | 67% | [urbano] + puestos de mercado por adulto (p95); puestos de mercado (p82) | − brecha de formalidad (pocas empresas por adulto) (p40) |
| 14 | AGALLPAMPA | OTUZCO | agro | 85.8 | 61% | [agro] + pequeños productores (<5 ha) (p90); productores agro excluidos por adulto (p90) | − % de productores excluidos del crédito (p64) |
| 15 | CHAO | VIRU | urbano | 71.7 | 88% | [urbano] + adultos 18-64 (p87); puestos de mercado (p85) | − brecha de formalidad (pocas empresas por adulto) (p24) |

## Espacios en blanco: prioridades sin agencia de Caja Trujillo

De los 15 primeros, **12** no tienen agencia propia (fuente: web de Caja Trujillo). Son candidatos a otro canal (asesores itinerantes, agentes, agencia móvil) o a apertura; en los que sí tienen agencia, la acción es prospección desde la agencia existente.

`agencia más cercana`: distrito con agencia propia más cercano en línea recta (en sierra, por carretera puede ser 2-3 veces más).

| # | distrito | segmento | agencias CT | agencia más cercana | km (recta) | adultos 18-64 | productores excluidos |
|---:|---|---|---:|---|---:|---:|---:|
| 1 | LA ESPERANZA | urbano | 2 | — | — | 124,230 | 0 |
| 2 | JULCAN | agro | 0 | OTUZCO | 28 | 8,596 | 2,868 |
| 3 | LAREDO | urbano | 1 | — | — | 28,282 | 614 |
| 4 | CHUGAY | agro | 0 | HUAMACHUCO | 28 | 12,925 | 3,609 |
| 5 | FLORENCIA DE MORA | urbano | 0 | LA ESPERANZA | 2 | 44,827 | 0 |
| 6 | PAIJAN | urbano | 0 | CHOCOPE | 11 | 17,977 | 356 |
| 7 | USQUIL | agro | 0 | OTUZCO | 24 | 17,035 | 4,490 |
| 8 | CASA GRANDE | urbano | 0 | CHOCOPE | 21 | 18,886 | 86 |
| 9 | SARTIMBAMBA | agro | 0 | HUAMACHUCO | 38 | 9,785 | 2,429 |
| 10 | TRUJILLO | urbano | 9 | — | — | 244,978 | 28 |
| 11 | MOCHE | urbano | 0 | VICTOR LARCO HERRERA | 5 | 29,395 | 408 |
| 12 | SALPO | agro | 0 | OTUZCO | 21 | 3,790 | 1,784 |
| 13 | SANTIAGO DE CAO | urbano | 0 | CHOCOPE | 16 | 12,671 | 149 |
| 14 | AGALLPAMPA | agro | 0 | OTUZCO | 18 | 5,814 | 1,886 |
| 15 | CHAO | urbano | 0 | VIRU | 34 | 28,121 | 701 |

## Auditoría de sesgo urbano/rural

| tercil de densidad | distritos | volumen | intensidad | final | en top-15 |
|---|---:|---:|---:|---:|---:|
| baja (rural) | 28.0 | 48.6 | 64.0 | 53.9 | 0.0 |
| media | 27.0 | 67.4 | 69.7 | 67.3 | 5.0 |
| alta (urbana) | 28.0 | 84.2 | 57.0 | 68.5 | 10.0 |

- Correlación de Spearman entre puntaje final y densidad: **+0.41**.
- Distritos rurales (tercil bajo) en el top-15: **0** de 15.
- Distritos de segmento agro en el top-15: **6** de 15 (fijado por el cupo agro).
- ⚠ Ningún distrito del tercil de menor densidad entra al top-15: los más remotos quedan fuera aunque haya agro. Si importa llegar a ellos, bajar alpha o evaluar un canal distinto (agentes, agencia móvil).

## Limitaciones (decirlas en el pitch)

- El padrón RUC reducido solo trae ubigeo para personas jurídicas (RUC 20); las personas naturales con negocio (RUC 10) casi nunca lo tienen. `ruc_activos_habidos` mide **empresas formales**, no microempresarios.
- CENAMA es de 2016 y CENAGRO de 2012: la estructura es estable, pero los montos pueden haber cambiado.
- La competencia por distrito cubre solo las entidades que publican su red (Mibanco, Efectiva, cajas Arequipa, Del Santa y Paita: ~31 % de las oficinas de la competencia). Falta Compartamos, cajas Huancayo, Piura y Cusco, y la banca tradicional (concentrada en Trujillo metropolitano). No incluye agentes corresponsales.
- Es un índice de priorización territorial, no evalúa a personas ni su riesgo crediticio.
- Alto Trujillo (130112) no tiene polígono en el mapa base: aparece en el ranking pero no en el mapa.
