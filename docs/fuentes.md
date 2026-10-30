# Fuentes sobre estafas por mensajes en Guatemala

Información recopilada para construir la base de conocimiento (`data/patrones.json`) y el conjunto de mensajes reales (`data/reales.jsonl`). Los textos de los mensajes reales se tomaron tal cual los citan las fuentes; conviene revisarlos en la URL original.

## Contexto del problema

- Los ciberdelitos registrados por el Ministerio Público pasaron de 1,292 casos en 2019 a 14,871 en 2025, y en el primer semestre de 2026 hubo 7,925 denuncias por estafas electrónicas. [AGN, 10/08/2026](https://agn.gt/?p=562196)
- El MP recibe unas 50 denuncias diarias por estafas digitales y reconoce 23 modalidades en 5 categorías. Por plataforma, Facebook concentra el 33% y WhatsApp el 14%. [Prensa Libre, 29/11/2025](https://www.prensalibre.com/guatemala/justicia/estafas-digitales-en-guatemala-las-redes-y-metodos-que-mas-afectan-a-los-usuarios/)
- Las estafas por grupos de tareas pagadas en WhatsApp y Telegram sumaron 148 denuncias en 2023 y 145 solo entre enero y abril de 2024, con un daño promedio que pasó de unos Q24 mil a unos Q70 mil. [Prensa Libre, 21/05/2024](https://www.prensalibre.com/guatemala/justicia/estafas-por-whatsapp-alertan-sobre-nueva-modalidad-de-engano-en-guatemala/)
- El 12% de los guatemaltecos encuestados por TransUnion fue víctima de fraude digital en el primer trimestre de 2025, el porcentaje más alto entre los países de la encuesta. [newsinamerica, 08/05/2025](https://newsinamerica.com/pdcc/gente/tecnologia/2025/los-consumidores-guatemaltecos-informan-ser-mas-victimas-de-fraude-digital-en-comparacion-con-otros-paises)
- La PMT vinculó unos 40 números a mensajes de multas de tránsito falsas y recibió cerca de 150 quejas en 2026. [Prensa Libre, 03/07/2026](https://www.prensalibre.com/guatemala/pmt-de-guatemala-amplia-alerta-por-estafas-digitales-hay-mas-denuncias-y-nuevos-metodos-como-whatsapp-y-correo-electronico/)

## Modalidades agregadas a partir de la investigación

| Patrón | Fuente principal |
|---|---|
| Multa de tránsito falsa (PMT o Emetra) | [La Hora, 09/02/2026](https://lahora.gt/nacionales/dleon/2026/02/09/alertan-sobre-estafas-mediante-mensajes-falsos-por-supuesto-cobro-de-infracciones/), [Agencia Ocote, 09/06/2026](https://www.agenciaocote.com/blog/2026/06/09/tiene-una-multa-pendiente-la-estafa-por-sms-y-whatsapp-que-se-viraliza-en-guatemala/) |
| Encomienda o maletas de un familiar en el extranjero | [Soy502, 09/06/2021](https://www.soy502.com/articulo/victimas-alertan-estafa-whatsapp-ocurrida-guatemala-153), [Prensa Libre, 23/11/2024](https://www.prensalibre.com/guatemala/justicia/como-operaba-en-redes-sociales-y-whatsapp-red-de-supuestos-estafadores-desarticulada-por-pnc/) |
| Grupo de tareas pagadas que termina en inversión | [Prensa Libre, 21/05/2024](https://www.prensalibre.com/guatemala/justicia/estafas-por-whatsapp-alertan-sobre-nueva-modalidad-de-engano-en-guatemala/), [Soy502, 28/04/2025](https://www.soy502.com/articulo/dinerofacil-forma-estan-estafando-guatemaltecos-101477) |
| Devolución o reembolso falso (IGSS o SAT) | [Soy502, 12/10/2026](https://www.soy502.com/articulo/nueva-modalidad-estafa-alerta-guatemaltecos-101026) |
| Puntos de tarjeta por vencer | [Banrural, alerta de smishing](https://www.banrural.com.gt/alerta-de-smishing) |

Las fuentes de los demás patrones están en el campo `fuentes` de cada uno en `data/patrones.json`.

## Canales oficiales para denunciar o verificar

- PNC, emergencias y denuncias: 110. WhatsApp confidencial: 3764-1561. [AGN, 14/01/2026](https://agn.gt/?p=509172)
- Denuncia anónima (Crime Stoppers): 1561.
- Línea antiextorsión de la PNC: 1574.
- Ministerio Público: sedes, mp.gob.gt y la app MPVirtual.
- Banrural: 2308-3000 (opción 0) y correo.sospechoso@banrural.com.gt. [Banrural, ciberseguridad](https://www.banrural.com.gt/ciberseguridad)
- Correos de Guatemala: 1595, WhatsApp 2318-7700 y correos.gob.gt. [La Hora, 29/09/2026](https://lahora.gt/nacionales/ralvarado/2026/09/29/correos-de-guatemala-alerta-por-mensajes-de-texto-fraudulentos-a-usuarios-now/)
- MIDES: mides.gob.gt. PMT y Emetra: solo muniguate.com.
