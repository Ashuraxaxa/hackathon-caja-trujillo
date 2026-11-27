# Simulación: prospección convencional frente a la propuesta

> **Resultados SIMULADOS con datos sintéticos.** No son resultados reales de Caja Trujillo. Sirven para comparar estrategias bajo supuestos explícitos.

Misma capacidad en ambos escenarios: **10 asesores × 40 días = 400 asesores-día** · 1,000 corridas con supuestos variables · valores: mediana (P10–P90).

| indicador | convencional | propuesta | diferencia mediana | corridas en que gana la propuesta |
|---|---:|---:|---:|---:|
| Visitas | 6,000 (6,000–6,000) | 5,570 (5,570–5,570) | -7% | 0% |
| Prospectos objetivo (no clientes de la Caja) | 1,661 (1,262–2,047) | 2,065 (1,761–2,365) | +24% | 100% |
| Prospectos con consentimiento | 572 (408–792) | 728 (542–933) | +24% | 100% |
| **Nuevos clientes con primer crédito en la Caja** | 106 (67–157) | 152 (97–218) | +43% | 100% |
| …de ellos, nuevos en el sistema financiero | 39 (24–57) | 98 (63–138) | +150% | 100% |
| Horas de viaje | 200 (200–200) | 415 (415–415) | +107% | 0% |

## Lectura

- Nuevos clientes por 100 visitas: convencional **1.8**, propuesta **2.7**.
- Nuevos clientes por asesor-día: convencional **0.26**, propuesta **0.38**.
- Sin el efecto del mensaje según la barrera, la propuesta logra **+33%** nuevos clientes frente a la convencional (gana en 99% de las corridas): la ventaja no depende solo de ese supuesto.

## Dónde trabaja cada escenario (asesores-día)

| distrito | segmento | agencia CT | convencional | propuesta |
|---|---|---:|---:|---:|
| TRUJILLO | urbano | 9 | 119 | 107 |
| LA ESPERANZA | urbano | 2 | 60 | 54 |
| USQUIL | agro | 0 | 0 | 42 |
| CHUGAY | agro | 0 | 0 | 34 |
| JULCAN | agro | 0 | 0 | 27 |
| SARTIMBAMBA | agro | 0 | 0 | 23 |
| FLORENCIA DE MORA | urbano | 0 | 0 | 20 |
| AGALLPAMPA | agro | 0 | 0 | 18 |
| SALPO | agro | 0 | 0 | 17 |
| MOCHE | urbano | 0 | 0 | 13 |
| LAREDO | urbano | 1 | 14 | 12 |
| CHAO | urbano | 0 | 0 | 12 |
| CASA GRANDE | urbano | 0 | 0 | 8 |
| PAIJAN | urbano | 0 | 0 | 8 |
| SANTIAGO DE CAO | urbano | 0 | 0 | 6 |
| EL PORVENIR | urbano | 1 | 49 | 0 |
| HUANCHACO | urbano | 1 | 26 | 0 |
| VICTOR LARCO HERRERA | urbano | 1 | 26 | 0 |
| HUAMACHUCO | agro | 1 | 23 | 0 |
| VIRU | urbano | 1 | 21 | 0 |
| CHEPEN | urbano | 1 | 18 | 0 |
| PACASMAYO | urbano | 1 | 10 | 0 |
| ALTO TRUJILLO | urbano | 1 | 10 | 0 |
| OTUZCO | agro | 1 | 10 | 0 |
| SANTIAGO DE CHUCO | agro | 1 | 7 | 0 |
| TAYABAMBA | agro | 1 | 5 | 0 |
| CHOCOPE | urbano | 1 | 4 | 0 |

## Supuestos (rango que se varía en cada corrida)

| supuesto | rango |
|---|---|
| fracción de adultos urbanos con negocio propio | 15%–30% |
| techo de penetración de la Caja donde tiene agencia | 15%–35% |
| techo de clientes de la competencia relevada | 20%–45% |
| clientes de banca no relevada en distritos densos | 5%–20% |
| no bancarizados entre los negocios urbanos | 30%–60% |
| prospectos que dan consentimiento en la visita | 25%–45% |
| prospectos no clientes que toman su primer crédito con la Caja | 4%–10% |
| cuánto baja la conversión si ya lo atiende otra entidad | 30%–60% |
| mejora de conversión por llevar el mensaje según la barrera | 0%–30% |
| desviación del efecto oculto por distrito (lognormal) | 20%–50% |

## Limitaciones

- El mundo sintético se construye con los mismos datos públicos que usa el índice. Para no evaluarlo contra sí mismo se agrega un efecto oculto por distrito y se varían todos los supuestos; aun así, la simulación muestra consistencia bajo supuestos razonables, no una prueba de campo.
- La competencia relevada cubre ~31 % de las oficinas; la banca no relevada se aproxima con la densidad.
- Las tasas de consentimiento y conversión son supuestos, no datos de la Caja: el piloto debe medirlas.
- Los prospectos sintéticos de `data/sintetico/prospectos_sinteticos.csv` no son personas reales.
- Distancias en línea recta × 2,5; el tiempo real de viaje en sierra puede ser mayor.
