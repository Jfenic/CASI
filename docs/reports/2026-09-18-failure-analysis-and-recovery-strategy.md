# Análisis de Fallos del Benchmark y Estrategia de Recuperación

**Fecha:** 2026-09-18  
**Modelo evaluado:** `qwen3.5:4b` (Ollama local)  
**Suite:** Development Benchmark (12 tareas)  
**Resultado de la corrida:** 5 / 12 (41.67%) vs. 9 / 12 (75.00%) anterior  

---

## 1. Resumen Ejecutivo

En la última corrida del benchmark sobre `qwen3.5:4b`, el rendimiento bajó de **9/12 (75%)** a **5/12 (41.67%)**. 

El análisis forense de las trazas (`trace.json`), diffs propuestos (`proposal.diff`) y fallos de verificación (`verification.txt`) revela que el descenso **no fue por errores en las herramientas o en el bucle de CASI** (la tasa de parches válidos fue del **100%**), sino por tres patrones claros:

1. **Sesgo del test visible (Overfitting a tests mínimos):** El modelo repara el bug que hace fallar el test visible del repositorio, pero ignora los requerimientos explícitos de la instrucción (tipos inválidos, números gigantes, multilínea). Al ver que el test visible pasa en el sandbox Docker, el modelo concluye prematuramente.
2. **Atajos sintácticos peligrosos en modelos pequeños (4B):**
   - Uso de `str(value)` en lugar de `isinstance(value, str)`.
   - Conversión final `float(decimal_total)` destruyendo la precisión de 64 bits.
   - `text.splitlines()` antes de `csv.reader()`, rompiendo campos entrecomillados con saltos de línea.
3. **Agotamiento de pasos en tareas CREATE de diseño de tests:** En tareas donde no hay código que reparar sino que hay que escribir una suite de tests desde cero (`dev_009`, `dev_010`), el modelo de 4B sufre para generar 40+ líneas de código en un solo bloque JSON y emite respuestas vacías o incompletas hasta agotar los 18 pasos.

---

## 2. Análisis Detallado Tarea por Tarea

### `dev_002` (boolean_config) — Regresión por validación de tipos
* **Instrucción:** `Non-string non-bool values raise TypeError.`
* **Test visible:** Solo probaba `parse_bool("false") is False`.
* **Código propuesto por el modelo:**
  ```python
  try:
      str_value = str(value)
  except TypeError:
      raise TypeError(...)
  ```
* **Fallo:** En Python, `0`, `1`, `[]`, `{}` se convierten perfectamente a string (`"0"`, `"[]"`), por lo que nunca lanzaban `TypeError`. Para `0` devolvía `False`, y para `[]` lanzaba `ValueError("Invalid boolean representation: '[]'")`.
* **Causa raíz:** El modelo intentó coercion genérica en lugar de comprobar estrictamente `if not isinstance(value, str): raise TypeError(...)`.

---

### `dev_003` (csv_totals) — Regresión por parseo de CSV
* **Instrucción:** `Input is CSV with headers product,quantity and standard CSV quoting.`
* **Test visible:** `totals("product,quantity\npen,2\npen,3\n") == {"pen": 5}`.
* **Código propuesto por el modelo:**
  ```python
  reader = csv.reader([line.strip() for line in text.splitlines()], delimiter=',')
  ```
* **Fallo:** Al hacer `text.splitlines()`, un campo entrecomillado multilínea como `"two\nlines",4` se parte en dos elementos separados antes de llegar a `csv.reader`, generando `{'twolines': 4}` en vez de `{'two\nlines': 4}`.
* **Causa raíz:** No usar `io.StringIO(text)` como stream nativo para `csv.reader`.

---

### `dev_004` (invoice_rounding) — Regresión por conversión redundante a float
* **Instrucción:** Formato con dos decimales usando precisión y redondeo exacto.
* **Código propuesto por el modelo:**
  ```python
  total += rounded_line
  return f"{float(total):.2f}"
  ```
* **Fallo:** El cálculo con `Decimal` era 100% correcto (`9007199254740993.31`), pero al hacer `float(total)`, el valor supera los 53 bits de mantisa de IEEE 754 ($2^{53} = 9007199254740992$), perdiendo precisión y redondeándose a `9007199254740994.00`.
* **Causa raíz:** Casteo innecesario a `float` en lugar de formatear directamente el `Decimal`: `f"{total:.2f}"`.

---

### `dev_006` (settings_merge) — Agotamiento de pasos por respuesta vacía
* **Instrucción:** Mezcla recursiva de diccionarios con deep copy independiente.
* **Comportamiento:** En el paso 18, Ollama devolvió respuestas con contenido vacío o JSON incompleto (`Ollama message does not contain usable content`), impidiendo que el agente emitiera su parche final dentro del límite de pasos.
* **Causa raíz:** Degradación de contexto largo en `qwen3.5:4b` cuando se acumulan nudges y salidas de tests en la ventana de contexto.

---

### `dev_008` (dependency_order) — Fallo en algoritmo de grafos
* **Instrucción:** Ordenamiento topológico lexicográfico ante tareas con dependencias implícitas y duplicadas.
* **Fallo:** `ValueError("Cycle detected...")` porque el modelo asumió que todos los nodos existían como claves del grafo, fallando al indexar nodos implícitos que solo aparecen como prerequisitos.
* **Causa raíz:** Tarea algorítmica compleja que supera el razonamiento cero-disparo de un modelo de 4B.

---

