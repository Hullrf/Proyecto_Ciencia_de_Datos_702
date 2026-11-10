# Predicción del ganador de un mapa (VCT) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Proyecto de curso que predice qué equipo gana un mapa de VCT, contado en 7 cuadernillos en español, con funciones compartidas en `src/`, gráficos en `reports/`, modelos en `models/` y enlazado a GitHub.

**Architecture:** Los CSV crudos (por año) se unen en una tabla base de mapas ordenada cronológicamente por ID. Sobre ella se calculan variables históricas por equipo (solo con mapas anteriores) y se expresan como diferencia A − B. Tres modelos de scikit-learn se comparan con partición temporal por año.

**Tech Stack:** Python 3.11, pandas, numpy, scikit-learn, matplotlib, seaborn, joblib, pyyaml, jupyter (nbconvert). Nada más.

**Spec:** `docs/specs/2026-11-10-prediccion-ganador-mapa-design.md`

## Global Constraints

- Texto de cuadernillos y documentos en español; identificadores de código y columnas derivadas en inglés.
- Cada cuadernillo: celda inicial `# NN — Título` + `## Objetivo`; una celda de texto antes de cada bloque de código explicando qué se hace y por qué; celda final `## Conclusiones` con hallazgos concretos (números reales de la ejecución) y enlace al siguiente paso.
- Nombres `NN_nombre.ipynb`, numeración ascendente desde `00`.
- Primera celda de código de cada cuadernillo: `import sys; sys.path.append("..")` y luego imports de `src`.
- Todo gráfico se guarda con `save_fig("NN_descripcion")` en `reports/figures/`; toda tabla de resultados en `reports/tables/` como CSV.
- Ninguna variable puede usar información del mapa que se predice ni de mapas posteriores.
- Partición temporal por año, nunca aleatoria. El conjunto de prueba se usa una sola vez (cuadernillo 06).
- `data/raw/` nunca se sube a git. Ningún archivo de más de 50 MB se sube.
- Sin dependencias nuevas. Semilla fija: 42.
- Los cuadernillos se entregan ejecutados: `jupyter nbconvert --to notebook --execute --inplace notebooks/NN_*.ipynb` debe terminar sin error.
- Git: `git add` de archivos puntuales, nunca `-A`. Trabajo en `feature/modelo-prediccion`; solo el commit inicial va a `main` (autorizado por el usuario). El merge del PR lo hace el usuario.
- No describir el proyecto como "terminado" en ningún texto.

## Datos verificados (2026-11-10)

- Mapas por año en `maps_scores.csv`: 2021: 14 503 · 2022: 8 884 · 2023: 830 · 2024: 1 104 · 2025: 1 277 · 2026: 886.
- Rangos de `Match ID` por año no se solapan y crecen (2021: 8756–51296 … 2026: 594740–684619) → sirven como orden cronológico.
- 2021–2022 traen suciedad: 27 empates por año, 23 y 4 claves duplicadas, ~20 mapas sin ID. 2023+ limpios.
- Team A gana 58 % en 2021–2022 y ~51 % después → sesgo de posición real.
- `draft_phase.csv` cubre solo 871 de 7 217 partidos en 2021; `eco_stats.csv` 4 319 de 7 217.
- `overview.csv`: columna `Side` ∈ {both, attack, defend}; `Map` incluye la fila agregada `All Maps`. Porcentajes vienen como texto (`"81%"`).
- `eco_stats.csv` `Type` ∈ {Pistol Won, Eco (won), $ (won), $$ (won), $$$ (won)}. `draft_phase.csv` `Action` ∈ {ban, pick}.

## Review Focus

1. Equipo sin historial (primer mapa): las variables deben quedar `NaN` y `maps_played = 0`, sin excepción ni división por cero.
2. Intercambiar Team A y Team B debe invertir el signo de toda variable `diff_*` e invertir el objetivo.
3. Mapas sin filas en `overview`/`eco_stats`/`draft_phase`: la fila se conserva con `NaN` en esas variables, no se pierde en un merge.
4. Porcentajes como texto (`"81%"`) y celdas vacías: se convierten a número/`NaN`, no a 0.
5. Claves duplicadas y empates de 2021–2022: se eliminan antes de calcular historial, y el merge con IDs no multiplica filas.

