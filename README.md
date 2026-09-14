# CVRP con GRASP

Experimento pequeño de GRASP para el Capacitated Vehicle Routing Problem.

## Problem

- **Objective**: minimizar la distancia total de las rutas.
- **Main constraints**:
  - flota homogenea con capacidad fija
  - cada cliente se visita exactamente una vez
  - cada ruta sale y vuelve al deposito

## Implemented Algorithms

### Constructive

- **GraspPfi** (`operators.py`): Priority-First Insertion con lista restringida de candidatos (RCL, `alpha=0.3`). Siembra la ruta con el cliente mas lejano al deposito e inserta el que menos alarga la ruta.

### Local Searches

- **TwoOpt** (`operators.py`): 2-opt intra-ruta, first improvement.

**Main metaheuristic**: GRASP (construir + 2-opt), implementado en `utils.py`.

## Resolution Structure

1. **Initialization**: lee instancias TSPLIB (EUC_2D) de `src/input/`.
2. **Construction**: GraspPfi genera una solucion factible.
3. **Improvement**: TwoOpt compacta cada ruta.
4. **Loop**: se repite N iteraciones y se guarda la mejor.
5. **Output**: imprime y escribe `.sol` en `src/output/`.

## Implementation Particularities

### Feasibility Validation

`is_feasible()` comprueba que no se supera la capacidad y que todos los clientes aparecen exactamente una vez.

### Distances

Matriz euclidea en `utils.py`. El deposito es el nodo 0 tras leer el `.vrp`.

## Input and Output

### Input

`src/input/*.vrp` en formato TSPLIB CVRP (`NODE_COORD_SECTION` + `DEMAND_SECTION`).

Hay una instancia de juguete: `toy-n8-k3.vrp` (7 clientes, capacidad 20).

### Output

`src/output/<nombre>.sol` con calidad, factibilidad y secuencia de cada ruta.

## Configuration

En `src/__main__.py`:

- `ITERATIONS = 40`
- `SEED = 1`
- `alpha = 0.3` (en el reader)

## Application

Baseline rapido para experimentos de routing: generar soluciones CVRP y comparar calidad/tiempo.

## Execution

```bash
uv sync
uv run python -m src
```
