# Sesión con el owner del reto — Caja Trujillo

**Duración:** 30 min · **Asisten:** owner del reto + líder del equipo + responsable de datos
**Objetivo:** salir con 6 decisiones tomadas para no construir algo que no se va a usar.
**Llevar:** `salidas/mapa_indice_v1.html` abierto en la laptop y `salidas/ranking_v1.csv`.

---

## 1. Contexto y demo (5 min)

- El reto, en una frase: *"dónde y con quién debería salir a captar la Caja mañana, y por qué"*.
- Mostrar el mapa del índice v1: los 83 distritos de La Libertad con datos públicos (SUNAT, RENIEC, CENAMA, CENAGRO).
- Dato de apertura (CENAGRO, La Libertad): de **130 mil productores agro, solo el 5,4 % obtuvo crédito** y el **55 %
  quedó excluido** (no lo pidió por intereses, falta de garantía, trámites o por creer que no se lo darían; o se lo
  negaron). **Un tercio de los créditos que sí se otorgaron vino de cajas municipales**: el canal ya existe, falta escala.
- **Competencia mapeada desde sus webs**: Mibanco, Efectiva y las cajas Arequipa, Del Santa y Paita (37 oficinas;
  las cifras cuadran con la SBS). En La Libertad hay 145 oficinas: Caja Trujillo lidera con 24, pero **las otras cajas
  municipales ya suman 33**.
- **Zonas prioritarias sin agencia de Caja Trujillo**: 6 de 15 si no se descuenta la competencia; **12 de 15** si se
  descuenta. En ambos casos aparecen 5 zonas agro de la sierra (Julcán, Usquil y Salpo, a 20-30 km de la agencia de
  Otuzco; Chugay y Sartimbamba, a 28-38 km de la de Huamachuco) y Florencia de Mora (45 mil adultos, sin la Caja ni
  competidores). Con descuento entran zonas urbanas medianas sin nadie: Paiján, Casa Grande, Moche, Chao.
  Pregunta clave: ¿se cubren con asesores itinerantes desde la agencia más cercana, con agentes o con agencia móvil?
- Explicar los dos segmentos (urbano y agro) y mostrar en vivo cómo cambia la lista al mover α y el cupo agro.
- Dejar claro lo que **no** es: no califica personas, no es scoring de crédito, no usa datos personales.

## 2. Seis decisiones clave (20 min, ~3 min cada una)

Para cada pregunta: qué hacemos según lo que responda. **Anotar la respuesta textual.**

### P1. ¿Qué decisión concreta debe apoyar la herramienta?
| Si responde… | Entonces… |
|---|---|
| "Dónde abrir agencia u oficina" | Horizonte de 3-5 años, peso alto al volumen, modelo de canibalización entre agencias. |
| "A qué zonas mandar a los asesores esta semana" | Bajamos a hexágonos H3 y rutas diarias; el entregable estrella es la app del asesor. |
| "Dónde poner agentes o corresponsales" | Peso alto a intensidad y ruralidad; el cruce con la competencia es crítico (hoy no tenemos agentes corresponsales). |

### P2. ¿Quién la usa todos los días?
- Analista o asesor de negocios → vista móvil, lista de zonas y rutas.
- Jefe de agencia → tablero de su zona con metas.
- Gerencia comercial → mapa regional y comparación entre agencias.
*Si dice "todos", pedir que elija **uno** para el demo.*

### P3. ¿Cómo reparte la cartera entre comercio urbano y agro? (cupo agro y α)
- **Cupo agro:** qué fracción de las zonas priorizadas va al pequeño productor agro. Hoy está en 40 %.
  Los datos no deciden esto: depende del apetito de riesgo agro de la Caja y de los productos que tiene.
- **α:** dentro de cada segmento, ¿prioriza dónde hay más gente (volumen) o dónde la brecha es mayor (intensidad)?
  Mostrar el top-15 con α = 0,6 frente a α = 0,3.
- **Competencia:** ¿la presencia de Mibanco, Efectiva u otras cajas en un distrito es una señal de **saturación**
  (restar puntos) o de **demanda comprobada** (no restar)? Mostrar el ranking con `--penalidad-competencia 0.3`
  frente a `0`. Esto cambia mucho la lista: El Porvenir, Virú y Chepén bajan; Paiján, Casa Grande y Moche suben.
- Advertencia de la auditoría: con α = 0,6 **ningún distrito del tercio más remoto** entra al top-15, ni siquiera
  por agro. Si quiere llegar ahí, probablemente le convenga otro canal (agentes, agencia móvil) en lugar de asesores.

### P4. ¿Podemos usar datos internos, aunque sean agregados o anonimizados?
| Si dice… | Entonces… |
|---|---|
| Sí: clientes por distrito o agencia, y prospecciones históricas | Look-alike con PU-learning y validación espacial: "zonas parecidas a donde ya nos va bien". |
| Solo agregados (por ejemplo, colocaciones por agencia) | Calibramos los pesos del índice contra el desempeño real de las agencias. |
| No | Pesos expertos (los validamos hoy) + datos sintéticos claramente rotulados para el demo. |

### P5. ¿Cómo se ve el éxito a los 3 meses de usarla?
Pedir **una** métrica: clientes nuevos por asesor, tasa de conversión de la prospección, % de clientes nuevos sin crédito previo (bancarizados por primera vez) o costo de captación.
Esa métrica define el backtest y el slide de impacto del pitch.

### P6. ¿Cómo nos va a evaluar el jurado?
- ¿Pesa más la solución técnica, el impacto o la viabilidad de implementarla?
- ¿Esperan un prototipo funcionando o basta un concepto bien sustentado?
- ¿Hay restricciones de stack o de nube (por ejemplo, Azure o on-premise)?

## 3. Validación rápida del ranking (3 min)

Preguntar sobre 3 distritos concretos del top:
- **El Porvenir / La Esperanza:** ¿la Caja ya está saturada ahí o hay espacio? (Esto prueba si nos falta el dato de oferta).
- **Virú:** sale como urbano (mercados y adultos). ¿Lo ven así o como zona agroexportadora?
- **Julcán / Chugay / Usquil (agro, sierra):** son los primeros del segmento agro. ¿La Caja tiene presencia o
  producto agro ahí? ¿Qué le impide crecer?

*Si el owner dice "esto ya lo sabíamos", preguntar: "¿qué distrito le sorprendería ver arriba?". Esa respuesta define la prueba de "lo no obvio".*

## 4. Pedidos y cierre (2 min)

- [ ] Confirmar el distrito de las 5 agencias marcadas "verificar" en `data/manual/agencias_caja_trujillo.csv` (las tomamos de la web).
- [ ] ¿Tienen a la mano los datos SBS de puntos de atención por distrito, o los bajamos nosotros?
- [ ] Nombre de un **jefe de agencia** que podamos entrevistar 15 minutos para validar la vista móvil.
- [ ] Canal de contacto para dudas durante el hackathón.

---

## Plantilla de decisiones (llenar durante la reunión)

| # | Decisión | Respuesta del owner | Impacto en el plan |
|---|---|---|---|
| P1 | Decisión objetivo | | |
| P2 | Usuario principal | | |
| P3 | α / cupo rural | | |
| P4 | Datos internos | | |
| P5 | Métrica de éxito | | |
| P6 | Criterios del jurado | | |
| — | Geografía piloto (¿solo La Libertad?) | | |
