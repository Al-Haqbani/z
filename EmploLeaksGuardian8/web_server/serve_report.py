from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import webbrowser


def serve_report(path="report.html", port=8000):
    """Serve the given report via a simple HTTP server."""
    abs_path = os.path.abspath(path)
    directory = os.path.dirname(abs_path)
    os.chdir(directory)
    url = f"http://localhost:{port}/{os.path.basename(abs_path)}"
    print(f"\nReport available at {url}\nPress Ctrl+C to stop the server.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve_report()
