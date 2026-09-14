import os
import time

from src.cvrp import read_vrp
from src.operators import GraspPfi, TwoOpt
from src.utils import Grasp, RandomManager

PROJECT_PATH = os.path.dirname(__file__)
INPUT_DIR = os.path.join(PROJECT_PATH, "input")
OUTPUT_DIR = os.path.join(PROJECT_PATH, "output")
ITERATIONS = 500000
SEED = 1


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    RandomManager.set_seed(SEED)

    grasp = Grasp(constructive=GraspPfi(), improvement=TwoOpt(), iterations=ITERATIONS)

    for filename in sorted(os.listdir(INPUT_DIR)):
        if not filename.endswith(".vrp"):
            continue
        instance = read_vrp(os.path.join(INPUT_DIR, filename))
        start = time.perf_counter()
        solution = grasp.execute(instance)
        elapsed = time.perf_counter() - start

        text = (
            f"instance={instance.name}\n"
            f"iterations={ITERATIONS}  seed={SEED}  time={elapsed:.3f}s\n"
            f"{solution}\n"
        )
        print(text)
        out_path = os.path.join(OUTPUT_DIR, filename.replace(".vrp", ".sol"))
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text)


if __name__ == "__main__":
    main()
