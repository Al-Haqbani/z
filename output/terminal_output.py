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
    table.add_column("File", overflow="fold")
    table.add_column("Leak Type")
    table.add_column("Value")
    table.add_column("Severity")
    table.add_column("Active")

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
            "True" if item.get("active") else ("False" if item.get("active") is not None else "?"),
            style=style,
        )
    console = Console()
    console.print(table)
    # Ensure output appears immediately
    import sys
    sys.stdout.flush()


def print_result(item, idx=None):
    """Print a single result immediately."""
    idx = idx or 1
    sev = item.get("severity") or _assign_severity(item.get("leak_type", ""))
    style = "red" if sev == "high" else "yellow"
    table = Table(show_header=True if idx == 1 else False)
    table.add_column("#", style="cyan")
    table.add_column("Source")
    table.add_column("File", overflow="fold")
    table.add_column("Leak Type")
    table.add_column("Value")
    table.add_column("Severity")
    table.add_column("Active")
    table.add_row(
        str(idx),
        item.get("source", ""),
        item.get("file", ""),
        item.get("leak_type", ""),
        item.get("value", ""),
        sev,
        "True" if item.get("active") else ("False" if item.get("active") is not None else "?"),
        style=style,
    )
    console = Console()
    console.print(table)
    import sys
    sys.stdout.flush()


def print_progress(info: dict):
    """Show progress information for repository scanning."""
    repo = info.get("repo", "")
    total = info.get("total")
    index = info.get("index")
    if repo and total and index:
        msg = f"Scanning {repo} ({index}/{total})"
    elif repo:
        status = info.get("status", "")
        msg = f"{status.capitalize()} {repo}"
    else:
        msg = str(info)
    print(msg)
    import sys
    sys.stdout.flush()