Cada punto tiene su test en la tarea 3 o 5.

## Estructura de archivos

```
config/config.yaml
data/raw/{vct_2021..vct_2026,all_ids}/     (git-ignorado)
data/interim/maps.csv                       (git-ignorado)
data/processed/dataset.csv                  (en git)
docs/variables_y_objetivo.md
models/*.joblib
notebooks/00..06_*.ipynb
reports/figures/*.png   reports/tables/*.csv
src/__init__.py  config.py  plotting.py  data_loading.py  features.py  evaluation.py
tests/test_data_loading.py  tests/test_features.py   (asserts planos, sin pytest)
.gitignore  README.md  requirements.txt
```

---

### Task 1: Estructura, configuración y enlace a GitHub

**Files:**
- Create: `.gitignore`, `README.md`, `requirements.txt`, `config/config.yaml`, `src/__init__.py`, `src/config.py`, `src/plotting.py`, `.gitkeep` en `models/`, `reports/figures/`, `reports/tables/`, `data/processed/`
- Move: `vct_20*/` y `all_ids/` → `data/raw/`

**Interfaces — Produces:**
- `src/config.py`: `ROOT: Path` (raíz del proyecto, `Path(__file__).resolve().parents[1]`); `load_config() -> dict`; constantes `RAW_DIR, INTERIM_DIR, PROCESSED_DIR, MODELS_DIR, FIGURES_DIR, TABLES_DIR: Path`.
- `src/plotting.py`: `set_style() -> None` (tema seaborn común); `save_fig(name: str) -> Path` (guarda la figura actual en `FIGURES_DIR/name.png`, dpi 150, `bbox_inches="tight"`, devuelve la ruta).
- `config/config.yaml`:
  ```yaml
  seed: 42
  years: [2021, 2022, 2023, 2024, 2025, 2026]
  split: {train: [2021, 2022, 2023, 2024], val: [2025], test: [2026]}
  recent_window: 10
  target: team_a_win
  features: []   # la llena el cuadernillo 04
  ```

- [ ] **Step 1:** Crear carpetas y mover los datos crudos a `data/raw/` (`mv`, no copiar). Verificar: `ls data/raw` muestra `all_ids vct_2021 … vct_2026`.
- [ ] **Step 2:** Escribir `.gitignore`: `data/raw/`, `data/interim/`, `__pycache__/`, `.ipynb_checkpoints/`, `.venv/`, `*.jpg`.
- [ ] **Step 3:** Escribir `README.md` mínimo (título, objetivo en una frase, enlace a Kaggle `https://www.kaggle.com/datasets/ryanluong1/valorant-champion-tour-2021-2023-data` e instrucción de descomprimir en `data/raw/`) y `requirements.txt` con las versiones instaladas (`pip freeze` filtrado a: pandas, numpy, scikit-learn, matplotlib, seaborn, joblib, pyyaml, jupyter, nbconvert, ipykernel).
- [ ] **Step 4:** `git init -b main`, `git remote add origin https://github.com/Hullrf/Proyecto_Ciencia_de_Datos_702.git`, commit de `README.md` y `.gitignore`, `git push -u origin main`. Verificar: `gh repo view Hullrf/Proyecto_Ciencia_de_Datos_702 --json isEmpty` → `false`.
- [ ] **Step 5:** `git switch -c feature/modelo-prediccion`.
- [ ] **Step 6:** Escribir `config/config.yaml`, `src/config.py`, `src/plotting.py`. Verificar: `python -c "from src.config import load_config, RAW_DIR; print(load_config()['seed'], RAW_DIR.exists())"` → `42 True`.
- [ ] **Step 7:** Commit (`chore: estructura del proyecto y configuración`) incluyendo spec y plan de `docs/`.

### Task 2: Carga de datos y cuadernillo 00

**Files:**
- Create: `src/data_loading.py`, `notebooks/00_comprension_de_datos.ipynb`
- Produce: `reports/tables/00_inventario_tablas.csv`, `reports/figures/00_mapas_por_anio.png`

