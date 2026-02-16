
import click
import asyncio
from ..core.orchestrator import Orchestrator
from ..output.json_exporter import export_json

@click.group()
def cli():
    pass

@cli.command()
@click.option('--provider', required=True, help='Cloud provider (gcp, aws, azure)')
@click.option('--days', default=30, help='Analysis period in days')
@click.option('--output', default='report.json', help='Output JSON file')
def analyze(provider, days, output):
    """Run cost analysis for a specific provider"""
    orchestrator = Orchestrator()
    result = asyncio.run(orchestrator.analyze(provider, days=days))
    export_json(result, output)
    click.echo(f"Analysis complete. Report saved to {output}")

if __name__ == '__main__':
    cli()
