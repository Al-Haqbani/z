import subprocess
import tempfile


def extract_links(js_text):
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".js", delete=False) as tmp:
        tmp.write(js_text)
        tmp.flush()
        cmd = ["linkfinder", "-i", tmp.name, "-o", "cli"]
        try:
            output = subprocess.check_output(cmd, text=True)
            return output.splitlines()
        except Exception:
            return []
