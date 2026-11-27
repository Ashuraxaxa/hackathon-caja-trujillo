# Concept solution — respuestas del formulario

> Cifras de este documento: las de contexto salen de fuentes públicas (SBS, INEI-CENAGRO, RENIEC, SUNAT); las de impacto
> salen de nuestra **simulación con datos sintéticos** y así se indica. Nada de lo simulado se presenta como resultado real.

---

## Nombre de la solución *

**RadarCT — dónde captar mañana, y por qué**

*(Alternativas: "Ruta Inclusiva", "MapaCapta".)*

---

## ¿En qué consiste su solución y cómo aborda la problemática del desafío? *

RadarCT es una herramienta de priorización territorial que le dice a Caja Trujillo **dónde y en qué segmentos concentrar la prospección** para captar clientes nuevos, y convierte esa priorización en **rutas semanales y mensajes concretos para el asesor de negocios**.

Está dirigida a dos usuarios: el **asesor de negocios** (usuario principal), que recibe su circuito de la semana, las zonas a visitar y el mensaje sugerido para cada una; y la **gestión comercial**, que ve el mapa de oportunidades de la región, ajusta las prioridades y compara resultados.

Aborda tres partes del problema:
1. **Identificar oportunidades poco exploradas** cruzando seis fuentes públicas por distrito y por zonas de ~5 km²: población adulta (RENIEC), empresas formales (SUNAT), mercados (PRODUCE), productores agro y su acceso al crédito (INEI-CENAGRO), oficinas de la competencia (SBS y webs públicas) y la red de agencias de la Caja.
2. **Priorizar por segmento** (comercio urbano y pequeño productor agro) sin que uno castigue al otro, con decisiones de negocio explícitas: peso entre volumen y brecha, cupo de zonas agro y cuánto resta la presencia de la competencia.
3. **Traducir el hallazgo en acción**: circuitos de visita, capacidad necesaria de asesores y el mensaje según la barrera dominante de cada zona (falta de garantía, intereses altos, autoexclusión, etc.).

Responde a lo identificado en la inmersión: el KPI es el cliente nuevo para la Caja con su primera operación crediticia, el usuario es el asesor y la decisión es dónde y en qué segmentos prospectar. En La Libertad, por ejemplo, el 55 % de 130 mil productores agro quedó excluido del crédito (CENAGRO) y, de las 15 zonas que RadarCT prioriza, entre 6 y 12 no tienen agencia de la Caja, según cuánto se descuente la presencia de la competencia.

---

## ¿Cómo funcionaría su solución? *

1. **Recibe información pública** (descarga y validación automática): padrón RUC, población RENIEC, censos CENAGRO y CENAMA, límites distritales, oficinas por entidad (SBS) y redes de agencias publicadas por la Caja y sus competidores. Puede incorporar datos internos agregados si la Caja los comparte.
2. **Procesa**: arma una tabla base por distrito y una grilla de hexágonos H3 (~5 km²) con los productores excluidos y su barrera principal; calcula un índice de oportunidad por segmento, su estabilidad (1 000 simulaciones de pesos) y una auditoría de sesgo urbano/rural.
3. **Gestión comercial interactúa**: ve el mapa y el ranking, mueve las perillas de negocio (volumen frente a brecha, cupo agro, peso de la competencia) y ve las zonas prioritarias sin agencia propia y la agencia más cercana.
4. **Genera planes para el asesor**: circuitos de hasta una semana con orden de visita, horas de viaje estimadas, modalidad (salida diaria o jornada concentrada con pernocte) y el mensaje sugerido por zona; calcula cuántos asesores hacen falta para cubrir la meta.
5. **El asesor ejecuta y registra** desde el celular: visita, consentimiento para contacto comercial y resultado (prospecto, solicitud, primer crédito).
6. **Aprende**: los resultados de campo recalibran la prioridad de cada zona y se comparan con la prospección convencional en un tablero de KPI.

Resultados que genera: ranking explicado por distrito, mapa de zonas, circuitos por asesor, estimación de capacidad, mensajes por zona y comparación de KPI frente al método convencional.

---

## ¿Qué diferencia su solución de otras alternativas existentes? *

