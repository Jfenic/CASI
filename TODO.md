# CASI - TODO

Lista priorizada de próximos pasos del proyecto.

## Prioridad inmediata

- [ ] Confirmar `apply_patch` desde el modelo.
  - Impedir que el modelo aplique cambios sin aprobación interactiva.
  - Validar siempre el parche antes de escribir.

- [ ] Implementar permisos de herramientas.
  - Permitir lectura y búsqueda automáticamente.
  - Requerir confirmación para ejecución y modificación.
  - Rechazar herramientas no registradas.

- [ ] Añadir contexto conversacional persistente.
  - Mantener mensajes entre tareas de la sesión.
  - Conservar límites de pasos y tamaño de contexto.
  - Permitir limpiar el contexto con `/clear`.

## Calidad Y Seguridad

- [ ] Completar pruebas de parches.
  - Crear archivos con `git apply`.
  - Eliminar archivos con `git apply`.
  - Rechazar rutas sensibles y traversal.
  - Verificar que un rechazo no modifica el repositorio.

- [ ] Integrar sandbox Docker seguro.
  - Ejecutar sobre una copia temporal.
  - Desactivar red.
  - Usar usuario no root.
  - Aplicar límites de CPU, memoria, tiempo y salida.

## CLI Y Evaluación

- [ ] Añadir comando `casi test`.
  - Mostrar código de salida, duración, stdout y stderr.
  - Permitir configurar timeout.
  - Mantener una lista de comandos permitidos.

- [ ] Actualizar benchmarks y métricas.
  - Medir éxito de tarea.
  - Medir validez de parches.
  - Medir tests pasados, pasos, tiempo y errores.
  - Generar informes reproducibles.

## Cierre De Cada Hito

- [ ] Ejecutar la suite completa de pruebas.
- [ ] Ejecutar `python3 -m compileall -q src tests`.
- [ ] Ejecutar `git diff --check`.
- [ ] Actualizar `README.md`, `planning.md` y `docs/implementation-tracker.md`.
- [ ] Crear un commit Git pequeño y descriptivo.
- [ ] Confirmar que el working tree queda limpio.
