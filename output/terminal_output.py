from rich.table import Table
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from core.regex_patterns import get_severity

SEVERITY_ICON = {
    "high": "\U0001F534",  # red circle
    "medium": "\U0001F7E0",  # orange circle
    "low": "\U0001F7E1",  # yellow circle
    "info": "\U0001F535",  # blue circle
}


def _assign_severity(leak_type: str) -> str:
    return get_severity(leak_type)


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
        sev_display = f"{SEVERITY_ICON.get(sev.lower(), '')} {sev}"
        table.add_row(
            str(idx),
            item.get("source", ""),
            item.get("file", ""),
            item.get("leak_type", ""),
            item.get("value", ""),
            sev_display,
            "True" if item.get("active") else ("False" if item.get("active") is not None else "?"),
            style=style,
        )
    console = Console()
    console.print(table)
    # Ensure output appears immediately
    import sys
    sys.stdout.flush()


# progress bar helpers
_progress = None
_task = None

def _start_bar(total):
    global _progress, _task
    if _progress is None:
        _progress = Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
        )
        _progress.start()
        _task = _progress.add_task("Scanning", total=total)

def _update_bar(idx):
    if _progress and _task:
        _progress.update(_task, completed=idx)

def _stop_bar():
    global _progress, _task
    if _progress:
        _progress.stop()
        _progress = None
        _task = None


def print_result(item, idx=None):
    """Print a single result immediately."""
    idx = idx or 1
    sev = item.get("severity") or _assign_severity(item.get("leak_type", ""))
    style = "red" if sev == "high" else "yellow"
    sev_display = f"{SEVERITY_ICON.get(sev.lower(), '')} {sev}"
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
        sev_display,
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
        if index == 1:
            _start_bar(total)
        _update_bar(index)
        msg = f"Scanning {repo} ({index}/{total})"
        if index == total:
            _stop_bar()
    elif repo:
        status = info.get("status", "")
        msg = f"{status.capitalize()} {repo}"
    else:
        msg = str(info)
    print(msg)
    import sys
    sys.stdout.flush()

def print_summary(results):
    """Print a summary table with leak counts by severity."""
    counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
    for item in results:
        sev = item.get("severity") or _assign_severity(item.get("leak_type", ""))
        sev = sev.lower()
        if sev in counts:
            counts[sev] += 1
        else:
            counts.setdefault(sev, 0)
            counts[sev] += 1
    table = Table(title="Leak Summary")
    table.add_column("Severity")
    table.add_column("Count", style="cyan")
    for sev in ["high", "medium", "low", "info"]:
        icon = SEVERITY_ICON.get(sev, "")
        table.add_row(f"{icon} {sev.capitalize()}", str(counts.get(sev, 0)))
    console = Console()
    console.print(table)
    import sys
    sys.stdout.flush()