- **De dónde ya estamos a dónde no estamos.** La prospección convencional barre alrededor de las agencias existentes. RadarCT encuentra **espacios en blanco**: zonas con demanda y sin agencia de la Caja ni competencia relevada.
- **Mide la exclusión, no la supone.** Usa la pregunta del censo agropecuario sobre crédito (si lo pidió, si se lo dieron y por qué no) para ubicar a 72 mil productores excluidos y su barrera, zona por zona.
- **Segmentos que no se castigan entre sí.** Un distrito urbano no pierde puntos por no tener agro ni uno andino por no tener mercados; el reparto entre segmentos es una decisión de cartera visible, no un efecto oculto del modelo.
- **Del mapa a la ruta.** No se queda en un tablero: entrega circuitos, horas de viaje, número de asesores y el mensaje a usar.
- **Explicable y auditado.** Cada zona dice por qué sube o baja, qué tan estable es su puesto y si el índice margina a los distritos más remotos.
- **Sin datos personales ni scoring de crédito.** Prioriza territorios con datos públicos agregados; los prospectos se registran solo con consentimiento.
- **Escalable.** Todo se regenera con cuatro comandos y cambia de región con un parámetro.

---

## Material visual complementario (opcional)

Adjuntar:
- `docs/concept_flujo.png` — flujo de funcionamiento y arquitectura.
- `salidas/mapa_preview.png` — mapa del índice por distrito (gestión comercial).
- `salidas/mapa_rutas_preview.png` — zonas H3 y circuito del asesor.

## Enlace complementario (opcional)

Deck del pitch: https://claude.ai/artifact/6NPSY7hvFMwpPjXTDE8VTR — **antes de enviarlo, compartirlo desde el menú Share** para que los evaluadores puedan abrirlo.

---

## ¿Qué impacto generaría su solución y cómo contribuiría al resultado esperado del desafío? *

**KPI del desafío: clientes nuevos para Caja Trujillo con su primera operación crediticia.**

En una **simulación con datos sintéticos** de La Libertad (10 asesores × 8 semanas en ambos escenarios, 1 000 corridas con supuestos variables), dirigir la prospección con RadarCT frente al barrido convencional alrededor de las agencias logra, en la mediana:
- **+43 % de clientes nuevos con primer crédito** (152 frente a 106; 0,38 frente a 0,26 por asesor-día). Gana en el 100 % de las corridas; sin el efecto del mensaje por barrera, +33 % (gana en el 99 %).
- **+150 % de personas que entran por primera vez al sistema financiero** (98 frente a 39): inclusión, no solo captación.
- **+24 % de prospectos con consentimiento** (728 frente a 572) para futuras acciones comerciales.
- Costo: el doble de horas de viaje (415 frente a 200), por ir a zonas sin agencia; RadarCT lo muestra y lo planifica.

Supuestos (rangos variados en cada corrida): consentimiento 25–45 % de los prospectos; conversión a primer crédito 4–10 %; la competencia reduce la conversión 30–60 %; 20–30 % de adultos urbanos con negocio; jornada de 8 h con 30 min por visita; carretera ≈ 2,5 × la línea recta a 25 km/h. Son supuestos, no datos de la Caja: el piloto los mide.

Otros beneficios: el asesor recibe su semana planificada y el mensaje para cada zona; la gestión comercial dimensiona cuántos asesores necesita (por ejemplo, en 8 semanas 2 asesores desde Huamachuco llegan a zonas que concentran el 53 % de los productores excluidos de su área, y 3 asesores al 82 %); y la Caja gana visibilidad de la competencia (las otras cajas municipales ya tienen 33 oficinas en La Libertad, frente a 24 de Caja Trujillo).

---

## ¿Cuál será el enfoque tecnológico de su solución? *

- **Datos y modelos (Python):** pandas y pyarrow (procesamiento), h3 (grilla hexagonal), numpy (índice, estabilidad Monte Carlo, simulación), pypdf (lectura de documentos públicos). Índice por percentiles con pesos explícitos: interpretable y auditable, sin caja negra.
- **Backend:** API en Python (FastAPI) que expone ranking, zonas, circuitos y registro de visitas; base de datos SQLite para el prototipo (PostgreSQL/PostGIS en producción).
- **Frontend:** web responsiva para el asesor (celular) y para la gestión comercial (escritorio), con Leaflet para mapas y fondos Esri.
- **IA generativa (opcional, Claude o similar):** redactar el guion de visita a partir del segmento y la barrera de la zona, nunca con datos personales.
- **Por qué este enfoque:** todo funciona con datos públicos que podemos obtener solos, corre en una laptop, se explica a negocio y se integra después con los sistemas de la Caja por API.

