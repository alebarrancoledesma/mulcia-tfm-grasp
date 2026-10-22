# CVRP con GRASP

Experimento pequeño de GRASP para el problema de rutas de vehículos con capacidad (CVRP).

## Problema

- **Objetivo**: minimizar la distancia total de las rutas.
- **Restricciones principales**:
  - flota homogénea con capacidad fija
  - cada cliente se visita exactamente una vez
  - cada ruta sale del depósito y vuelve a él

## Algoritmos implementados

### Constructivo

- **GraspPfi** (`operators.py`): inserción por prioridad con lista restringida de candidatos (RCL, `alpha=0.3`). Cada ruta empieza vacía: el primer cliente usa el mismo score, RCL y RNG que el resto, con posición 0. Cuando ningún cliente cabe, se cierra la ruta y se abre otra; si ninguno cabe en una ruta vacía, se rechaza la instancia con un error claro.

La variante actual aplica esta regla por igual a baseline y scores custom. Los 20 scores del pipeline se generaron con un prompt que describía semilla farthest y se reutilizan sin nuevas llamadas ni cambios en sus fuentes o respuestas históricas. Esto no implica mejores resultados; se evalúa desde cero y las mediciones farthest quedan archivadas aparte.

**PRIMERA VERSIÓN.** El constructor fijaba el hueco a la inserción geométrica más barata, minimizando `d[prev][cliente] + d[cliente][next] - d[prev][next]`, y la heurística solo ordenaba clientes para la RCL. No podía cambiar esa posición.

**SEGUNDA (MEJORA).** Para cada cliente que cabe en la capacidad restante, se evalúa el score en todas las posiciones de la ruta y se conserva la de menor valor. Si hay empate, gana la primera. Ese cliente entra en la RCL con el score guardado, y la RCL elige al azar entre los que cumplen `score <= min + alpha*(max-min)`. La fórmula decide el hueco y la prioridad del cliente. Si el score es el incremento de distancia de `heuristic.py`, el mínimo coincide con la inserción más barata de la primera versión.

La firma no cambia: un `float` por cliente y posición, y un valor más bajo sigue siendo mejor. Cambia el uso de ese número. En la primera versión la posición ya venía fijada y el valor solo ordenaba la RCL. En la segunda, el mínimo entre posiciones elige el hueco y ese mínimo es el que entra en la RCL. La lista sigue siendo de clientes, no de todos los huecos: meter cada posición en la RCL haría que `alpha` aceptara inserciones malas. Un término igual en todas las posiciones de un cliente no mueve el hueco; solo cambia su prioridad. "Mejora" nombra esta generalización del constructor. La primera versión es el caso particular en el que el score es el incremento de distancia. No afirma, por sí sola, que las rutas sean mejores. La inserción más barata sigue siendo una salida válida, así que las heurísticas pueden variar en el hueco o repetir la regla geométrica y cambiar solo la prioridad.

### Búsquedas locales

- **TwoOpt** (`operators.py`): 2-opt dentro de cada ruta, primera mejora.

**Metaheurística principal**: GRASP (construir y después 2-opt), implementada en `utils.py`.

## Estructura de la resolución

1. **Inicialización**: lee instancias TSPLIB (EUC_2D) de `src/input/`.
2. **Construcción**: GraspPfi genera una solución factible.
3. **Mejora**: TwoOpt compacta cada ruta.
4. **Bucle**: se repite N iteraciones y se guarda la mejor.
5. **Salida**: imprime y escribe `.sol` en `src/output/`.

## Particularidades de la implementación

### Validación de factibilidad

`is_feasible()` comprueba que no se supera la capacidad y que todos los clientes aparecen exactamente una vez.

### Distancias

Matriz euclídea en `utils.py`. El depósito es el nodo 0 tras leer el `.vrp`.

## Entrada y salida

### Entrada

`src/input/*.vrp` en formato TSPLIB CVRP (`NODE_COORD_SECTION` + `DEMAND_SECTION`).

Hay una instancia de juguete: `toy-n8-k3.vrp` (7 clientes, capacidad 20).

