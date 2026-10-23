# Informe Completo de Benchmarks y Conclusiones — 2026-09-21

Evaluación exhaustiva del agente **CASI** ejecutada sobre la totalidad de las suites de benchmarks del proyecto utilizando el modelo local **`qwen3.5:4b`** en un entorno aislado con Docker (`casi-sandbox:latest`).

---

## 1. Metadatos de la Ejecución

| Parámetro | Valor |
| :--- | :--- |
| **Fecha** | 2026-09-21 |
| **Modelo evaluado** | `qwen3.5:4b` (`digest: 2a654d98e6fba55d...`, 4.7B params, Q4_K_M) |
| **Commit base** | `eb1cab0a4e17a8cf248843ebee493a8586dfeeb5` |
| **Entorno de ejecución** | Python 3.12.3, Linux x86_64, Docker 28.1.1 |
| **Modo de sandbox** | Docker sin red, usuario no-root, sin fallback local |
| **Routing** | `assist` |
| **Duración total** | 85.0 minutos (5,098.5 segundos) |
| **Puntuación global (Aceptación Independiente)** | **63 / 76 tareas (82.89%)** |
| **Tasa de éxito del agente (Agent Success)** | **69 / 76 tareas (90.79%)** |
| **Validez de parches generados** | **100.00%** |

Los artefactos completos por tarea (trazas `trace.json`, respuestas `response.txt`, salidas de prueba `verification.txt` y diffs `proposal.diff`) se encuentran archivados en el directorio:
[`docs/reports/2026-09-21-full-suite-qwen35-4b/`](2026-09-21-full-suite-qwen35-4b/).

---

## 2. Resultados Consolidados por Suite

| Suite | Tareas | Aprobadas | Tasa Tarea | Tasa Agente | Validez Parche | Duración | Informe Específico |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| **Security** | 3 | 3 | **100.00%** | 100.00% | 100.00% | 73.1s | [security.md](2026-09-21-full-suite-qwen35-4b/security.md) |
| **General** | 26 | 25 | **96.15%** | 96.15% | 100.00% | 549.9s | [general.md](2026-09-21-full-suite-qwen35-4b/general.md) |
| **Fundamentals** | 9 | 8 | **88.89%** | 100.00% | 100.00% | 235.2s | [fundamentals.md](2026-09-21-full-suite-qwen35-4b/fundamentals.md) |
| **ML** | 6 | 5 | **83.33%** | 100.00% | 100.00% | 189.4s | [ml.md](2026-09-21-full-suite-qwen35-4b/ml.md) |
| **Development** | 12 | 9 | **75.00%** | 75.00% | 100.00% | 1624.9s | [development.md](2026-09-21-full-suite-qwen35-4b/development.md) |
| **Diagnosis** | 8 | 6 | **75.00%** | 100.00% | N/A | 96.8s | [diagnosis.md](2026-09-21-full-suite-qwen35-4b/diagnosis.md) |
| **Capabilities v2 — ML** | 4 | 3 | **75.00%** | 100.00% | 100.00% | 158.9s | [v2_ml.md](2026-09-21-full-suite-qwen35-4b/v2_ml.md) |
| **Capabilities v2 — Security** | 4 | 2 | **50.00%** | 75.00% | 100.00% | 393.1s | [v2_security.md](2026-09-21-full-suite-qwen35-4b/v2_security.md) |
| **Capabilities v2 — Testing** | 4 | 2 | **50.00%** | 50.00% | 100.00% | 1776.0s | [v2_testing.md](2026-09-21-full-suite-qwen35-4b/v2_testing.md) |
| **Total / Promedio** | **76** | **63** | **82.89%** | **90.79%** | **100.00%** | **85.0 min** | [summary.md](2026-09-21-full-suite-qwen35-4b/summary.md) |

---

## 3. Análisis Detallado de Hallazgos

### 3.1. Rendimiento Sobresaliente en Tareas de Corrección (`fix`)
- En la suite **Development**, todas las tareas de tipo `fix` pasaron limpiamente (**7 de 7**, 100%): `dev_001`, `dev_002`, `dev_003`, `dev_004`, `dev_005`, `dev_006`, `dev_011` y `dev_012`.
- Destaca especialmente la recuperación estable de `dev_006` (regresión por mutabilidad recursiva de diccionarios) y `dev_003` (manejo de CSV multilínea con CRLF).
- La infraestructura de sanitización de errores implementada previamente (`tail strategy` y truncado semántico) evitó saturar el contexto de 4B tokens, permitiendo al agente iterar con parches correctos sin perder las aserciones de fallo.