Licencias y condiciones de uso de terceros: Leaflet (BSD-2), H3 (Apache 2.0), pandas, numpy y FastAPI (BSD/MIT); tipografías de Google Fonts (OFL); fondos de mapa Esri (uso con atribución; producción requiere cuenta ArcGIS); datos de OpenStreetMap (ODbL, con atribución); datos abiertos del Estado peruano (INEI, RENIEC, PRODUCE, SBS, SUNAT) con cita de fuente; las webs de agencias de entidades financieras se leen solo en sus páginas y documentos públicos. Los modelos de IA, si se usan, bajo los términos comerciales del proveedor y sin enviar datos personales.

---

## ¿Cuál será el punto de partida para construir su solución? *

**Desarrollo a partir de soluciones o componentes preexistentes (propios).**

Ya desarrollamos, antes del hackathon:
- Pipeline de descarga y validación de 7 fuentes públicas (scripts de Python con reporte de calidad).
- Índice de oportunidad por segmento con perillas de negocio, estabilidad y auditoría de sesgo; mapa interactivo (HTML).
- Relevamiento de agencias de la Caja y de 5 competidores desde sus webs públicas.
- Zonas H3 del segmento agro, circuitos de asesores y cálculo de capacidad; mapa de rutas.
- Simulación de prospección convencional frente a la propuesta con datos sintéticos.

Durante el hackathon construiremos la capa de producto encima de estos componentes (ver "¿Qué construirán?").

---

## ¿Identifican alguna limitación o riesgo técnico relevante?

| Limitación o riesgo | Cómo lo abordamos |
|---|---|
| CENAGRO es de 2012 | La estructura agraria es estable; se reemplaza por el próximo censo o por datos internos agregados de la Caja. |
| El padrón RUC público solo ubica empresas, no microempresarios | Se complementa con mercados y población; la geocodificación de direcciones queda para una etapa posterior. |
| La competencia relevada cubre ~31 % de las oficinas (algunas webs bloquean la lectura) | Se completa a mano o con datos SBS más finos; la penalidad por competencia es un parámetro ajustable. |
| Tasas de consentimiento y conversión son supuestos | Se varían en la simulación y el piloto las mide; el ciclo de aprendizaje las recalibra. |
| Distancias en línea recta | Factor de carretera explícito; en producción, rutas por red vial (OSRM u otro motor). |
| Conectividad en sierra para la app del asesor | Plan de la semana descargable y registro sin conexión que sincroniza al volver. |
| Protección de datos personales (Ley 29733) | Solo datos agregados; los prospectos se registran con consentimiento explícito y finalidad declarada. |

---

## ¿Qué construirán durante el hackathon? *

1. **App del asesor (web móvil) — funcionalidad crítica.** "Mi semana": circuito asignado, zonas en el mapa, orden de visita, mensaje sugerido por zona y registro de visita (consentimiento sí/no, resultado). Funciona con prospectos sintéticos.
2. **Panel de gestión comercial.** Mapa y ranking con las perillas en vivo (α, cupo agro, peso de la competencia), zonas sin agencia y asignación de circuitos a asesores.
3. **API** que une el pipeline existente con ambas vistas (ranking, zonas, circuitos, visitas).
4. **Ciclo de aprendizaje.** Los resultados de las visitas registradas actualizan la prioridad de las zonas.
5. **Tablero de KPI:** clientes nuevos con primer crédito, consentimientos y nuevos en el sistema, frente al escenario convencional.

**Funcionalidad crítica que debe quedar operativa:** que un asesor abra su semana con las zonas priorizadas y el mensaje de cada una, registre una visita, y que ese registro se vea en el tablero de la gestión comercial.

---

## ¿Qué resultado funcional esperan demostrar al finalizar el hackathon? *

