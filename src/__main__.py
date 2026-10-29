import argparse
import json
import math
import os
from pathlib import Path

from src.cvrp import read_vrp
from src.custom_heuristic import heuristic as custom_score
from src.heuristic import heuristic as basic_score
from src.operators import GraspPfi, TwoOpt
from src.utils import Grasp, RandomManager

PROJECT_PATH = Path(__file__).resolve().parent
REPOSITORY = PROJECT_PATH.parent
ARTIFACTS = Path(os.environ.get('TFM_ARTIFACTS_DIR', REPOSITORY.parent / 'mulcia-tfm-artifacts'))
INPUT_DIR = ARTIFACTS / 'inputs' / '03-grasp' / '01-instances'
OUTPUT_DIR = REPOSITORY / 'outputs'


def positive_float(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('must be finite and positive')
    return number


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return number


def alpha_value(value):
    number = float(value)
    if not 0 <= number <= 1:
        raise argparse.ArgumentTypeError('alpha must be in [0, 1]')
    return number


def build_parser():
    parser = argparse.ArgumentParser(description='CVRP GRASP anytime')
    parser.add_argument('--heuristic', choices=['basic', 'custom'], default='basic')
    parser.add_argument('--time-limit', type=positive_float,
                        help='seconds per instance (default 300 unless --iterations)')
    parser.add_argument('--iterations', type=positive_int)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--alpha', type=alpha_value, default=0.3)
    parser.add_argument('--input-dir', type=Path, default=INPUT_DIR)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT_DIR)
    parser.add_argument('--instance', help='filename or stem within input-dir')
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    files = sorted(args.input_dir.glob('*.vrp'))
    if args.instance:
        files = [p for p in files if args.instance in (p.name, p.stem)]
    if not files:
        parser.error('no matching .vrp instances in input-dir')
    time_limit = args.time_limit
    if time_limit is None and args.iterations is None:
        time_limit = 300.0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in files:
        instance = read_vrp(str(path), alpha=args.alpha)
        RandomManager.set_seed(args.seed)
        grasp = Grasp(GraspPfi(basic_score if args.heuristic == 'basic' else custom_score),
                      TwoOpt(), iterations=args.iterations, time_limit=time_limit)
        solution = grasp.execute(instance)
        metrics = dict(grasp.metrics, instance=instance.name, seed=args.seed,
                       alpha=args.alpha, heuristic=args.heuristic, time_limit=time_limit,
                       iteration_limit=args.iterations)
        text = json.dumps(metrics, allow_nan=False)
        print(text)
        (args.output_dir / (path.stem + '.json')).write_text(text + '\n', encoding='utf-8')
        (args.output_dir / (path.stem + '.sol')).write_text(
            f'instance={instance.name}\n' + (str(solution) if solution is not None
                                             else 'feasible=False (no complete solution)') + '\n',
            encoding='utf-8')


if __name__ == '__main__':
    main()
