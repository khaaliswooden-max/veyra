#!/usr/bin/env python
"""
Benchmark Runner Script

Run Veyra benchmarks from the command line.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir / "src"))

from veyra import VeyraCore
from veyra.config import load_config
from veyra.logging_utils import setup_logging
from veyra.benchmarks import BenchmarkRunner
from veyra.benchmarks.base import BenchmarkFamily, Difficulty
from veyra.benchmarks.runner import list_benchmarks


def main():
    parser = argparse.ArgumentParser(
        description="Run Veyra Benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run CPLC benchmark with 10 tasks
  python scripts/run_benchmark.py --family CPLC --count 10

  # Run with specific difficulty
  python scripts/run_benchmark.py --family CPLC --difficulty hard --count 5

  # Run full benchmark suite
  python scripts/run_benchmark.py --all

  # Save results to file
  python scripts/run_benchmark.py --family CPLC --output results.json
        """,
    )
    
    # Benchmark selection
    parser.add_argument(
        "--family", "-f",
        type=str,
        choices=[f.value for f in BenchmarkFamily],
        help="Benchmark family to run",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run full benchmark suite",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available benchmarks",
    )
    
    # Configuration
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=10,
        help="Number of tasks to run",
    )
    parser.add_argument(
        "--difficulty", "-d",
        type=str,
        choices=[d.value for d in Difficulty],
        default="medium",
        help="Difficulty level",
    )
    
    # Model configuration
    parser.add_argument(
        "--backend", "-b",
        type=str,
        default="mock",
        help="Model backend to use",
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file",
    )
    
    # Output
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file for results (JSON)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level="DEBUG" if args.verbose else "INFO")
    
    # List benchmarks
    if args.list:
        print("Available benchmarks:")
        for name in list_benchmarks():
            print(f"  - {name}")
        print("\nBenchmark families:")
        for family in BenchmarkFamily:
            print(f"  - {family.value}: {family.name}")
        return
    
    # Require either --family or --all
    if not args.family and not args.all:
        parser.print_help()
        print("\nError: Specify --family or --all")
        sys.exit(1)
    
    # Load configuration
    config = load_config(args.config)
    config.model.backend = args.backend
    
    # Create Veyra instance
    veyra = VeyraCore(config=config)
    runner = BenchmarkRunner(veyra)
    
    # Run benchmarks
    difficulty = Difficulty(args.difficulty)
    
    async def run():
        if args.all:
            print(f"Running full benchmark suite ({args.count} tasks per family, {args.difficulty} difficulty)")
            result = await runner.run_all(
                count_per_family=args.count,
                difficulty=difficulty,
            )
        else:
            family = BenchmarkFamily(args.family)
            print(f"Running {family.value} benchmark ({args.count} tasks, {args.difficulty} difficulty)")
            result = await runner.run_family(
                family=family,
                count=args.count,
                difficulty=difficulty,
            )
        
        return result
    
    result = asyncio.get_event_loop().run_until_complete(run())
    
    # Print results
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total Tasks:  {result.total_tasks}")
    print(f"Passed:       {result.passed_tasks}")
    print(f"Failed:       {result.failed_tasks}")
    print(f"V-Score:      {result.v_score:.3f}")
    print(f"Total Time:   {result.total_time_seconds:.2f}s")
    
    if result.family_scores:
        print("\nFamily Scores:")
        for family, score in result.family_scores.items():
            print(f"  {family}: {score:.3f}")
    
    print("=" * 60)
    
    # Save results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()