**Caso de uso: "el lunes del asesor de Huamachuco".**
1. La gestión comercial abre el panel, fija el cupo agro y ve que Chugay y Sartimbamba son zonas prioritarias sin agencia, a ~2 h de Huamachuco.
2. Asigna el circuito de la semana a un asesor; el sistema indica jornada concentrada, zonas, orden de visita y el mensaje dominante ("crédito sin garantía real: grupal o con aval").
3. El asesor abre su semana en el celular, registra visitas a prospectos sintéticos con consentimiento y un primer crédito.
4. El tablero se actualiza y la prioridad de la zona se recalibra.
5. Cerramos con la simulación: mismo número de asesores, convencional frente a RadarCT, mostrando clientes nuevos con primer crédito, consentimientos y nuevos en el sistema, con sus supuestos.

**Verificación:** el flujo completo funciona de punta a punta con datos sintéticos rotulados; los KPI del tablero cuadran con los registros; la simulación es reproducible (semilla fija) y su reporte declara fuentes, supuestos y limitaciones.

---

## ¿Qué funcionalidades o capacidades quedarán fuera del alcance del prototipo?

- Integración con el core bancario, el CRM o los sistemas de originación de la Caja.
- Evaluación o scoring de crédito de personas (fuera del propósito de la solución).
- Geocodificación de direcciones del padrón RUC para el segmento urbano a nivel de zona.
- Rutas por red vial real y optimización avanzada de rutas.
- Campañas automáticas por WhatsApp u otros canales.
- Despliegue en todas las regiones (el prototipo es La Libertad; el pipeline admite otras con un parámetro).
- Calibración con datos internos históricos de la Caja.

---

## ¿Qué tipo de requerimiento de datos e insumos tiene su propuesta? *

Marcar **"No requerimos datos ni insumos"** y **"Requerimiento deseable de datos e insumos"**.

- **Autónomo:** construimos y validamos el prototipo con fuentes públicas y datos sintéticos generados por nosotros.
- **Deseable (enriquece y valida mejor, no es indispensable):** clientes nuevos o colocaciones agregadas por distrito o agencia; tasas históricas de conversión de la prospección; coordenadas de las agencias de la Caja; y cualquier dato agregado de prospección de los asesores. Siempre agregado y sin datos personales.

---

## ¿Cómo contribuirían estos datos e insumos a mejorar su solución? *

Todos los datos que pedimos son **agregados y anonimizados**, sin nombres ni documentos de identidad, y en cualquier formato tabular (Excel o CSV). Si la Caja no puede compartirlos, el prototipo funciona igual con fuentes públicas y datos sintéticos.

| Dato e insumo | Características | Para qué lo usaríamos | Qué mejora |
|---|---|---|---|
| **Clientes nuevos con primer crédito por distrito** | Conteo mensual de los últimos 12–24 meses, por distrito y segmento (urbano/agro o tipo de crédito) | Calibrar los pesos del índice: comparar las zonas que el índice prioriza con donde la Caja realmente captó | Pasa de pesos expertos a pesos ajustados con evidencia; permite medir el acierto del índice en zonas ya conocidas |
| **Tasas de la prospección** | Por agencia o distrito: visitas, prospectos con consentimiento, solicitudes y créditos desembolsados | Reemplazar los supuestos de la simulación (consentimiento 25–45 %, conversión 4–10 %) por valores observados | La estimación de impacto deja de depender de rangos supuestos y se acota |
| **Coordenadas y cobertura de las agencias** | Latitud y longitud de las 24 agencias de La Libertad y el área que atiende cada una (distritos o caseríos) | Ubicar con precisión el punto de salida de los asesores y confirmar el distrito de 5 agencias que asignamos por dirección | Distancias, horas de viaje y circuitos más exactos; la "agencia más cercana" deja de ser aproximada |
| **Capacidad comercial** | Número de asesores por agencia, jornadas de campo y metas de captación vigentes | Dimensionar los circuitos con la capacidad real en lugar del supuesto (12 visitas por día, 2 asesores por agencia) | Planes de la semana ejecutables y comparación justa con la prospección actual |
| **Penetración de la Caja por distrito** | Clientes activos por distrito, en total y por segmento | Descontar del potencial a quienes ya son clientes (hoy se estima con la presencia de agencias) | Evita priorizar zonas ya cubiertas y mejora el cálculo de clientes **nuevos** |
| **Productos para el segmento agro** | Condiciones del crédito agro y grupal vigente (montos, garantías requeridas, plazos) | Afinar el mensaje sugerido según la barrera de cada zona (falta de garantía, intereses altos) | Mensajes alineados con lo que la Caja realmente puede ofrecer |

