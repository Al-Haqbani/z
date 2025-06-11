from rich.table import Table
from rich.console import Console


def print_results(results):
    table = Table(title="Leak Results")
    table.add_column("#", style="cyan")
    table.add_column("Source")
    table.add_column("File")
    table.add_column("Leak Type")
    table.add_column("Value")

    for idx, item in enumerate(results, 1):
        table.add_row(str(idx), item.get("source", ""), item.get("file", ""),
                      item.get("leak_type", ""), item.get("value", ""))
    console = Console()
    console.print(table)