**Interfaces — Produces:**
- `MATCH_KEY = ["Tournament", "Stage", "Match Type", "Match Name"]`; `MAP_KEY = MATCH_KEY + ["Map"]`.
- `load_table(relative_path: str, years: list[int] | None = None) -> pd.DataFrame` — lee `data/raw/vct_{year}/{relative_path}` de cada año (por defecto `config.years`), agrega columna `Year`, concatena. Usa `low_memory=False`.

- [ ] **Step 1:** Implementar `load_table`. Verificar: `python -c "from src.data_loading import load_table; d=load_table('matches/maps_scores.csv'); print(len(d), sorted(d.Year.unique()))"` → `27484 [2021, …, 2026]`.
- [ ] **Step 2:** Escribir el cuadernillo 00. Contenido: origen del dataset; inventario de las 20 tablas por año (filas, columnas, tamaño) guardado como tabla; muestra y descripción de las tablas que se usarán (`maps_scores`, `overview`, `eco_stats`, `draft_phase`, `all_ids`); gráfico de mapas por año; identificación de qué tablas describen el *resultado* del mapa (riesgo de fuga) y cuáles son contexto previo. Conclusiones: unidad de análisis = mapa, tablas elegidas, problemas detectados (sin fechas, volumen desigual por año).
- [ ] **Step 3:** Ejecutar con nbconvert; verificar que existen la tabla y la figura.
- [ ] **Step 4:** Commit (`feat: carga de datos y cuadernillo 00`).

### Task 3: Tabla base de mapas y cuadernillo 01

**Files:**
- Modify: `src/data_loading.py`
- Create: `tests/test_data_loading.py`, `notebooks/01_limpieza_y_tabla_base.ipynb`
- Produce: `data/interim/maps.csv`, `reports/tables/01_limpieza_resumen.csv`

**Interfaces — Produces:**
- `clean_maps(scores: pd.DataFrame, ids: pd.DataFrame) -> pd.DataFrame` — función pura. Entrada: `maps_scores` concatenado con `Year`, e `all_matches_games_ids`. Elimina claves `MAP_KEY+Year` duplicadas (en ambas tablas, `keep=False` en `scores`: un duplicado es ambiguo), une por `MAP_KEY+Year`, elimina filas sin `Game ID`/`Match ID`, elimina empates, ordena por `(match_id, game_id)`. Salida, columnas exactas: `game_id, match_id, year, tournament, stage, match_type, match_name, map, team_a, team_b, team_a_score, team_b_score, team_a_win` (`team_a_win` int 0/1; ids int).
- `build_maps_table() -> pd.DataFrame` — carga los crudos y llama a `clean_maps`.

- [ ] **Step 1: Test** en `tests/test_data_loading.py` (asserts planos, ejecutable con `python tests/test_data_loading.py`), con un `scores` sintético de 5 filas: una normal, un par duplicado, un empate, una sin ID. Asserts: resultado tiene 1 fila; `game_id` único; `team_a_win` ∈ {0,1}; columnas == lista exacta de arriba; salida ordenada por `match_id, game_id`.
- [ ] **Step 2:** Ejecutar → falla (`clean_maps` no existe).
- [ ] **Step 3:** Implementar `clean_maps` y `build_maps_table`.
- [ ] **Step 4:** Ejecutar test → pasa.
- [ ] **Step 5:** Cuadernillo 01: unir años; mostrar cada problema con su conteo antes de corregirlo (duplicados, empates, sin ID, por año); validar el supuesto cronológico (rango de `match_id` por año sin solape, gráfico o tabla); normalización de nombres de equipo (espacios; revisar si un mismo equipo aparece con variantes); guardar `data/interim/maps.csv` y la tabla resumen de filas antes/después. Conclusiones con los números reales y la limitación de no tener fechas.
- [ ] **Step 6:** Ejecutar con nbconvert; verificar `data/interim/maps.csv` existe y tiene ~27 300 filas.
- [ ] **Step 7:** Commit (`feat: tabla base de mapas y cuadernillo 01`).

### Task 4: Cuadernillo 02 — análisis exploratorio

**Files:**
- Create: `notebooks/02_analisis_exploratorio.ipynb`
- Produce: figuras `02_*.png`

**Interfaces — Consumes:** `data/interim/maps.csv`, `load_table`, `set_style`, `save_fig`.

