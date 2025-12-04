"""
Veyra CLI Entry Point

Provides command-line interface for running Veyra.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from veyra.core import VeyraCore
from veyra.config import load_config
from veyra.logging_utils import setup_logging
from veyra.models import list_backends


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="veyra",
        description="Veyra: Post-Super-Intelligence Interplanetary LLM System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with mock backend (no API key needed)
  veyra --prompt "Hello Veyra" --backend mock
  
  # Run with OpenAI backend
  veyra --prompt "Analyze this data" --backend openai
  
  # Interactive mode
  veyra --interactive
  
  # Load from file and save results
  veyra --input-file task.json --output results.json
        """,
    )
    
    # Input options
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        help="Prompt to execute",
    )
    parser.add_argument(
        "--input-file", "-i",
        type=str,
        help="JSON file containing task(s) to execute",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file for results (JSON)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output except results",
    )
    
    # Model options
    parser.add_argument(
        "--backend", "-b",
        type=str,
        choices=list_backends(),
        help="Model backend to use",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        help="Specific model name (backend-dependent)",
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        help="Sampling temperature (0.0-2.0)",
    )
    
    # Configuration
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="configs/default.yaml",
        help="Path to configuration file",
    )
    
    # System options
    parser.add_argument(
        "--simulate-latency",
        action="store_true",
        help="Simulate interplanetary communication delays",
    )
    parser.add_argument(
        "--environment", "-e",
        type=str,
        choices=["earth", "mars", "lunar", "space"],
        help="Target environment",
    )
    
    # Debug options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health check and exit",
    )
    
    return parser


def run_interactive(veyra: VeyraCore) -> None:
    """Run interactive mode."""
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║           VEYRA Interactive Mode                          ║")
    print("║  Post-Super-Intelligence Interplanetary LLM System        ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print("║  Commands:                                                ║")
    print("║    /quit, /exit  - Exit interactive mode                  ║")
    print("║    /health       - Check system health                    ║")
    print("║    /audit        - Show audit log                         ║")
    print("║    /clear        - Clear screen                           ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    while True:
        try:
            prompt = input("\033[36mveyra>\033[0m ").strip()
            
            if not prompt:
                continue
            
            # Handle commands
            if prompt.lower() in ("/quit", "/exit", "quit", "exit"):
                print("\nGoodbye! 🚀")
                break
            elif prompt.lower() == "/health":
                health = asyncio.get_event_loop().run_until_complete(veyra.health_check())
                print(json.dumps(health, indent=2))
                continue
            elif prompt.lower() == "/audit":
                audit = veyra.get_audit_log()
                if audit:
                    print(json.dumps(audit[-5:], indent=2))  # Last 5 entries
                else:
                    print("No audit entries yet.")
                continue
            elif prompt.lower() == "/clear":
                print("\033[2J\033[H", end="")
                continue
            elif prompt.startswith("/"):
                print(f"Unknown command: {prompt}")
                continue
            
            # Execute prompt
            print("\033[33mProcessing...\033[0m")
            result = veyra.execute(prompt)
            
            if result.success:
                print(f"\n\033[32m{result.content}\033[0m\n")
            else:
                print(f"\n\033[31mError: {result.error}\033[0m\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type /quit to exit.")
        except EOFError:
            print("\nGoodbye! 🚀")
            break


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    if args.quiet:
        log_level = "WARNING"
    setup_logging(level=log_level)
    
    # Load configuration
    config = load_config(args.config if Path(args.config).exists() else None)
    
    # Apply CLI overrides
    if args.backend:
        config.model.backend = args.backend
    if args.model:
        if config.model.backend == "openai":
            config.model.openai_model = args.model
        elif config.model.backend == "anthropic":
            config.model.anthropic_model = args.model
    if args.temperature is not None:
        config.model.temperature = args.temperature
    if args.simulate_latency:
        config.latency.simulate_latency = True
    if args.environment:
        config.environment = args.environment
    
    # Create Veyra instance
    veyra = VeyraCore(config=config)
    
    # Handle health check
    if args.health_check:
        health = asyncio.get_event_loop().run_until_complete(veyra.health_check())
        print(json.dumps(health, indent=2))
        sys.exit(0 if health["status"] == "healthy" else 1)
    
    # Handle interactive mode
    if args.interactive:
        run_interactive(veyra)
        return
    
    # Handle input file
    if args.input_file:
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
            sys.exit(1)
        
        with open(input_path) as f:
            tasks = json.load(f)
        
        # Handle single task or list of tasks
        if isinstance(tasks, dict):
            tasks = [tasks]
        
        results = []
        for task in tasks:
            result = veyra.execute(task)
            results.append(result.to_dict())
        
        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(results, indent=2))
        
        return
    
    # Handle prompt
    if args.prompt:
        result = veyra.execute(args.prompt)
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            if not args.quiet:
                print(f"Result written to {args.output}")
        else:
            if result.success:
                print(result.content)
            else:
                print(f"Error: {result.error}", file=sys.stderr)
                sys.exit(1)
        
        return
    
    # No input specified - show help or run legacy mode
    if len(sys.argv) == 1:
        # No arguments - run legacy mode for backwards compatibility
        veyra.run()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
