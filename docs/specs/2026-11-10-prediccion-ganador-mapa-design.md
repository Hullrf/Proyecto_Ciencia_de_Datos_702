# Diseño: predicción del ganador de un mapa en VCT (Valorant)

Fecha: 2026-11-10 · Repositorio: https://github.com/Hullrf/Proyecto_Ciencia_de_Datos_702

## 1. Intención

Proyecto del curso Ciencia de Datos (S7). El profesor pide un modelo de predicción sobre un
dataset de libre elección. Se eligió el dataset de Valorant Champions Tour (Kaggle,
`ryanluong1/valorant-champion-tour-2021-2023-data`, scrapeado de vlr.gg, años 2021–2026).

Lo que se evalúa no es solo el modelo: es que en cada cuadernillo se vea el análisis que llevó
a cada decisión. El proyecto tiene que leerse como un recorrido, de los datos crudos al modelo final.

## 2. Objetivo de predicción (decidido por el usuario)

Predecir **qué equipo gana un mapa** antes de que se juegue.

- Unidad de análisis: un mapa jugado (una fila de `matches/maps_scores.csv`), ~26 000 filas.
- Variable objetivo: `team_a_win` (1 si `Team A Score` > `Team B Score`, 0 si no). Binaria, sin empates.

## 3. Metas, no-metas y anti-metas

**Metas**
- Cuadernillos numerados, en español, cada uno con: objetivo, paso a paso comentado y conclusiones.
- Funciones compartidas en `src/` (archivos `.py`), importadas desde los cuadernillos.
- Todos los gráficos guardados en `reports/figures/`; tablas de resultados en `reports/tables/`.
- Modelos entrenados guardados en `models/`.
- Argumentar por qué se usa cada modelo.
- Documento `docs/variables_y_objetivo.md`: objetivo final y justificación de cada variable.
- Proyecto enlazado al repositorio de GitHub.

**No-metas:** despliegue, API, aplicación web, deep learning, scraping de datos nuevos,
predicción en vivo durante la partida.

**Anti-metas (harían fracasar el proyecto aunque "funcione")**
- **Fuga de datos:** usar estadísticas del mismo mapa que se predice (kills, rating, economía
  de ese mapa). Daría ~95 % de acierto sin valor. Toda variable se calcula solo con mapas anteriores.
- Partición aleatoria de entrenamiento/prueba: mezclaría futuro con pasado. La partición es temporal.
- Cuadernillos que solo son código sin explicación ni conclusiones.
- Vender una precisión inflada. Lo esperable en e-sports es 60–65 %; se reporta lo que salga,
  comparado contra líneas base.

## 4. Restricciones

- Python 3.11 ya instalado con pandas, numpy, scikit-learn, matplotlib, seaborn, joblib, pyyaml,
  jupyter. No se agregan dependencias fuera de esas.
- Texto de los cuadernillos y documentos en español; el código (nombres de variables,
  funciones, columnas derivadas) en inglés.
- El dataset crudo pesa 1.3 GB y tiene archivos de más de 100 MB: **no se sube a GitHub**.
  Queda en `data/raw/` ignorado por git; el README explica cómo descargarlo de Kaggle.
- Los CSV no traen fecha. El orden cronológico se aproxima con `Match ID` y `Game ID` de
  `all_ids/all_matches_games_ids.csv` (los IDs de vlr.gg crecen con el tiempo). Es una
  limitación que se documenta y se verifica en el cuadernillo 01 (los IDs deben ser
  coherentes con el año).

## 5. Estructura de carpetas (decisión del constructor; el usuario dio libertad)

```
Proyecto/
├── config/
│   └── config.yaml            # rutas, semilla, años de corte, ventanas de historial
├── data/
│   ├── raw/                   # vct_2021 … vct_2026, all_ids  (ignorado por git)
│   ├── interim/               # tabla base de mapas limpia   (ignorado por git si es grande)
│   └── processed/             # dataset final de modelado    (sí va al repo, es pequeño)
├── docs/
│   ├── variables_y_objetivo.md
│   └── specs/                 # este documento
├── models/                    # modelos entrenados (.joblib)
├── notebooks/                 # 00_… a 06_…
├── reports/
│   ├── figures/               # todos los gráficos (.png)
│   └── tables/                # tablas de resultados (.csv)
├── src/                       # funciones compartidas
├── .gitignore
├── README.md
└── requirements.txt
```

Los CSV actuales (`vct_*`, `all_ids`) se mueven a `data/raw/`. La imagen de ejemplo no se
sube al repo. No se crea `.env` (no hay secretos).

## 6. Cuadernillos

Cada uno abre con **Objetivo**, desarrolla con celdas de texto antes de cada bloque de código,
y cierra con **Conclusiones** que conectan con el siguiente. Se entregan ejecutados, con salidas.

