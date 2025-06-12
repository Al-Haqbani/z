from rich.table import Table
from rich.console import Console


def _assign_severity(leak_type: str) -> str:
    name = leak_type.lower()
    if "token" in name or "key" in name:
        return "high"
    return "medium"


def print_results(results):
    table = Table(title="Leak Results")
    table.add_column("#", style="cyan")
    table.add_column("Source")
    table.add_column("File")
    table.add_column("Leak Type")
    table.add_column("Value")
    table.add_column("Severity")

    for idx, item in enumerate(results, 1):
        sev = item.get("severity") or _assign_severity(item.get("leak_type", ""))
        style = "red" if sev == "high" else "yellow"
        table.add_row(
            str(idx),
            item.get("source", ""),
            item.get("file", ""),
            item.get("leak_type", ""),
            item.get("value", ""),
            sev,
            style=style,
        )
    console = Console()
    console.print(table)
