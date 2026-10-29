# GRASP para CVRP

Implementación del algoritmo especializado utilizado en el TFM. El constructor emplea una lista restringida de candidatos y permite sustituir la función de puntuación de cada inserción. Después aplica 2-opt dentro de cada ruta.

## Ejecución

```powershell
uv sync
uv run python -m src --heuristic basic --instance E-n22-k4
uv run python -m unittest discover -s tests -v
```

Por defecto se leen las instancias de `../mulcia-tfm-artifacts/inputs/03-grasp/01-instances` y se escriben resultados en `outputs/`. Ambas rutas pueden cambiarse con `--input-dir` y `--output-dir`.

Opciones principales: `--heuristic basic|custom`, `--seed`, `--alpha`, `--time-limit` y `--iterations`. La salida incluye un JSON de métricas y una solución `.sol` por instancia.

`src/heuristic.py` contiene la referencia y `src/custom_heuristic.py` el punto de integración de una puntuación generada. La generación, validación y ranking de candidatos se realizan desde `mulcia-tfm-hllm-pipeline`.
