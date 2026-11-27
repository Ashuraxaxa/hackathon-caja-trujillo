# Decisiones del owner (respuestas recibidas el 27-11-2026)

| Tema | Respuesta (resumen) | Cómo lo aplicamos |
|---|---|---|
| Ámbito geográfico | Libre: urbano, rural o periurbano, en regiones donde la Caja opera o puede expandirse. Delimitar un ámbito para el prototipo y mostrar escalabilidad. | Piloto en **La Libertad**. El pipeline es paramétrico (`DEPARTAMENTOS_PILOTO` en `fase0/sources.py`) para replicarlo en otras regiones. |
| Valor diferencial | Demo funcional + evidencia cuantitativa con **datos sintéticos** (más fuentes públicas): comparar prospección convencional frente a la propuesta. No hace falta backtest con datos de la Caja. Declarar fuentes, supuestos y limitaciones; no presentar lo simulado como real. | `fase3/simulacion.py`: mundo sintético por distrito, misma capacidad de asesores en ambos escenarios, Monte Carlo con supuestos variables y resultados rotulados como simulados. |
| Éxito | **Cliente nuevo para Caja Trujillo con su primera operación crediticia**, aunque ya tenga productos en otras entidades. Complementarios: prospectos con consentimiento, apertura de ahorro y personas que entran por primera vez al sistema financiero. | KPI principal: nuevos clientes con primer crédito en la Caja. KPI secundarios: consentimientos y clientes nuevos en el sistema financiero. |
| Usuario principal | **Asesor de negocios**; también la gestión comercial. | Las rutas y circuitos son para el asesor; el índice y el mapa son para la gestión comercial. |
| Decisión a mejorar | **Dónde y en qué segmentos concentrar la prospección.** Puede bajar a zonas, rutas y campañas. No hace falta proponer agencias ni agentes. | Se quita la recomendación de abrir agentes o agencias; las zonas lejanas se trabajan con jornadas concentradas (con pernocte). |

Pendientes que no respondieron: cupo agro, si la competencia resta puntos y confirmación del distrito de 5 agencias. Mantenemos los valores por defecto (cupo agro 40 %, la competencia resta hasta 30 %) y los mostramos como parámetros.
