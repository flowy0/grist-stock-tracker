#!/usr/bin/env python3
"""Environment management script for Grist Stock Tracker.

Manages switching between dev, test, and production environments.

Usage:
    uv run python manage_env.py status              # Show current environment
    uv run python manage_env.py start [env]         # Start environment (default: current)
    uv run python manage_env.py stop [env]          # Stop environment (default: current)
    uv run python manage_env.py switch <env>        # Switch to environment
    uv run python manage_env.py logs [env]          # Show logs for environment

Environments:
    dev          - Local development (port 8484, ./grist-data)
    test         - Test environment (port 8485, ./grist-data-test)
    production   - Production environment (port 8484, ./grist-data-prod)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DOCKER_COMPOSE = PROJECT_ROOT / "docker-compose.yml"
DOCKER_COMPOSE_TEST = PROJECT_ROOT / "docker-compose.test.yml"


def get_current_env() -> str:
    """Get current environment from ENVIRONMENT variable."""
    return os.getenv("ENVIRONMENT", "dev")


def show_status():
    """Show current environment status."""
    env = get_current_env()
    print(f"Current environment: {env}")
    print()

    # Show container status
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=grist-stock-tracker", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        print("Containers:")
        print(result.stdout)
    else:
        print("No containers running.")

    # Show data directories
    print("\nData directories:")
    for name, path in [
        ("dev", PROJECT_ROOT / "grist-data"),
        ("test", PROJECT_ROOT / "grist-data-test"),
        ("production", PROJECT_ROOT / "grist-data-prod"),
    ]:
        size = "N/A"
        if path.exists():
            try:
                total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                size = f"{total_size / (1024*1024):.1f} MB"
            except:
                size = "exists"
        status = "✓" if path.exists() else "✗"
        print(f"  [{status}] {name}: {path} ({size})")


def start_environment(env: str = None):
    """Start the specified environment."""
    env = env or get_current_env()

    print(f"Starting {env} environment...")

    if env == "test":
        # Test environment uses override file
        subprocess.run(
            ["docker-compose", "-f", str(DOCKER_COMPOSE), "-f", str(DOCKER_COMPOSE_TEST), "up", "-d"],
            cwd=PROJECT_ROOT,
            check=True,
        )
        print(f"\nTest environment started on http://localhost:8485")
    else:
        # Development or production
        data_dir = f"./grist-data{'-prod' if env == 'production' else ''}"
        env_vars = os.environ.copy()
        env_vars["GRIST_DATA_DIR"] = data_dir

        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=PROJECT_ROOT,
            env=env_vars,
            check=True,
        )
        port = "8484"
        print(f"\n{env.title()} environment started on http://localhost:{port}")


def stop_environment(env: str = None):
    """Stop the specified environment."""
    env = env or get_current_env()

    print(f"Stopping {env} environment...")

    if env == "test":
        subprocess.run(
            ["docker-compose", "-f", str(DOCKER_COMPOSE), "-f", str(DOCKER_COMPOSE_TEST), "down"],
            cwd=PROJECT_ROOT,
            check=True,
        )
    else:
        subprocess.run(
            ["docker-compose", "down"],
            cwd=PROJECT_ROOT,
            check=True,
        )

    print(f"{env.title()} environment stopped.")


def switch_environment(env: str):
    """Switch to a different environment."""
    valid_envs = ["dev", "test", "production"]

    if env not in valid_envs:
        print(f"Invalid environment: {env}")
        print(f"Valid environments: {', '.join(valid_envs)}")
        sys.exit(1)

    # Update .env file
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"

    if not env_file.exists():
        if env_example.exists():
            print("Creating .env from .env.example...")
            env_file.write_text(env_example.read_text())
        else:
            env_file.write_text("")

    content = env_file.read_text()

    # Replace or add ENVIRONMENT line
    if "ENVIRONMENT=" in content:
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("ENVIRONMENT="):
                new_lines.append(f"ENVIRONMENT={env}")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        content = f"ENVIRONMENT={env}\n{content}"

    env_file.write_text(content)
    print(f"Switched to {env} environment")
    print(f"Updated {env_file}")
    print()
    print("Note: You may need to restart your shell or reload .env for changes to take effect.")


def show_logs(env: str = None, follow: bool = False):
    """Show logs for the specified environment."""
    env = env or get_current_env()

    cmd = ["docker-compose", "logs"]
    if follow:
        cmd.append("-f")

    if env == "test":
        cmd = ["docker-compose", "-f", str(DOCKER_COMPOSE), "-f", str(DOCKER_COMPOSE_TEST), "logs"]
        if follow:
            cmd.append("-f")

    subprocess.run(cmd, cwd=PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(
        description="Manage Grist Stock Tracker environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python manage_env.py status              # Show current status
  uv run python manage_env.py start               # Start current environment
  uv run python manage_env.py start test          # Start test environment
  uv run python manage_env.py switch test         # Switch to test environment
  uv run python manage_env.py logs -f             # Follow logs
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Status command
    subparsers.add_parser("status", help="Show current environment status")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start environment")
    start_parser.add_argument("env", nargs="?", choices=["dev", "test", "production"],
                             help="Environment to start (default: current)")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop environment")
    stop_parser.add_argument("env", nargs="?", choices=["dev", "test", "production"],
                            help="Environment to stop (default: current)")

    # Switch command
    switch_parser = subparsers.add_parser("switch", help="Switch environment")
    switch_parser.add_argument("env", choices=["dev", "test", "production"],
                              help="Environment to switch to")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show environment logs")
    logs_parser.add_argument("env", nargs="?", choices=["dev", "test", "production"],
                            help="Environment to show logs for (default: current)")
    logs_parser.add_argument("-f", "--follow", action="store_true",
                            help="Follow log output")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "status":
            show_status()
        elif args.command == "start":
            start_environment(args.env)
        elif args.command == "stop":
            stop_environment(args.env)
        elif args.command == "switch":
            switch_environment(args.env)
        elif args.command == "logs":
            show_logs(args.env, args.follow)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
