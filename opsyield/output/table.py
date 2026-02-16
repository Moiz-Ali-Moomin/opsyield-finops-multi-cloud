from rich.console import Console
from rich.table import Table


def render_table(report):

    console = Console()

    # --- Main Summary Table ---
    table = Table(title="CloudLens Report")

    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Total Resources", str(report["resources"]))
    table.add_row("Estimated Monthly Cost ($)", str(report["cost"]))
    table.add_row("Waste Findings", str(len(report["waste"])))

    console.print(table)

    # --- Waste Details ---
    if report["waste"]:
        waste_table = Table(title="Idle / Waste Resources")

        waste_table.add_column("Instance")
        waste_table.add_column("Type")
        waste_table.add_column("Reasons")

        for item in report["waste"]:
            waste_table.add_row(
                item["name"],
                item["type"],
                ", ".join(item["reasons"])
            )

        console.print(waste_table)

    # --- Advanced Optimization ---
    if report.get("advanced"):
        adv_table = Table(title="Advanced Optimization Insights")

        adv_table.add_column("Instance")
        adv_table.add_column("Type")
        adv_table.add_column("Idle Score")
        adv_table.add_column("Recommendations")

        for item in report["advanced"]:
            adv_table.add_row(
                item["name"],
                item["type"],
                str(item["idle_score"]),
                "\n".join(item["recommendations"])
            )

        console.print(adv_table)
