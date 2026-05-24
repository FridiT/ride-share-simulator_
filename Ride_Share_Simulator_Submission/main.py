#!/usr/bin/env python3
"""
Ride Share Simulator - Main Entry Point

Orchestrates the entire simulation workflow:
1. Load and validate input data via Parser
2. Initialize Simulator with configuration
3. Run simulation with selected Strategy
4. Generate final report and output
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.parser import parse_input_json, generate_report, save_to_json
from src.simulator import Simulator
from src.strategies import ShortestDistanceStrategy, WeightedScoreStrategy


def configure_logging(log_dir: Path, dev_mode: bool) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"simulation_{datetime.now(timezone.utc):%Y-%m-%d_%H-%M-%S}.log"

    handlers = [logging.FileHandler(log_file, encoding="utf-8")]
    if dev_mode:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
    )

    if dev_mode:
        # Show DEBUG only for this project, keep third-party loggers quieter.
        logging.getLogger("__main__").setLevel(logging.DEBUG)
        logging.getLogger("src").setLevel(logging.DEBUG)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Ride Share Simulator.")
    parser.add_argument(
        "--input",
        default="data/input.json",
        help="Path to the input JSON file containing drivers and rides.",
    )
    parser.add_argument(
        "--strategy",
        default="weighted",
        choices=["weighted", "shortest"],
        help="Matching strategy to use: weighted or shortest.",
    )
    parser.add_argument(
        "--output",
        default="output/results.json",
        help="Path to write the simulation output JSON report.",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Enable console logging in addition to log file output.",
    )
    return parser.parse_args()


def select_strategy(strategy_name: str):
    if strategy_name == "shortest":
        return ShortestDistanceStrategy()
    return WeightedScoreStrategy()


def main() -> int:
    args = parse_args()
    configure_logging(Path("logs"), args.dev)
    logger = logging.getLogger(__name__)

    logger.info("Starting Ride Share Simulator")
    logger.info("Input: %s", args.input)
    logger.info("Strategy: %s", args.strategy)
    logger.info("Output: %s", args.output)

    try:
        drivers, rides = parse_input_json(args.input)
    except FileNotFoundError as error:
        logger.error("Input file not found: %s", error)
        return 1
    except Exception as error:
        logger.error("Failed to parse input JSON: %s", error)
        return 1

    logger.info("Loaded %d drivers and %d rides from input", len(drivers), len(rides))

    if not drivers:
        logger.warning("No drivers loaded from input.")

    if not rides:
        logger.warning("No rides loaded from input.")

    # Sort rides deterministically by request time, distance, and id
    rides.sort(key=lambda ride: (ride.request_time_seconds, ride.calculate_distance(), ride.id))

    strategy = select_strategy(args.strategy)
    simulator = Simulator(strategy)

    for driver in drivers:
        simulator.add_driver(driver)

    results = simulator.run(rides)
    report = generate_report(results)

    try:
        save_to_json(report, args.output)
    except Exception as error:
        logger.error("Failed to save output JSON: %s", error)
        return 1

    logger.info("Simulation complete. Results written to %s", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