- [ ] **Step 1:** Escribir el cuadernillo. Análisis, cada uno con gráfico guardado e interpretación: (a) balance del objetivo global y por año → evidencia del sesgo de posición Team A (58 % en 2021–22); (b) mapas más jugados y su evolución por año; (c) winrate ataque vs defensa por mapa (`agents/maps_stats.csv`, filas distintas de `All Maps`); (d) distribución de marcadores y diferencia de rondas, frecuencia de overtime; (e) mapas jugados por equipo (cola larga: muchos equipos con poco historial); (f) persistencia: ¿el equipo que ganó su mapa anterior gana más el siguiente? (primera señal de que el historial predice). Conclusiones: lista numerada de hallazgos y qué decisión de modelado motiva cada uno (intercambio aleatorio A/B, variable de experiencia, variables por mapa).
- [ ] **Step 2:** Ejecutar con nbconvert; verificar ≥ 6 figuras `02_*.png`.
- [ ] **Step 3:** Commit (`feat: cuadernillo 02 análisis exploratorio`).

### Task 5: Variables históricas y cuadernillo 03

**Files:**
- Create: `src/features.py`, `tests/test_features.py`, `notebooks/03_ingenieria_de_variables.ipynb`
- Produce: `data/processed/dataset.csv`, figuras `03_*.png`

**Interfaces — Consumes:** `maps` (salida de `clean_maps`), `load_table`.

**Interfaces — Produces** (`src/features.py`):
- `to_number(s: pd.Series) -> pd.Series` — quita `%`, convierte a float, vacíos → `NaN`.
- `team_map_stats(maps, overview, eco_stats) -> pd.DataFrame` — tabla larga, 2 filas por mapa (una por equipo): `game_id, match_id, map, team, opponent, won, round_diff, rating, acs, adr, kast, fkd, pistol_won`. Estadísticas de jugadores = media de los jugadores del equipo en ese mapa (`overview`, `Side == "both"`, `Map != "All Maps"`); `pistol_won` de `eco_stats` (`Type == "Pistol Won"`, columna `Won`). Left join: mapa sin datos → `NaN`.
- `build_dataset(maps, overview, eco_stats, draft, window: int, seed: int) -> pd.DataFrame` — una fila por mapa. Columnas: `game_id, match_id, year, map, team_a, team_b, team_a_win` + variables:

  | Columna | Definición (siempre con mapas previos, orden `match_id, game_id`) |
  |---|---|
  | `diff_winrate` | winrate acumulado A − B |
  | `diff_winrate_recent` | winrate en los últimos `window` mapas |
  | `diff_winrate_map` | winrate acumulado en ese mapa |
  | `diff_maps_played` | nº de mapas previos |
  | `diff_maps_played_map` | nº de mapas previos en ese mapa |
  | `diff_round_diff` | media de diferencia de rondas |
  | `diff_rating`, `diff_acs`, `diff_adr`, `diff_kast`, `diff_fkd` | media acumulada del promedio de equipo |
  | `diff_pistol` | media de pistolas ganadas por mapa |
  | `h2h_winrate_a`, `h2h_games` | winrate de A contra B y nº de mapas previos entre ambos |
  | `a_picked_map` | 1 si A eligió el mapa, −1 si B, 0 si decider/desconocido con draft presente, `NaN` sin draft |
  | `min_maps_played` | mínimo de mapas previos entre A y B (evidencia disponible) |

  Mecánica: sobre la tabla larga, `groupby("team")` + `shift(1)` + `expanding()/rolling(window)`; así el mapa actual nunca entra. Sin historial → `NaN` (los conteos → 0). Al final, con `np.random.default_rng(seed)`, intercambiar A y B en la mitad de las filas: se intercambian `team_a/team_b`, se niegan `diff_*` y `a_picked_map`, `h2h_winrate_a → 1 − h2h_winrate_a`, `team_a_win → 1 − team_a_win`.
  `# ponytail:` el historial es por nombre de equipo e ignora cambios de plantilla; mejora posible: historial por jugador.

