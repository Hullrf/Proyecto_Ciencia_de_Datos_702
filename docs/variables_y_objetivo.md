# Objetivo del proyecto y justificación de las variables

## 1. Objetivo final

**Predecir qué equipo gana un mapa de Valorant Champions Tour (VCT) antes de que se juegue**,
usando únicamente información disponible antes del inicio del mapa.

El modelo recibe la descripción de un enfrentamiento (dos equipos y un mapa) y devuelve la
probabilidad de que gane cada equipo. El valor del proyecto está tanto en el modelo como en el
recorrido: mostrar, paso a paso, cómo se llega de un conjunto de tablas crudas a una predicción
evaluada de forma honesta.

### Por qué el ganador del mapa y no otra cosa

| Alternativa | Por qué no se eligió |
|---|---|
| Ganador de la serie (partido completo) | Menos observaciones (una por serie en lugar de una por mapa) y se pierde el efecto del mapa concreto. |
| Ganador de cada ronda | Muchísimas filas, pero es un problema distinto (economía de la ronda) y menos interesante como predicción previa al partido. |
| Rating de un jugador | Es regresión sobre una fórmula propia de vlr.gg; menos interpretable como resultado. |
| **Ganador del mapa** | **27 368 observaciones, objetivo binario sin empates, y el mapa aporta información propia.** |

## 2. Variable objetivo

`team_a_win` — vale 1 si el equipo listado como Team A gana el mapa, 0 si gana Team B.

- Se deriva del marcador en `matches/maps_scores.csv` (`Team A Score` > `Team B Score`).
- No hay empates: se eliminaron los 17 mapas con marcador empatado y los 4 incompletos, que
  son errores de registro.
- **Balance:** en los datos originales Team A gana el 57.3 % de los mapas, porque la web lista
  primero al favorito. Para que el modelo no aprenda la posición, Team A y Team B se
  intercambian al azar en la mitad de las filas; el objetivo queda en 50.1 %.

## 3. El principio que gobierna todas las variables

> Una variable solo puede usar información que existía **antes** del mapa que se predice.

Casi todo el dataset describe lo que pasó *durante* cada mapa (kills, rating, economía).
Usarlo directamente sería **fuga de datos**: la diferencia de ACS del propio mapa "predice" al
ganador con 93.6 % de acierto, porque es una consecuencia del resultado.

Por eso todas las variables son **históricas**: resumen lo que cada equipo hizo en mapas
anteriores. Y como el dataset no trae fechas y los IDs de vlr.gg no ordenan los partidos
dentro de una misma etapa (en los *playoffs* de Champions 2024, la Gran Final tiene un ID menor
que la llave inferior), el historial se restringe aún más: **solo mapas de etapas anteriores**
a la del mapa que se predice.

Las variables de rendimiento se expresan como **diferencia Team A − Team B**: lo que importa
no es qué tan bueno es un equipo en abstracto, sino comparado con su rival.

## 4. Variables utilizadas (11)

| Variable | Qué mide | Origen | Por qué debería predecir |
|---|---|---|---|
| `diff_winrate` | Diferencia en la proporción de mapas ganados en todo el historial | `maps_scores` | Es la medida más directa de la fuerza de un equipo. En el análisis exploratorio, la probabilidad de ganar sube de 33 % a 77 % a medida que crece esta diferencia. Es la variable más importante del modelo final. |
| `diff_winrate_recent` | Diferencia de winrate en los últimos 10 mapas | `maps_scores` | Capta el momento del equipo (rachas, cambios recientes) que el promedio histórico diluye. |
| `diff_winrate_map` | Diferencia de winrate en el mapa concreto que se juega | `maps_scores` | Los equipos tienen mapas fuertes y débiles; es la única variable específica del mapa. |
| `diff_maps_played` | Diferencia en el número de mapas jugados | `maps_scores` | Mide experiencia. Los equipos que acumulan más mapas son los que avanzan en los torneos y se mantienen en el circuito. Fue la variable con mayor AUC univariado (0.651). |
| `diff_round_diff` | Diferencia en el margen promedio de rondas | `maps_scores` | Distingue entre ganar 13–2 y ganar 13–11: dice *con cuánta* ventaja gana un equipo, no solo si gana. Mayor correlación con el objetivo (0.27). |
| `diff_acs` | Diferencia en el ACS promedio histórico de los jugadores | `overview` | El ACS (puntaje de combate) resume el nivel individual: daño, bajas y multi-kills. |
| `diff_kast` | Diferencia en el KAST promedio histórico | `overview` | Porcentaje de rondas en que un jugador aporta (baja, asistencia, sobrevive o es vengado). Mide consistencia y juego en equipo. Segunda variable más importante del modelo final. |
| `diff_fkd` | Diferencia en duelos de apertura (primeras bajas − primeras muertes) | `overview` | Ganar el primer duelo de la ronda da ventaja numérica; es un aspecto táctico distinto del nivel general. |
| `h2h_winrate_a` | Proporción de mapas que Team A le ha ganado a Team B | `maps_scores` | Recoge cruces de estilos: hay equipos que rinden sistemáticamente mejor o peor contra un rival concreto. |
| `a_picked_map` | 1 si Team A eligió el mapa, −1 si lo eligió Team B, 0 si es el mapa decisivo | `draft_phase` | Los equipos eligen sus mejores mapas. Es la única variable que no depende del historial y se conoce antes de jugar. Quien elige gana cerca del 51.5 %. |
| `min_maps_played` | Mapas previos del equipo con menos historial | `maps_scores` | No dice quién gana, sino cuánta evidencia respalda a las demás variables: un winrate calculado con 3 mapas vale menos que uno con 200. |