### 3.2. Causa Raíz de Fallos en Tareas de Creación (`create`)
De las 13 tareas fallidas en la batería completa, 5 correspondieron a tareas de creación donde el modelo agotó el presupuesto de 18 pasos:
- `dev_008` (orden topológico con desempates lexicográficos y detección de ciclos).
- `dev_009` (diseño de tests de reintentos contra 5 mutaciones).
- `dev_010` (tests de regresión de slugificación contra 5 mutaciones).
- `task_023` (creación de módulo `initials.py`).
- `test_002` (suite de tests de regresión con mutaciones).

**Patrón observado:** Al enfrentarse a generación de código compleja o diseño de tests contra múltiples mutaciones sin código previo en el repositorio, `qwen3.5:4b` emite periódicamente respuestas de acción vacías (`empty model response: Ollama action response does not contain content`). Aunque los nudges automáticos de CASI mantienen la sesión viva y solicitan una llamada válida, el modelo consume sus pasos sin converger a un parche final.

### 3.3. Restricciones de Ámbito y Seguridad (`allowed_files`)
- En `test_001` (Capabilities v2 — Testing), el agente formuló una solución correcta para los tests, pero incluyó modificaciones en `retrying.py` (el archivo de implementación base).
- El validador de CASI rechazó correctamente el parche por violar `allowed_files: ["test_retrying.py"]`. Esto demuestra que las salvaguardas de seguridad del agente funcionan según lo especificado en la arquitectura, impidiendo mutaciones no autorizadas fuera del alcance asignado.

### 3.4. Casos Límite en Verificación Independiente
Un subconjunto de tareas falló exclusivamente en la evaluación externa (los tests visibles del repositorio pasaban, pero el grader withholding rechazó la solución):
- **`fund_008` (Fundamentals):** El modelo implementó una conversión a binario pero generó los bits en orden invertido (`'01'` en lugar de `'10'`).
- **`ml_003` (ML):** El agente calculó la desviación estándar con corrección muestral ($N-1$) mientras que la prueba independiente requería desviación poblacional ($N$).
- **`sec_v2_002` (Capabilities v2 — Security):** La función de extracción segura no detectó adecuadamente enlaces simbólicos relativos que apuntaban a directorios externos autorizados.
- **`diag_002` y `diag_006` (Diagnosis):** El agente diagnosticó el fallo en el código y la causa general, pero las palabras o símbolos clave requeridos por la rúbrica determinista no coincidieron textualmente.

---

## 4. Conclusiones y Próximos Pasos

1. **Estado del Agente:**
   - La arquitectura modular (evaluador de tareas con perfiles especializados, sanitización de errores, verificación en Docker y aislamiento git) es altamente sólida y determinista.
   - Alcanzar un **82.89% global en 76 tareas** con un modelo ligero de 4.7B parámetros (`qwen3.5:4b`) confirma la efectividad de las restricciones guiadas por esquema y la ejecución de herramientas.

2. **Áreas de Mejora para el Backlog:**
   - **Guía de generación en `create`:** Mejorar los templates o prompts del rol `create` para modelos pequeños, proporcionando una estructura de esqueleto que evite respuestas vacías en tareas algorítmicas densas.
   - **Nudges proactivos de ámbito:** Inyectar en el prompt de sistema una advertencia explícita sobre `allowed_files` cuando la tarea tenga una lista blanca restringida, para evitar rechazos como el de `test_001`.
   - **Rúbricas de diagnóstico:** Considerar una tolerancia semántica básica en las comprobaciones de texto para diagnósticos en lugar de coincidencias literales de expresiones regulares.

3. **Alineación con el Roadmap:**
   - Habiendo validado de forma exhaustiva el rendimiento base de todo el conjunto de benchmarks, el proyecto se encuentra en condiciones óptimas para avanzar en la prioridad inmediata estipulada en [TASKS.md](../TASKS.md): **API & UI Persistence & Hardening** (almacenamiento SQLite/archivo para tareas y trazas, clarificaciones vía HTTP y verificación E2E de la UI).
