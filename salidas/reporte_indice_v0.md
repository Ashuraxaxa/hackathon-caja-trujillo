# Índice de oportunidad v0 — La Libertad

alpha (peso de VOLUMEN) = **0.6** · oferta financiera SBS: **pendiente** · 84 distritos

## Cómo se calcula

Cada variable se convierte a percentil dentro de La Libertad (0 a 1) y se pondera:

| lente | variable | peso dentro del lente |
|---|---|---:|
| volumen | adultos 18-64 (`pob_18_64`) | 50% |
| volumen | puestos de mercado (`puestos_mercado`) | 25% |
| volumen | empresas formales activas (`ruc_activos_habidos`) | 25% |
| intensidad | brecha de formalidad (pocas empresas por adulto) (`brecha_formal`) | 50% |
| intensidad | puestos de mercado por adulto (`puestos_x1000`) | 50% |

`score = 100 × (α·volumen + (1−α)·intensidad) × factor_oferta`

## Top 15

`estabilidad` = % de 1 000 simulaciones (pesos y α perturbados) en que el distrito sigue en el top-15.

| # | distrito | provincia | score | estabilidad | por qué |
|---:|---|---|---:|---:|---|
| 1 | TRUJILLO | TRUJILLO | 80.2 | 100% | + adultos 18-64 (p100); puestos de mercado (p100) | − brecha de formalidad (pocas empresas por adulto) (p1) |
| 2 | EL PORVENIR | TRUJILLO | 80.1 | 100% | + adultos 18-64 (p98); puestos de mercado (p98) | − brecha de formalidad (pocas empresas por adulto) (p18) |
| 3 | LA ESPERANZA | TRUJILLO | 80.1 | 100% | + adultos 18-64 (p99); puestos de mercado (p99) | − brecha de formalidad (pocas empresas por adulto) (p12) |
| 4 | VIRU | VIRU | 78.3 | 100% | + puestos de mercado (p95); adultos 18-64 (p92) | − brecha de formalidad (pocas empresas por adulto) (p26) |
| 5 | LAREDO | TRUJILLO | 77.0 | 100% | + puestos de mercado por adulto (p98); puestos de mercado (p93) | − brecha de formalidad (pocas empresas por adulto) (p21) |
| 6 | FLORENCIA DE MORA | TRUJILLO | 76.9 | 100% | + puestos de mercado (p94); adultos 18-64 (p93) | − brecha de formalidad (pocas empresas por adulto) (p20) |
| 7 | CHEPEN | CHEPEN | 75.9 | 100% | + puestos de mercado (p92); adultos 18-64 (p90) | − brecha de formalidad (pocas empresas por adulto) (p17) |
| 8 | PACASMAYO | PACASMAYO | 74.5 | 97% | + puestos de mercado por adulto (p99); puestos de mercado (p96) | − brecha de formalidad (pocas empresas por adulto) (p8) |
| 9 | HUANCHACO | TRUJILLO | 73.2 | 82% | + adultos 18-64 (p96); empresas formales activas (p96) | − brecha de formalidad (pocas empresas por adulto) (p5) |
| 10 | PAIJAN | ASCOPE | 72.8 | 94% | + puestos de mercado por adulto (p94); puestos de mercado (p87) | − brecha de formalidad (pocas empresas por adulto) (p23) |
| 11 | OTUZCO | OTUZCO | 72.5 | 94% | + adultos 18-64 (p82); puestos de mercado por adulto (p81) | − brecha de formalidad (pocas empresas por adulto) (p43) |
| 12 | CASA GRANDE | ASCOPE | 72.4 | 74% | + puestos de mercado por adulto (p82); adultos 18-64 (p81) | − brecha de formalidad (pocas empresas por adulto) (p42) |
| 13 | MOCHE | TRUJILLO | 72.0 | 78% | + empresas formales activas (p93); adultos 18-64 (p89) | − brecha de formalidad (pocas empresas por adulto) (p7) |
| 14 | SANTIAGO DE CAO | ASCOPE | 71.8 | 54% | + puestos de mercado por adulto (p95); puestos de mercado (p82) | − brecha de formalidad (pocas empresas por adulto) (p40) |
| 15 | CHAO | VIRU | 71.7 | 86% | + adultos 18-64 (p87); puestos de mercado (p85) | − brecha de formalidad (pocas empresas por adulto) (p24) |

## Auditoría de sesgo urbano/rural

| tercil de densidad | distritos | volumen | intensidad | final | en top-15 |
|---|---:|---:|---:|---:|---:|
| baja (rural) | 28.0 | 32.6 | 48.6 | 39.0 | 0.0 |
| media | 27.0 | 43.0 | 53.5 | 47.2 | 2.0 |
| alta (urbana) | 28.0 | 75.2 | 50.6 | 65.3 | 13.0 |

- Correlación de Spearman entre puntaje final y densidad: **+0.70**.
- Distritos rurales (tercil bajo) en el top-15: **0** de 15.
- ⚠ Con este alpha el top queda 100 % urbano: bajar alpha o agregar un cupo rural.

## Limitaciones (decirlas en el pitch)

- El padrón RUC reducido solo trae ubigeo para personas jurídicas (RUC 20); las personas naturales con negocio (RUC 10) casi nunca lo tienen. `ruc_activos_habidos` mide **empresas formales**, no microempresarios.
- CENAMA es de 2016; los puestos de mercado pueden haber cambiado.
- Sin datos SBS el índice no sabe dónde ya hay agencias/agentes: puede priorizar zonas ya atendidas.
- Es un índice de priorización territorial, no evalúa a personas ni su riesgo crediticio.
- Alto Trujillo (130112) no tiene polígono en el mapa base: aparece en el ranking pero no en el mapa.