- [ ] **Step 1: Tests** en `tests/test_features.py` (asserts planos) con `maps` sintético de 3 equipos y ~8 mapas, `overview`/`eco_stats`/`draft` mínimos (uno de los mapas sin filas en ellos), `seed` fijo:
  - `test_no_leakage`: invertir el resultado y marcador del último mapa no cambia ninguna variable de esa fila (solo `team_a_win`).
  - `test_future_does_not_affect_past`: quitar los 2 últimos mapas no cambia las variables de los anteriores.
  - `test_first_map_has_no_history`: en el primer mapa `min_maps_played == 0` y `diff_winrate` es `NaN`.
  - `test_swap_symmetry`: construir con `maps` y con `maps` con A/B (nombres y marcadores) intercambiados de entrada, mismo `seed` → por `game_id`, `diff_*` de uno == −`diff_*` del otro y `team_a_win` complementario.
  - `test_missing_side_tables_keep_row`: nº de filas de salida == nº de mapas; el mapa sin `overview` influye con `NaN`, no desaparece.
  - `test_to_number`: `to_number(pd.Series(["81%", "", None, "1.5"]))` → `[81.0, NaN, NaN, 1.5]`.
- [ ] **Step 2:** Ejecutar → fallan.
- [ ] **Step 3:** Implementar `src/features.py`.
- [ ] **Step 4:** Ejecutar `python tests/test_features.py` → pasan.
- [ ] **Step 5:** Cuadernillo 03: explicar el problema de la fuga con un ejemplo (correlación de kills del mismo mapa con el resultado); construir la tabla larga; construir el dataset; **demostración sobre un mapa real** (elegir un partido conocido, mostrar los mapas previos del equipo y que la variable coincide con el cálculo a mano); porcentaje de nulos por variable y por año; explicar el intercambio aleatorio A/B y verificar que el objetivo queda ~50 %; guardar `data/processed/dataset.csv`. Conclusiones: variables creadas, cobertura, decisiones sobre nulos.
- [ ] **Step 6:** Ejecutar con nbconvert; verificar `dataset.csv` (mismo nº de filas que `maps.csv`, media de `team_a_win` entre 0.48 y 0.52).
- [ ] **Step 7:** Commit (`feat: variables históricas sin fuga y cuadernillo 03`) incluyendo `data/processed/dataset.csv`.

### Task 6: Cuadernillo 04 — selección de variables

**Files:**
- Create: `src/evaluation.py` (solo `temporal_split`), `notebooks/04_seleccion_de_variables.ipynb`
- Modify: `config/config.yaml` (`features`)
- Produce: figuras `04_*.png`, `reports/tables/04_variables.csv`

**Interfaces — Produces:**
- `temporal_split(df: pd.DataFrame, split: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]` — filtra por `year` según `config.split`; devuelve `(train, val, test)`.

- [ ] **Step 1:** Implementar `temporal_split`. Verificar con el dataset real: los años de cada parte son exactamente los de `config.split` y las tres partes suman el total.
- [ ] **Step 2:** Cuadernillo 04, **usando solo `train`** (decirlo explícitamente y por qué): distribución de cada variable según el objetivo; correlación de cada variable con el objetivo y AUC univariado; mapa de calor de correlación entre variables (redundancia, p. ej. `rating`/`acs`/`adr`); cobertura (nulos); información mutua o importancia por permutación de un modelo rápido. Decidir el conjunto final con una tabla `variable · decisión · motivo` guardada en `reports/tables/04_variables.csv`, y escribir la lista en `config.yaml → features`. Conclusiones.
- [ ] **Step 3:** Ejecutar con nbconvert; verificar `python -c "from src.config import load_config; print(len(load_config()['features']) > 0)"` → `True`.
- [ ] **Step 4:** Commit (`feat: selección de variables y cuadernillo 04`).

### Task 7: Cuadernillo 05 — modelado y comparación

**Files:**
- Modify: `src/evaluation.py`
- Create: `notebooks/05_modelado_y_comparacion.ipynb`
- Produce: `models/logistic_regression.joblib`, `models/random_forest.joblib`, `models/hist_gradient_boosting.joblib`, `reports/tables/05_comparacion_modelos.csv`, figuras `05_*.png`

**Interfaces — Produces:**
- `evaluate(y_true, y_proba) -> dict` con claves `accuracy` (umbral 0.5), `roc_auc`, `log_loss`.

