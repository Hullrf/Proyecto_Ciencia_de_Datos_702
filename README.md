# Predicción del ganador de un mapa en Valorant Champions Tour

Proyecto del curso Ciencia de Datos (grupo 702). El objetivo es predecir qué equipo gana
un mapa de VCT **antes de que se juegue**, usando solo el historial previo de ambos equipos.

El proyecto está organizado como un recorrido en nueve cuadernillos: cada uno tiene un
objetivo, muestra el paso a paso y cierra con conclusiones que motivan el siguiente. Cada
modelo tiene su propio cuadernillo, y cada gráfico va acompañado de por qué se eligió, cómo
se lee y qué muestra.

## Resultado principal

Evaluación sobre 886 mapas de 2026, que no se usaron en ninguna decisión del proyecto:

| Modelo | Exactitud | ROC-AUC | Log loss |
|---|---|---|---|
| Clase mayoritaria | 0.497 | 0.500 | 0.693 |
| Regla "gana el de mejor winrate" | 0.560 | — | — |
| Logística con una variable | 0.547 | 0.587 | 0.680 |
| **Modelo final (Gradient Boosting)** | **0.571** | **0.606** | **0.680** |

El modelo acierta el 57.1 % de los mapas (IC 95 %: 53.9 %–60.4 %). Es mejor que el azar y
algo mejor que las reglas simples en exactitud, aunque dentro del margen de error; en calidad
de probabilidades empata con una logística de una sola variable. Predecir un mapa entre
equipos profesionales con estadísticas históricas da una ventaja real pero modesta.

## Estructura

```
├── config/config.yaml        Rutas, semilla, partición por años, variables y umbral de historial
├── data/
│   ├── raw/                  Dataset original (no está en el repositorio)
│   ├── interim/              Tabla base de mapas (se genera con el cuadernillo 01)
│   └── processed/            Dataset de modelado
├── docs/
│   ├── Explicacion_del_codigo.docx   Por qué y cómo funciona cada fragmento de código
│   ├── explicacion_del_codigo.md     Misma explicación en Markdown
│   └── variables_y_objetivo.md       Objetivo final y justificación de cada variable
├── models/                   Cuadernillos de los modelos (05 a 07)
├── notebooks/                Cuadernillos 00 a 04 y 08
├── reports/
│   ├── figures/              Todos los gráficos generados
│   └── tables/               Tablas de resultados
├── src/                      Funciones compartidas por los cuadernillos
├── tests/                    Pruebas (incluye las pruebas anti-fuga de datos)
└── requirements.txt
```

## Cuadernillos

| Cuadernillo | Objetivo | Conclusión principal |
|---|---|---|
| `00_comprension_de_datos` | Inventario del dataset y elección de tablas | La unidad de análisis es el mapa; casi todas las tablas describen el resultado y solo sirven como historial |
| `01_limpieza_y_tabla_base` | Unir años, limpiar y ordenar en el tiempo | Los IDs no ordenan los partidos dentro de una etapa: el historial solo puede usar etapas anteriores |
| `02_analisis_exploratorio` | Entender el objetivo y sus posibles predictores | Team A gana más por cómo la web ordena los equipos; el winrate previo sí predice |
| `03_ingenieria_de_variables` | Construir variables históricas sin fuga de datos | Las estadísticas del propio mapa "aciertan" el 94 %; las históricas dan una señal real pero pequeña |
| `04_seleccion_de_variables` | Separar los datos por año y decidir las variables | Entrenamiento 2021–2024, validación 2025, prueba 2026; 11 de 16 variables |
| `models/05_modelo_regresion_logistica` | Primer modelo y cómo se mide | Entrenar con partidos no comparables arruina las probabilidades; se entrena con mapas entre equipos con 30+ mapas previos |
| `models/06_modelo_random_forest` | Segundo modelo | Captar relaciones complejas no mejora a la logística |
| `models/07_modelo_gradient_boosting` | Tercer modelo | La curva de log loss muestra el sobreajuste; la configuración importa más que el modelo |
| `08_comparacion_y_evaluacion_final` | Comparar, ajustar y evaluar en 2026 | 57.1 % de exactitud en prueba; conclusiones y limitaciones del proyecto |