Las estadísticas de jugadores se promedian por equipo en cada mapa (cinco jugadores, filas
`Side = both`) y luego se promedian sobre el historial del equipo.

## 5. Variables descartadas

### Por redundancia (cuadernillo 04)

| Variable | Motivo |
|---|---|
| `diff_rating` | Correlación de 0.95 con `diff_kast`. El *rating* es una fórmula de vlr.gg que ya incorpora el KAST; se prefiere la estadística directa. |
| `diff_adr` | Correlación de 0.94 con `diff_acs` (el ACS se calcula sobre todo a partir del daño), con menos señal y más faltantes. |
| `diff_maps_played_map` | Correlación de 0.77 con `diff_maps_played` y menor AUC. |

### Por falta de señal (cuadernillo 04)

| Variable | Motivo |
|---|---|
| `diff_pistol` | AUC univariado de 0.57, 55 % de valores faltantes y sin aporte dentro de un modelo. |
| `h2h_games` | AUC de 0.50. Que `h2h_winrate_a` esté vacía ya indica que no hay enfrentamientos previos. |

Quitar estas cinco variables no empeoró la predicción (AUC en 2024: 0.599 con 11 variables
frente a 0.586–0.596 con 16).

### Por fuga de datos (nunca se consideraron como variables)

| Información | Motivo |
|---|---|
| Kills, rating, ACS, economía, etc. **del mapa que se predice** | Solo existen cuando el mapa terminó. |
| `players_stats`, `agents_pick_rates`, `teams_picked_agents` | Son agregados por torneo o etapa que mezclan partidos anteriores y posteriores al que se predice. |
| Marcadores por lado y duración del mapa | Son parte del resultado. |

### Por decisión de análisis (cuadernillo 02)

| Información | Motivo |
|---|---|
| Posición del equipo (ser Team A o Team B) | Depende de cómo la web ordena los equipos; se neutralizó con el intercambio aleatorio. |
| Nombre del mapa | La rotación cambia cada año: hay mapas en el conjunto de prueba que casi no existen en el entrenamiento. Se usa el rendimiento del equipo *en* el mapa. |
| Lado inicial (ataque/defensa) | El ataque gana entre 50 % y 51.5 % de las rondas en todos los mapas y ambos equipos juegan los dos lados. |

## 6. Valores faltantes

Una variable queda vacía cuando no hay con qué calcularla (equipos sin etapas previas,
estadísticas no registradas, partidos sin datos de vetos). Los faltantes **no se rellenan en
el dataset**, porque "no hay información" es distinto de "la diferencia es cero":

- El modelo final (Gradient Boosting) los maneja de forma nativa.
- La regresión logística y el Random Forest usan la mediana más un indicador de "dato faltante".

## 7. Qué se logró con estas variables

Evaluación sobre 886 mapas de 2026, que no se usaron en ninguna decisión del proyecto:

| Modelo | Exactitud | ROC-AUC | Log loss |
|---|---|---|---|
| Clase mayoritaria | 0.497 | 0.500 | 0.693 |
| Regla "gana el de mejor winrate" | 0.560 | — | — |
| Logística con una variable (`diff_winrate`) | 0.547 | 0.587 | 0.680 |
| **Modelo final (Gradient Boosting, 11 variables)** | **0.571** | **0.606** | **0.680** |

El modelo acierta el 57.1 % de los mapas (IC 95 %: 54.0 %–60.4 %): mejor que el azar y algo
mejor que las reglas simples en exactitud, aunque en calidad de probabilidades empata con una
logística de una sola variable. La señal previa al partido existe, pero es modesta y está
concentrada en la fuerza general del equipo; las demás variables agregan poco sobre ella.

## 8. Limitaciones de las variables

- **Historial por nombre de equipo:** no reacciona a cambios de plantilla. Un equipo que
  renueva sus jugadores conserva su historial; uno que cambia de nombre lo pierde.
- **Promedios de toda la historia:** un mapa de 2021 pesa lo mismo que uno del mes pasado
  (salvo en `diff_winrate_recent`).
- **Sin información dentro de la etapa:** por la falta de fechas, los resultados de la etapa
  en curso no entran al historial.
- **Sin composición de agentes**, que se conoce justo antes del mapa y podría aportar.

Un ensayo informal con un rating tipo Elo actualizado por etapas dio un AUC similar (≈ 0.60
en 2024–2026), lo que sugiere que el techo viene más de lo impredecible del juego que de la
elección de variables. No forma parte de los cuadernillos.