### `dev_009` (retry_tests) y `dev_010` (slug_tests) — Bloqueo en Test Writing
* **Instrucción:** Crear `test_retry.py` / `test_slug.py` sin modificar el código fuente.
* **Comportamiento:** Consumen el 70% del tiempo de todo el benchmark (11 minutos en `dev_009` y 7 minutos en `dev_010`). El modelo entra en bucle llamando a `list_files` y `read_file` sin atreverse a emitir el archivo completo mediante `propose_file`, hasta agotar los 18 pasos.
* **Causa raíz:** El modelo no sabe qué aserciones escribir si no tiene una plantilla mental o directriz clara de casos de prueba.

---

## 3. Estrategia de Recuperación (Plan de Acción)

Para recuperar el **75% (9/12)** de inmediato y avanzar hacia el **85-90% (10-11/12)**, implementaremos cuatro palancas complementarias:

### Palanca 1: Nudge de Verificación de Contrato Exhaustivo (Anti-Overfitting de Test Visible)
**Problema:** El modelo se conforma en cuanto ve `1 passed` en `run_tests`.  
**Solución:** Modificar las instrucciones del perfil `fix` y los nudges de CASI:
- Antes de dar por buena una solución porque los tests visibles pasaron, inyectar una comprobación mental de contrato:
  > *"Existing visible tests in the repository may be minimal. Reread the prompt instruction carefully: verify explicit requirements regarding invalid types, negative inputs, empty collections, multiline strings, and numerical precision before completing."*

### Palanca 2: Reglas Defensivas Específicas en el Prompt del Especialista `fix`
Añadir a `PROFILES[TaskIntent.FIX]` directrices defensivas concretas contra los 3 patrones de fallo detectados:
1. **Tipos:** *"When validating types, use strict `isinstance(val, expected_type)` checks. Never rely on `try: str(val)` to detect strings or numbers."*
2. **Precisión numérica:** *"When calculations require `Decimal`, never convert the result back to `float` before formatting; use `f'{decimal_val:.2f}'` directly."*
3. **Archivos y CSV:** *"When parsing delimited text or CSV, pass `io.StringIO(text)` to standard library readers like `csv.reader()`. Never pre-split lines with `splitlines()` as it breaks quoted multiline fields."*

### Palanca 3: Desbloqueo del Especialista `test_engineer` (Fases de Escritura)
Para `dev_009` y `dev_010`, la personalidad `test_engineer` (incorporada en la orquestación) debe activarse con una directiva de acción inmediata:
- En lugar de permitir que gaste 10 pasos inspeccionando archivos ya leídos, forzar que en el paso 2 o 3 emita un primer borrador de tests con `propose_file` conteniendo:
  1. Caso nominal (happy path).
  2. Casos límite (límites vacíos, cero, None, tipos erróneos).
  3. Comprobación de excepciones esperadas con `pytest.raises()`.

### Palanca 4: Estrategia de Inferencia y Modelo
- **Ajuste de Temperatura:** Fijar `temperature: 0.0` para benchmarks y tareas de código para eliminar la variabilidad estocástica observada entre corridas.
- **Opción de Modelo 7B/8B:**
  - `qwen3.5:4b` es un modelo ligero excelente para velocidad, pero tiene límites claros de capacidad en diseño de suites de test y grafos topológicos.
  - El proyecto ya cuenta con `qwen2.5-coder:7b` y `qwen3:8b` instalados en Ollama. Una ejecución comparativa con `--models qwen3.5:4b,qwen2.5-coder:7b` permitirá constatar el salto de calidad directo en las tareas complejas.

---

## 4. Matriz de Impacto Estimado

| Tarea | Corrida Actual | Con Palanca 1 & 2 (Prompts defensivos) | Con Palanca 3 & 4 (Modelo 7B / Temp 0) |
| :--- | :---: | :---: | :---: |
| `dev_001` (pagination) | ✅ PASS | ✅ PASS | ✅ PASS |
| `dev_002` (boolean_config) | ❌ FAIL | ✅ **PASS** (isinstance estricto) | ✅ **PASS** |
| `dev_003` (csv_totals) | ❌ FAIL | ✅ **PASS** (io.StringIO) | ✅ **PASS** |
| `dev_004` (invoice_rounding) | ❌ FAIL | ✅ **PASS** (Decimal sin float) | ✅ **PASS** |
| `dev_005` (ttl_cache) | ✅ PASS | ✅ PASS | ✅ PASS |
| `dev_006` (settings_merge) | ❌ FAIL | ✅ **PASS** (menor acumulación de contexto) | ✅ **PASS** |
| `dev_007` (jsonl_reader) | ✅ PASS | ✅ PASS | ✅ PASS |
| `dev_008` (dependency_order) | ❌ FAIL | ❌ FAIL (algoritmo complejo) | ✅ **PASS** (7B resuelve topológico) |
| `dev_009` (retry_tests) | ❌ FAIL | ⚠️ Posible PASS | ✅ **PASS** |
| `dev_010` (slug_tests) | ❌ FAIL | ⚠️ Posible PASS | ✅ **PASS** |
| `dev_011` (version_parse) | ✅ PASS | ✅ PASS | ✅ PASS |
| `dev_012` (checkout_mini) | ✅ PASS | ✅ PASS | ✅ PASS |
| **Puntuación proyectada** | **5 / 12 (41.7%)** | **8 - 9 / 12 (66% - 75%)** | **11 - 12 / 12 (91% - 100%)** |
