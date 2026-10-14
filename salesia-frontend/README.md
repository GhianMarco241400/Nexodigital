# SalesIA Frontend

Crea la interfaz visual (solo el frontend) de una aplicación web interna llamada SalesIA: el sistema de gestión que usan los trabajadores de una empresa que vende páginas web y apps móviles a pymes (combos con precio fijo en soles). NO es para clientes. Hazlo únicamente en React con TypeScript y Tailwind, con los gráficos en Recharts. Son solo pantallas y componentes visuales: los botones únicamente navegan entre pantallas o abren paneles y ventanas visuales. Todos los datos son de ejemplo, escritos en src/data con interfaces de TypeScript (Pedido, Venta, Cliente, Combo, Proveedor, Vendedor, Usuario, Alerta), separados de los componentes.

ESTILO: aspecto de software empresarial profesional. Azul corporativo como color principal, cyan como acento, fondos blancos y grises con un leve tono azul; verde, ámbar y rojo SOLO para estados. Tipografía sans-serif clara, esquinas suavemente redondeadas, sombras sutiles, nada de gradientes llamativos ni emojis.

PRINCIPIO DE DISEÑO: sobrio, limpio y NADA recargado. Prioriza legibilidad y jerarquía visual:
- El menú lateral agrupa los módulos en secciones desplegables; solo la sección activa aparece abierta, y el menú puede contraerse a solo iconos.
- Cada pantalla tiene UNA acción principal visible; las secundarias van en un menú "⋯".
- Las tablas muestran solo las columnas esenciales; el detalle se abre en un panel lateral o en pestañas.
- Los filtros se agrupan en un botón "Filtros" que abre un popover.
- Usa pestañas para comprimir contenido relacionado dentro de un mismo módulo.
- Mucho espacio en blanco y máximo 4 tarjetas de indicadores por pantalla.

MENÚ (separa las operaciones del mantenimiento: clientes, productos y proveedores NUNCA van mezclados con ventas):
1. Operaciones: Pedidos, Ventas (con pagos), Inventario.
2. Mantenimiento: Clientes, Productos (combos, extras y categorías), Proveedores, Vendedores.
3. Análisis: Analytics, Insights, Reportes.
4. Administración: Usuarios y roles, Auditoría, Seguridad (revisión con IA).
Barra superior: buscador, notificaciones y menú de usuario con nombre, rol y un selector de demostración "Ver como" (Administrador, Gerente, Vendedor, Analista, Almacén) que muestra u oculta módulos según el rol: Vendedor ve Pedidos, Ventas y Clientes; Almacén ve Inventario, Productos y Proveedores; Analista ve Analytics, Insights y Reportes; Gerente ve Dashboard, Ventas, Analytics y Reportes; Administrador ve todo.

PANTALLAS
- /login: pantalla de inicio de sesión visual con el nombre SalesIA.
- Dashboard (inicio): 4 indicadores (ventas del mes, ticket promedio, pedidos pendientes, clientes activos), un gráfico de líneas de ventas por periodo y una tabla corta de últimos pedidos.
- Pedidos: tabla con código (formato PED-0249), cliente, combo, total, estado (Pendiente de revisión, En revisión, Confirmado, Rechazado) y riesgo (bajo, medio, alto), con pestañas por estado. Detalle: datos de la empresa, combo y extras con precios, y un panel "Revisión con IA" con resumen en lenguaje claro, alertas resaltadas y nivel de riesgo; botones Confirmar venta y Rechazar, una casilla "Revisé los datos" y una línea de tiempo del historial.
- Ventas: tabla (número, cliente, vendedor, método de pago: Efectivo, Yape, Tarjeta o Transferencia, total, estado), con pestañas "Ventas" y "Pagos".
- Inventario: cupos disponibles por combo y región con barras de progreso, alertas de poco cupo y pestaña "Movimientos".
- Clientes, Productos, Proveedores y Vendedores: tabla simple con buscador y botón "Nuevo" que abre un formulario en panel lateral.
- Analytics con pestañas: "Resumen" (media, mediana, cantidad de ventas, comparación media vs. mediana con histograma y un recuadro de insight), "Variables" (variables estadísticas y aleatorias con gráficos), "Probabilidad y Bayes" (formulario con P(A), P(B|A) y P(B), botón Calcular, la fórmula P(A|B) = P(B|A)·P(A) / P(B) y el resultado explicado paso a paso) e "Historial" de análisis guardados. Los filtros (periodo, vendedor, combo) van dentro del botón "Filtros".
- Insights: lista corta de tarjetas, cada una con la observación y el número que la respalda.
- Reportes: tarjetas de reportes (ventas, productos, clientes, estadístico) con vista previa imprimible y botón Exportar.
- Usuarios y roles: tabla con roles y estado.
- Auditoría: registro de acciones (fecha, usuario, acción) con filtros.
- Seguridad: alertas de anomalías (descuentos fuera de lo normal, intentos de ingreso fallidos, ventas fuera de horario) con severidad y evidencia.

Todas las tablas y formularios principales incluyen estados de carga (skeleton), vacío, error y éxito (toast). Responsive para escritorio y tablet. Datos de ejemplo con empresas peruanas ficticias, precios en soles y una etiqueta "Datos de ejemplo".

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/42d41f1c-b193-44ae-abec-608b67775950).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