Con los dos primeros insumos podríamos además hacer una **validación retrospectiva**: verificar si las zonas que RadarCT habría priorizado hace un año son las que más clientes nuevos dieron después. Eso complementaría la simulación con datos sintéticos.

---

## Desarrollos tecnológicos preexistentes *

Elegir en cada desplegable la opción más cercana a la sugerida.

| # | Tipo (sugerido) | Nombre | Nivel | Titularidad |
|---|---|---|---|---|
| 1 | Automatización / integración de datos | Pipeline de datos públicos territoriales | Prototipo funcional | Propia del equipo |
| 2 | Modelo analítico | Índice de oportunidad por segmento y mapa interactivo | Prototipo funcional | Propia del equipo |
| 3 | Automatización (extracción de datos) | Relevamiento de redes de agencias | Prototipo funcional | Propia del equipo |
| 4 | Módulo / algoritmo | Zonificación H3 y planificador de circuitos de asesores | Prototipo funcional | Propia del equipo |
| 5 | Modelo de simulación | Simulador de prospección con datos sintéticos | Prototipo funcional | Propia del equipo |

## Describan los desarrollos tecnológicos preexistentes *

Contamos con cinco componentes propios, desarrollados por el equipo en Python, que hoy funcionan como scripts de línea de comandos sobre datos públicos de La Libertad. Durante el hackathon construiremos encima de ellos la capa de producto (app del asesor, panel de gestión comercial, API, ciclo de aprendizaje y tablero de KPI).

1. **Pipeline de datos públicos territoriales.** Operativo: descarga y valida 7 fuentes públicas (RENIEC, padrón RUC de SUNAT, CENAGRO, CENAMA, límites distritales, SBS y redes de agencias), con reanudación de descargas, huella SHA-256 y un reporte de calidad; genera la tabla base por distrito. Uso en la propuesta: alimenta todos los demás módulos y permite cambiar de región con un parámetro.
2. **Índice de oportunidad por segmento y mapa interactivo.** Operativo: calcula el índice urbano/agro con parámetros de negocio (peso volumen/brecha, cupo agro, peso de la competencia), su estabilidad con 1 000 simulaciones, la auditoría de sesgo urbano/rural, las zonas sin agencia propia y un mapa HTML. Uso: es el motor del panel de gestión comercial que construiremos.
3. **Relevamiento de redes de agencias.** Operativo: lee las agencias publicadas por Caja Trujillo y cinco competidores (Mibanco, Efectiva y las cajas Arequipa, Del Santa y Paita) desde sus páginas y documentos públicos, y las asigna a distritos. Uso: presencia propia y de la competencia en el índice.
4. **Zonificación H3 y planificador de circuitos.** Operativo: divide los distritos agro priorizados en hexágonos de ~5 km² con productores excluidos y su barrera principal; arma circuitos semanales con orden de visita, horas de viaje, mensaje sugerido y número de asesores necesarios. Uso: genera el plan de la semana que verá el asesor en la app.
5. **Simulador de prospección con datos sintéticos.** Operativo: compara la prospección convencional con la propuesta con la misma capacidad de asesores, en 1 000 corridas con supuestos variables, y genera prospectos sintéticos (no personas reales). Uso: tablero de KPI y sustento cuantitativo del impacto.

**Titularidad y licencias.** Los cinco componentes son de titularidad del equipo. Usan librerías de código abierto de terceros bajo licencias permisivas: pandas y numpy (BSD-3, NumFOCUS y colaboradores), pyarrow (Apache 2.0, Apache Software Foundation), h3 (Apache 2.0, Uber Technologies), Leaflet (BSD-2, Volodymyr Agafonkin y colaboradores), requests (Apache 2.0), pypdf (BSD-3), openpyxl (MIT) y xlrd (BSD). Los datos provienen de fuentes públicas del Estado peruano (INEI, RENIEC, SUNAT, PRODUCE, SBS) y se citan; las redes de agencias se toman solo de páginas y documentos públicos de cada entidad. Los mapas usan fondos de Esri con atribución (uso de desarrollo; en producción, cuenta ArcGIS) y datos de OpenStreetMap (ODbL). No incluyen datos personales.

## Enlace de referencia (opcional)

Repositorio del equipo en GitHub (hoy **privado**: para incluirlo, hacerlo público o dar acceso a los evaluadores; si no, dejar el campo vacío).