- [ ] **Step 1:** Implementar `evaluate`. Verificar: `evaluate([0,1,1,0],[0.1,0.9,0.8,0.3])` → `accuracy == 1.0`, `roc_auc == 1.0`.
- [ ] **Step 2:** Cuadernillo 05. Entrenar en `train`, evaluar en `val`:
  - Líneas base: clase mayoritaria; regla "gana quien tiene `diff_winrate > 0`" (empate/`NaN` → 0.5).
  - Regresión logística: `Pipeline(SimpleImputer(median, add_indicator=True) → StandardScaler → LogisticRegression)`.
  - Random Forest: `Pipeline(SimpleImputer(median, add_indicator=True) → RandomForestClassifier(n_estimators=300, min_samples_leaf=20, random_state=42, n_jobs=-1))`.
  - `HistGradientBoostingClassifier(random_state=42)` (nulos nativos).
  - `map` como variable categórica solo si el cuadernillo 04 la dejó en `features` (one-hot / `categorical_features`).
  Antes de cada modelo, una celda de texto que **argumente por qué se prueba** (qué supone, qué ventaja y qué límite tiene para estos datos). Tabla comparativa (accuracy, ROC-AUC, log loss) guardada; gráfico de barras; curvas ROC superpuestas. Guardar los tres modelos con `joblib.dump(..., compress=3)`. Conclusiones: cuál gana, por cuánto frente a las líneas base, y cuál pasa al ajuste (criterio: menor log loss en validación; ante empate técnico, el más simple).
- [ ] **Step 3:** Ejecutar con nbconvert; verificar los 3 `.joblib` (< 50 MB cada uno) y la tabla.
- [ ] **Step 4:** Commit (`feat: comparación de modelos y cuadernillo 05`).

### Task 8: Cuadernillo 06 — ajuste y evaluación final

**Files:**
- Create: `notebooks/06_ajuste_y_evaluacion_final.ipynb`
- Produce: `models/final_model.joblib`, `reports/tables/06_resultados_finales.csv`, figuras `06_*.png`

- [ ] **Step 1:** Escribir el cuadernillo: ajuste del modelo elegido con `RandomizedSearchCV` (`cv=TimeSeriesSplit(n_splits=5)`, `scoring="neg_log_loss"`, `random_state=42`) sobre `train+val` ordenado por `match_id, game_id`; reentrenar con los mejores hiperparámetros en `train+val`; **única evaluación en `test` (2026)** junto a las dos líneas base en el mismo conjunto; matriz de confusión; curva ROC; curva de calibración; importancia por permutación en `test`; análisis de errores (acierto según `min_maps_played` y según confianza de la predicción). Guardar `final_model.joblib`. Conclusiones del cuadernillo y del proyecto: resultado frente a líneas base, qué variables pesan, limitaciones (sin fechas, historial por nombre de equipo, 2021–22 con torneos menores, 2026 parcial) y mejoras posibles.
- [ ] **Step 2:** Ejecutar con nbconvert; verificar `final_model.joblib` y que `joblib.load` + `predict_proba` sobre 5 filas de `dataset.csv` funciona.
- [ ] **Step 3:** Commit (`feat: ajuste, evaluación final y cuadernillo 06`).

### Task 9: Documento de variables, README y PR

**Files:**
- Create: `docs/variables_y_objetivo.md`
- Modify: `README.md`

- [ ] **Step 1:** Escribir `docs/variables_y_objetivo.md` con los resultados reales de los cuadernillos 03–06: objetivo final; definición de la variable objetivo; tabla `variable · qué mide · archivo de origen · por qué debería predecir`; variables descartadas y motivo (fuga, baja cobertura, redundancia); limitaciones.
- [ ] **Step 2:** Completar `README.md`: objetivo, árbol de carpetas, cómo obtener los datos, cómo ejecutar (`pip install -r requirements.txt`, orden de cuadernillos, `python tests/test_features.py`), tabla de cuadernillos, resumen de modelos y por qué, resultados principales, enlace al documento de variables.
- [ ] **Step 3:** Verificación completa desde limpio: ejecutar los 2 tests y los 7 cuadernillos en orden con nbconvert; todo sin error. `git status` no muestra nada de `data/raw/`.
- [ ] **Step 4:** Commit (`docs: documento de variables y README`), `git push -u origin feature/modelo-prediccion`, `gh pr create` hacia `main` con resumen y resultados. No mergear.
