Ejemplos de referencia (no son el mensaje a analizar):

Mensaje (número desconocido): "BI: Estimado cliente, detectamos un intento de compra por Q4,890 con su tarjeta. Si no lo reconoce, cancele en bi-alertas.com/cancelar antes de 30 minutos."
Respuesta esperada: veredicto "estafa", certeza "alta", tipo "banco_bloqueo". El enlace bi-alertas.com no es el dominio oficial del banco y la urgencia busca que ingresés tus datos.

Mensaje (empresa o código corto): "Banrural: Su codigo de seguridad es 482915. No lo comparta con nadie, ni con personal del banco."
Respuesta esperada: veredicto "seguro", certeza "alta", tipo "ninguno". Es un código que el propio usuario solicitó y el banco advierte que no se comparta.

Mensaje (número desconocido): "Hola papi, se me cayó el cel al agua y este es mi número nuevo. Ocupo que me depositás Q800 para pagar algo de la U, no me llames porque no tengo señal aquí"
Respuesta esperada: veredicto "estafa", certeza "alta", tipo "familiar_emergencia". Número nuevo, pedido urgente de dinero y pide que no llamen para verificar.

Mensaje (contacto guardado): "Vos ya me podés pasar los Q75 de la pizza del sábado? te mando mi cuenta de BI por si acaso: 0170012345"
Respuesta esperada: veredicto "seguro", certeza "alta", tipo "ninguno". Es un contacto conocido cobrando un gasto compartido pequeño, sin urgencia ni enlaces.

Mensaje (número desconocido): "Buenas, vi tu anuncio de la refri en Marketplace. ¿Todavía la tenés? Me gustaría pasar a verla mañana en la tarde, ¿en qué zona estás?"
Respuesta esperada: veredicto "seguro", certeza "media", tipo "ninguno". Un comprador que quiere ver el producto en persona es normal; solo conviene reunirse en un lugar público.

Mensaje (empresa o código corto): "Cada semana hay nuevos ganadores. Vos podes ser el siguiente ganador de un VW o Motos Honda. No dejes la dejes pasar! Si la usas, ganas: http://tgor.me/j8y?1h6"
Respuesta esperada: veredicto "seguro", certeza "media", tipo "ninguno". Es publicidad de una promoción de marca enviada con su nombre como remitente por la plataforma de SMS que usan las empresas. Invita a participar comprando el producto y no pide datos, códigos ni pagos.

Mensaje (número desconocido): "VISA: Recuerda que tus 12,500 pt0s expiran hoy. No pierdas la oportunidad de canjearlos. https://lnk.ink/PKvTE"
Respuesta esperada: veredicto "estafa", certeza "alta", tipo "puntos_por_vencer". Una marca no escribe desde un número celular común, el enlace es un acortador anónimo y la urgencia de que los puntos vencen hoy busca que ingresés los datos de tu tarjeta.
