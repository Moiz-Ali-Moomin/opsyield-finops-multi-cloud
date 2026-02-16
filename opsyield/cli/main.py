import argparse
import sys
import json
import logging
import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import List

from ..core.orchestrator import Orchestrator
from ..core.snapshot import SnapshotManager
from ..core.models import AnalysisResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("opsyield-cli")

def main():
    parser = argparse.ArgumentParser(description="OpsYield - Cloud Financial Intelligence Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common Arguments Parser (Parent)
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--provider", type=str, required=True, choices=["gcp", "aws"], help="Cloud provider")
    common_parser.add_argument("--project-id", type=str, help="GCP Project ID (required for GCP)")
    common_parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")
    common_parser.add_argument("--policy", type=str, help="Path to policies.yaml", default=None)

    # Analyze Command
    analyze_parser = subparsers.add_parser("analyze", parents=[common_parser], help="Analyze cloud costs and optimizations")
    analyze_parser.add_argument("--out", type=str, default="stdout", help="Output file path or 'stdout'")
    analyze_parser.add_argument("--format", type=str, default="json", choices=["json", "table"], help="Output format")

    # Snapshot Command
    snapshot_parser = subparsers.add_parser("snapshot", help="Manage cost snapshots")
    snapshot_subparsers = snapshot_parser.add_subparsers(dest="snapshot_command", help="Snapshot actions")
    
    # Snapshot Save
    snap_save_parser = snapshot_subparsers.add_parser("save", parents=[common_parser], help="Save a baseline snapshot")
    snap_save_parser.add_argument("file", type=str, help="Path to save the snapshot JSON")

    # Diff Command
    diff_parser = subparsers.add_parser("diff", parents=[common_parser], help="Compare current state against a baseline")
    diff_parser.add_argument("baseline", type=str, help="Path to baseline snapshot JSON")
    diff_parser.add_argument("--threshold", type=float, default=0.0, help="Fail if cost increase % > threshold")
    diff_parser.add_argument("--fail-on-policy", action="store_true", help="Fail if policy violations exist")

    # Serve Command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    # GCP Command Group
    gcp_parser = subparsers.add_parser("gcp", help="GCP-specific commands")
    gcp_subparsers = gcp_parser.add_subparsers(dest="gcp_command", help="GCP actions")

    # GCP Setup
    gcp_setup_parser = gcp_subparsers.add_parser("setup", help="Configure GCP billing export to BigQuery")
    gcp_setup_parser.add_argument("--project-id", type=str, help="GCP Project ID (auto-detected from ADC if omitted)")
    gcp_setup_parser.add_argument("--billing-account", type=str, help="Billing Account ID (e.g. 01A2B3-C4D5E6-F7G8H9)")
    gcp_setup_parser.add_argument("--dataset", type=str, default="billing_export", help="BigQuery dataset name")
    gcp_setup_parser.add_argument("--location", type=str, default="US", help="BigQuery dataset location")

    args = parser.parse_args()

    if args.command == "analyze":
        asyncio.run(run_analyze(args))
    elif args.command == "snapshot":
        if args.snapshot_command == "save":
            asyncio.run(run_snapshot_save(args))
        else:
            snapshot_parser.print_help()
    elif args.command == "diff":
        asyncio.run(run_diff(args))
    elif args.command == "serve":
        run_serve(args)
    elif args.command == "gcp":
        if hasattr(args, 'gcp_command') and args.gcp_command == "setup":
            run_gcp_setup(args)
        else:
            gcp_parser.print_help()
    else:
        parser.print_help()

async def get_analysis_data(args) -> dict:
    # Reusable analysis logic using Orchestrator
    logger.info(f"Starting analysis for provider: {args.provider}")
    
    orchestrator = Orchestrator()
    result = await orchestrator.analyze(
        provider_name=args.provider, 
        days=args.days, 
        project_id=args.project_id
    )
    
    # Convert dataclass to dict for serialization/compatibility
    return asdict(result)

async def run_analyze(args):
    data = await get_analysis_data(args)
    
    # Output
    if args.out == "stdout":
        # Handle datetime serialization if necessary, but asdict usually produces serializable types 
        # except datetime objects.
        print(json.dumps(data, indent=2, default=str))
    else:
        with open(args.out, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Report written to {args.out}")

async def run_snapshot_save(args):
    data = await get_analysis_data(args)
    SnapshotManager.save(data, args.file)

async def run_diff(args):
    current_data = await get_analysis_data(args)
    baseline_data = SnapshotManager.load(args.baseline)
    
    diff_result = SnapshotManager.compare(
        baseline=baseline_data,
        current=current_data,
        cost_threshold_pct=args.threshold,
        fail_on_policy=args.fail_on_policy
    )
    
    print(json.dumps({
        "is_regression": diff_result.is_regression,
        "cost_increase_pct": round(diff_result.cost_increase_pct, 2),
        "risk_score_change": round(diff_result.risk_score_change, 2),
        "new_anomalies": diff_result.new_anomalies,
        "new_violations": diff_result.new_violations,
        "details": diff_result.details
    }, indent=2))
    
    if diff_result.is_regression:
        logger.error("Guardrail failure: Regression detected.")
        sys.exit(1)
    else:
        logger.info("Guardrail passed: No significant regression.")
        sys.exit(0)

def run_serve(args):
    import uvicorn
    uvicorn.run("opsyield.api.main:app", host=args.host, port=args.port, reload=True)


def run_gcp_setup(args):
    """Run GCP billing export automation with Rich output."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        HAS_RICH = True
    except ImportError:
        HAS_RICH = False

    from ..automation.gcp_setup import run_full_setup, GCPSetupError

    if HAS_RICH:
        console = Console()
        console.print("\n[bold blue]OpsYield[/bold blue] — GCP Billing Export Setup\n")
    else:
        print("\nOpsYield — GCP Billing Export Setup\n")

    try:
        result = run_full_setup(
            project_id=getattr(args, 'project_id', None),
            billing_account_id=getattr(args, 'billing_account', None),
            dataset_id=getattr(args, 'dataset', 'billing_export'),
            location=getattr(args, 'location', 'US'),
        )
    except GCPSetupError as e:
        if HAS_RICH:
            console.print(f"[red bold]✗ Error ({e.step}):[/red bold] {e}")
            if e.hint:
                console.print(f"  [yellow]Hint:[/yellow] {e.hint}")
        else:
            print(f"ERROR ({e.step}): {e}")
            if e.hint:
                print(f"  Hint: {e.hint}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

    # ── Print Results ──
    if HAS_RICH:
        # Steps table
        table = Table(title="Setup Steps", show_header=True, header_style="bold cyan")
        table.add_column("Step", style="bold")
        table.add_column("Status")
        table.add_column("Details")

        for step_name, step_data in result.get("steps", {}).items():
            status = step_data.get("status", "unknown")
            if status == "error":
                status_str = "[red]✗ Error[/red]"
            elif status in ("ok", "exists", "created"):
                status_str = "[green]✓ OK[/green]"
            elif status == "skipped":
                status_str = "[yellow]⊘ Skipped[/yellow]"
            else:
                status_str = f"[dim]{status}[/dim]"

            details = step_data.get("message", step_data.get("error", ""))
            if not details:
                details = json.dumps({k: v for k, v in step_data.items() if k != "status"}, default=str)[:80]

            table.add_row(step_name.upper(), status_str, str(details)[:80])

        console.print(table)
        console.print(f"\n[dim]Completed in {result.get('elapsed_s', '?')}s[/dim]")

        # Overall result
        if result.get("success"):
            console.print(Panel(
                f"[green bold]✓ {result.get('message', 'Setup complete')}[/green bold]",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[yellow bold]⚠ {result.get('message', 'Setup incomplete')}[/yellow bold]",
                border_style="yellow",
            ))

        # Next steps
        next_steps = result.get("next_steps", [])
        if next_steps:
            console.print("\n[bold]Next Steps:[/bold]")
            for step in next_steps:
                if step:  # skip empty lines
                    console.print(f"  {step}")
                else:
                    console.print()
    else:
        # Plain text fallback
        print(json.dumps(result, indent=2, default=str))

    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