## Modelos y por qué se usaron

Se compararon tres modelos de familias distintas, de menor a mayor complejidad, contra tres
líneas base (clase mayoritaria, regla del winrate y logística de una variable):

- **Regresión logística** (cuadernillo 05): el punto de partida natural para clasificación
  binaria. Es interpretable y difícil de sobreajustar con pocos datos. Su límite es que no
  capta interacciones ni relaciones no lineales.
- **Random Forest** (cuadernillo 06): promedia cientos de árboles, capta no linealidades e
  interacciones y es robusto sin apenas ajuste. Es menos interpretable.
- **Gradient Boosting** (cuadernillo 07): suele ser la mejor familia en datos tabulares y
  maneja los valores faltantes de forma nativa, algo importante aquí porque "no hay
  historial" tiene significado propio. Es el más sensible a su configuración.

El criterio de selección, fijado antes de comparar, fue el menor *log loss* en validación
(2025): interesa que las probabilidades sean confiables, no solo acertar el ganador. Ganó
Gradient Boosting, que después se ajustó con validación cruzada temporal (cuadernillo 08).

Los modelos no se guardan como archivos: cada cuadernillo los entrena de nuevo y, con la
misma semilla, produce siempre el mismo modelo.

## Decisiones que protegen la validez del resultado

- **Sin fuga de datos:** toda variable se calcula solo con mapas de etapas anteriores.
  `tests/test_features.py` lo verifica automáticamente.
- **Partición temporal:** entrenamiento 2021–2024, validación 2025, prueba 2026. Nunca al azar.
- **Posición neutralizada:** Team A y Team B se intercambian al azar en la mitad de las filas.
- **El conjunto de prueba se usó una sola vez**, al final, y los resultados se reportan con
  su intervalo de confianza.

## Datos

Dataset de Kaggle (extraído de vlr.gg):
https://www.kaggle.com/datasets/ryanluong1/valorant-champion-tour-2021-2023-data

Pesa 1.3 GB, por eso no está en el repositorio. Para reproducir el proyecto desde cero,
descárgalo y descomprímelo en `data/raw/`, de modo que queden `data/raw/vct_2021/`, …,
`data/raw/vct_2026/` y `data/raw/all_ids/`.

El dataset de modelado ya procesado (`data/processed/dataset.csv`) sí está en el repositorio,
así que los cuadernillos 04 a 08 se pueden ejecutar sin descargar nada.

## Cómo ejecutar

```bash
pip install -r requirements.txt

# pruebas
python tests/test_data_loading.py
python tests/test_features.py

# cuadernillos, en orden: 00 a 04 en notebooks/, 05 a 07 en models/, 08 en notebooks/
cd notebooks
python -m nbconvert --to notebook --execute --inplace 00_comprension_de_datos.ipynb
# … hasta 04_seleccion_de_variables.ipynb; luego, desde models/, 05 a 07;
# y por último, desde notebooks/, 08_comparacion_y_evaluacion_final.ipynb
```

También se pueden abrir y ejecutar directamente en Jupyter o en PyCharm. Los cuadernillos
00 a 03 necesitan los datos crudos en `data/raw/`. El cuadernillo 08 lee los resultados que
guardan el 05, el 06 y el 07, así que hay que ejecutarlos antes.

## Documentación

- [Explicación del código](docs/Explicacion_del_codigo.docx) — por qué y cómo funciona cada
  celda y cada función, cómo se separaron los datos, qué es la curva de log loss y por qué se
  usan intervalos de confianza ([versión Markdown](docs/explicacion_del_codigo.md)).
- [Objetivo y justificación de las variables](docs/variables_y_objetivo.md)

## Limitaciones y posibles mejoras

El dataset no trae fechas, el historial se agrupa por nombre de equipo (no reacciona a cambios
de plantilla) y la temporada 2026 es parcial. Las mejoras más prometedoras son construir el
historial por jugador, dar más peso a los mapas recientes y conseguir las fechas reales de los
partidos. El detalle está en las conclusiones del cuadernillo 08.
