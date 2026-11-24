# Índice de oportunidad v1 — La Libertad

alpha (peso de VOLUMEN) = **0.6** · cupo agro = **40%** · oferta financiera por distrito: **pendiente** · 84 distritos

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
| 1 | TRUJILLO | TRUJILLO | urbano | 80.2 | 100% | [urbano] + adultos 18-64 (p100); puestos de mercado (p100) | − brecha de formalidad (pocas empresas por adulto) (p1) |
| 2 | JULCAN | JULCAN | agro | 93.1 | 100% | [agro] + productores agro sin acceso a crédito (p95); pequeños productores (<5 ha) (p94) | − % de productores excluidos del crédito (p89) |
| 3 | EL PORVENIR | TRUJILLO | urbano | 80.2 | 100% | [urbano] + adultos 18-64 (p98); puestos de mercado (p98) | − brecha de formalidad (pocas empresas por adulto) (p18) |
| 4 | CHUGAY | SANCHEZ CARRION | agro | 92.0 | 100% | [agro] + productores agro sin acceso a crédito (p96); pequeños productores (<5 ha) (p96) | − productores agro excluidos por adulto (p83) |
| 5 | LA ESPERANZA | TRUJILLO | urbano | 80.1 | 100% | [urbano] + adultos 18-64 (p99); puestos de mercado (p99) | − brecha de formalidad (pocas empresas por adulto) (p12) |
| 6 | VIRU | VIRU | urbano | 78.3 | 100% | [urbano] + puestos de mercado (p95); adultos 18-64 (p92) | − brecha de formalidad (pocas empresas por adulto) (p26) |
| 7 | USQUIL | OTUZCO | agro | 90.3 | 100% | [agro] + productores agro sin acceso a crédito (p99); pequeños productores (<5 ha) (p99) | − % de productores excluidos del crédito (p73) |
| 8 | LAREDO | TRUJILLO | urbano | 77.1 | 100% | [urbano] + puestos de mercado por adulto (p98); puestos de mercado (p93) | − brecha de formalidad (pocas empresas por adulto) (p21) |
| 9 | OTUZCO | OTUZCO | agro | 89.6 | 94% | [agro] + productores agro sin acceso a crédito (p100); pequeños productores (<5 ha) (p98) | − productores agro excluidos por adulto (p74) |
| 10 | FLORENCIA DE MORA | TRUJILLO | urbano | 76.9 | 100% | [urbano] + puestos de mercado (p94); adultos 18-64 (p93) | − brecha de formalidad (pocas empresas por adulto) (p20) |
| 11 | CHEPEN | CHEPEN | urbano | 75.9 | 99% | [urbano] + puestos de mercado (p92); adultos 18-64 (p90) | − brecha de formalidad (pocas empresas por adulto) (p17) |
| 12 | SARTIMBAMBA | SANCHEZ CARRION | agro | 88.7 | 91% | [agro] + % de productores excluidos del crédito (p98); productores agro sin acceso a crédito (p94) | − productores agro excluidos por adulto (p77) |
| 13 | PACASMAYO | PACASMAYO | urbano | 74.4 | 69% | [urbano] + puestos de mercado por adulto (p99); puestos de mercado (p96) | − brecha de formalidad (pocas empresas por adulto) (p8) |
| 14 | SALPO | OTUZCO | agro | 87.0 | 79% | [agro] + productores agro excluidos por adulto (p99); productores agro sin acceso a crédito (p88) | − % de productores excluidos del crédito (p65) |
| 15 | HUANCHACO | TRUJILLO | urbano | 73.2 | 54% | [urbano] + adultos 18-64 (p96); empresas formales activas (p96) | − brecha de formalidad (pocas empresas por adulto) (p5) |

## Auditoría de sesgo urbano/rural

| tercil de densidad | distritos | volumen | intensidad | final | en top-15 |
|---|---:|---:|---:|---:|---:|
| baja (rural) | 28.0 | 48.6 | 64.0 | 54.4 | 0.0 |
| media | 27.0 | 67.4 | 69.7 | 67.3 | 2.0 |
| alta (urbana) | 28.0 | 84.2 | 57.0 | 73.2 | 13.0 |

- Correlación de Spearman entre puntaje final y densidad: **+0.52**.
- Distritos rurales (tercil bajo) en el top-15: **0** de 15.
- Distritos de segmento agro en el top-15: **6** de 15 (fijado por el cupo agro).
- ⚠ Ningún distrito del tercil de menor densidad entra al top-15: los más remotos quedan fuera aunque haya agro. Si importa llegar a ellos, bajar alpha o evaluar un canal distinto (agentes, agencia móvil).

## Limitaciones (decirlas en el pitch)

- El padrón RUC reducido solo trae ubigeo para personas jurídicas (RUC 20); las personas naturales con negocio (RUC 10) casi nunca lo tienen. `ruc_activos_habidos` mide **empresas formales**, no microempresarios.
- CENAMA es de 2016 y CENAGRO de 2012: la estructura es estable, pero los montos pueden haber cambiado.
- Sin oferta por distrito (la SBS solo publica oficinas por departamento) el índice no sabe dónde ya hay agencias/agentes: puede priorizar zonas ya atendidas.
- Es un índice de priorización territorial, no evalúa a personas ni su riesgo crediticio.
- Alto Trujillo (130112) no tiene polígono en el mapa base: aparece en el ranking pero no en el mapa.