### Salida

`src/output/<nombre>.sol` con calidad, factibilidad y secuencia de cada ruta.

## Configuración

CLI: `--heuristic basic|custom` (basic por defecto), `--seed 1`, `--alpha 0.3`, `--input-dir src/input`, `--output-dir src/output`, `--instance E-n22-k4`. Sin límites explícitos se usan 300 segundos **por instancia**. `--iterations N` sin `--time-limit` desactiva el plazo para una regresión determinista; con ambos límites se termina al alcanzar cualquiera. La semilla se reinicia por instancia.

## Aplicación

Línea base rápida para experimentos de rutas: generar soluciones CVRP y comparar calidad y tiempo.

## Ejecución

```bash
uv sync
uv run python -m src
```

## Evaluación anytime

```powershell
.venv\Scripts\python.exe -m src --heuristic basic --time-limit 300 --seed 1 --alpha 0.3 --input-dir src/input --output-dir src/output/basic --instance E-n22-k4
.venv\Scripts\python.exe -m src --heuristic custom --time-limit 300 --seed 1 --alpha 0.3 --input-dir src/input --output-dir src/output/custom --instance E-n22-k4
.venv\Scripts\python.exe -m src --heuristic basic --iterations 5 --seed 7 --instance E-n22-k4
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Omitir `--instance` procesa todos los `.vrp` del directorio. Se incluyen los originales E-n22-k4, E-n30-k3, P-n19-k2 y P-n40-k5, copiados byte a byte de artifacts.

La salida estándar contiene un JSON por instancia (JSONL). Se escriben `<stem>.json` y `<stem>.sol` en el directorio de salida; una nueva ejecución en ese directorio los sustituye. Campos JSON: `instance`, `seed`, `alpha`, `heuristic`, `time_limit`, `iteration_limit`, `first_solution_time`, `first_solution_cost`, `best_cost`, `time_to_best`, `elapsed`, `iterations`, `feasible`, `routes`, `improvements`. `routes` son listas de índices con base cero, sin depósito. `improvements` contiene `{time, cost}` para la primera solución factible y cada mejora estricta del incumbente, incluido cada movimiento 2-opt que lo mejora. Los tiempos van en segundos monotónicos desde el inicio de `execute` y excluyen la lectura, la matriz y la escritura. `iterations` cuenta construcciones terminadas, aunque su búsqueda local se interrumpa. La primera solución se mide **tras una construcción factible y antes de la búsqueda local**. Sin solución completa: `feasible=false`, costes y tiempos de solución a `null`, `routes=[]`. No se publica una construcción parcial. El incumbente se copia antes de la búsqueda local y tras cada mejora, y sobrevive a la interrupción.

El plazo es cooperativo dentro de candidatos, inserciones y pares 2-opt: el presupuesto queda cerca de lo solicitado, sin garantía de tiempo real duro, porque una operación atómica, el scoring o una copia pueden terminar después del límite. El scoring inyectado debe ser puro, rápido y finito. La implementación incluida no usa red ni un modelo de lenguaje en ejecución. El ranking ascendente (`utils.ranking_key`) ordena por **factibilidad, coste final y tiempo hasta la mejor**; todos los resultados no factibles empatan al final.

### Scoring

`heuristic.py` es el score por defecto de `GraspPfi` (`--heuristic basic`) y no se modifica. `custom_heuristic.py` es el score que se sustituye (`--heuristic custom`). El contrato de ambos es el mismo: entrada CVRP válida, un score menor es mejor, y no se mutan la instancia, la solución ni los clientes sin asignar. En la mejora cada llamada se repite una vez por posición factible, así que un cuerpo de coste lineal en la longitud de la ruta cuesta el cuadrado de esa longitud para ese cliente.

Se conserva la **distancia euclídea real sin redondear** y la **flota no restringida**: la `k` del nombre no limita el número de vehículos. Por eso no se calcula la brecha respecto al óptimo publicado de CVRPLIB, cuyo modelo puede ser distinto.