| Archivo | Objetivo | Produce |
|---|---|---|
| `00_comprension_de_datos.ipynb` | Inventario del dataset: qué tablas hay, qué contiene cada una, volumen por año, cuáles sirven para el objetivo. | tabla resumen en `reports/tables/` |
| `01_limpieza_y_tabla_base.ipynb` | Unir todos los años, asignar IDs, validar el orden cronológico, limpiar (nulos, duplicados, tipos, nombres de equipo) y construir la tabla base de mapas con el objetivo. | `data/interim/maps.csv` |
| `02_analisis_exploratorio.ipynb` | Entender el objetivo y sus posibles predictores: balance de clases, sesgo de posición Team A/B, mapas, lados ataque/defensa, distribución de marcadores, actividad por equipo. | figuras |
| `03_ingenieria_de_variables.ipynb` | Construir variables históricas sin fuga y mostrar, con un ejemplo concreto, que cada fila solo usa información previa. | `data/processed/dataset.csv` |
| `04_seleccion_de_variables.ipynb` | Analizar relación de cada variable con el objetivo, correlación entre variables, redundancia; decidir el conjunto final. | figuras, lista final en `config` |
| `05_modelado_y_comparacion.ipynb` | Entrenar y comparar líneas base y modelos candidatos con validación temporal; argumentar cada modelo. | tabla comparativa, modelos en `models/` |
| `06_ajuste_y_evaluacion_final.ipynb` | Ajustar hiperparámetros del mejor modelo, evaluarlo una sola vez en el conjunto de prueba, interpretar (importancia de variables, calibración, errores) y cerrar con conclusiones y limitaciones del proyecto. | `models/final_model.joblib`, figuras |

## 7. Variables (todas históricas, calculadas con mapas anteriores al que se predice)

Por equipo, y luego expresadas como **diferencia Team A − Team B**:

- Forma: winrate global en los últimos N mapas; número de mapas jugados (experiencia).
- Winrate histórico en ese mapa específico.
- Nivel de jugadores: promedio previo de Rating, ACS, ADR, KAST (`overview.csv`, filas `Side = both`).
- Duelos de apertura: First Kills − First Deaths previos.
- Diferencia promedio de rondas (margen con que gana o pierde).
- Economía: winrate histórico en rondas de pistola (`eco_stats.csv`), si la cobertura de datos lo permite.
- Enfrentamientos directos previos entre ambos equipos.
- Contexto conocido antes de jugar: mapa, y quién eligió el mapa (`draft_phase.csv`), si la cobertura lo permite.

Equipos sin historial: las variables quedan nulas o con un valor neutro, y se incluye el conteo
de mapas previos para que el modelo sepa cuánta evidencia hay. El cuadernillo 03 decide y
justifica el tratamiento. Las variables marcadas "si la cobertura lo permite" se descartan con
explicación si faltan en demasiados años.

**Sesgo de posición:** si el cuadernillo 02 muestra que Team A gana bastante más del 50 %
(vlr.gg suele listar primero al favorito), se intercambian A y B al azar en la mitad de las
filas (con semilla fija) para que el modelo no aprenda la posición.

## 8. Modelado (decisión del constructor; el usuario dijo "lo que consideres mejor")

- **Partición temporal:** entrenamiento = años antiguos, validación = año siguiente,
  prueba = el o los años más recientes con datos suficientes. Los cortes exactos se fijan en
  el cuadernillo 01 al ver el volumen real por año (2026 puede estar incompleto) y quedan en `config.yaml`.
- **Líneas base:** (a) clase mayoritaria; (b) "gana el equipo con mejor winrate histórico".
  Un modelo que no las supere no aporta nada.
- **Candidatos, todos de scikit-learn:**
  - Regresión logística: simple, interpretable, bien calibrada; referencia lineal.
  - Random Forest: capta no linealidades e interacciones, robusto, poco ajuste.
  - Gradient Boosting (`HistGradientBoostingClassifier`): suele ser el mejor en datos
    tabulares y maneja nulos de forma nativa.
- **Métricas:** accuracy, ROC-AUC y log loss (importa la calidad de la probabilidad, no solo el acierto).
- **Ajuste:** búsqueda de hiperparámetros con `TimeSeriesSplit` sobre entrenamiento+validación.
  El conjunto de prueba se usa una sola vez, al final.
- La argumentación de cada modelo va escrita en el cuadernillo 05 y resumida en el README.

## 9. Código compartido (`src/`)

Módulos pequeños, solo lo que se use en más de un cuadernillo:

- `config.py` — carga `config.yaml` y expone rutas.
- `data_loading.py` — leer y unir un CSV de todos los años.
- `features.py` — construcción de variables históricas.
- `plotting.py` — estilo común y `save_fig()` que guarda en `reports/figures/`.
- `evaluation.py` — partición temporal y cálculo de métricas.

Una comprobación automática mínima: un test que verifique que las variables de un mapa no
cambian si se alteran los resultados de ese mapa o de mapas posteriores (prueba anti-fuga).

## 10. Documento `docs/variables_y_objetivo.md`

Contiene: objetivo final del proyecto, definición de la variable objetivo, tabla de variables
usadas (qué es, de qué archivo sale, por qué debería predecir), variables descartadas y por qué
(fuga de datos, baja cobertura), y limitaciones. Se escribe al final para que refleje lo que
realmente quedó tras los cuadernillos 03 y 04.

## 11. Git y GitHub

- `git init` en `Proyecto/`, remoto `origin` = repositorio del curso (hoy vacío).
- Primer commit en `main` con la base mínima (`README.md`, `.gitignore`) — **requiere permiso
  del usuario**, porque es un push directo a la rama principal.
- El resto del trabajo en una rama `feature/modelo-prediccion`, con commits por cuadernillo,
  push de la rama y PR. El merge lo hace el usuario.

## 12. Queda a criterio del constructor

Ventanas de historial (N), tratamiento exacto de nulos, hiperparámetros, estilo de gráficos,
cómo se generan y ejecutan los `.ipynb`, y recortar variables que los datos no soporten
(explicándolo en el cuadernillo correspondiente).
