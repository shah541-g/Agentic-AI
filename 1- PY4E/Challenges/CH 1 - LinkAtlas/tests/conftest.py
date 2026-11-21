"""Session-wide fake site test fixture using ThreadingHTTPServer."""
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
import pytest


class FakeSiteHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Record request path
        self.server.requests.append(self.path)

        path_clean = self.path.split("?")[0]

        if path_clean == "/robots.txt":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"User-agent: *\nDisallow: /private/\n")

        elif path_clean == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Home Page</title></head>
            <body>
                <a href="/a">Page A</a>
                <a href="/slow">Slow Page</a>
                <a href="/missing">Missing Page</a>
                <a href="/private/secret">Secret</a>
                <a href="/file.pdf">PDF Document</a>
                <a href="/old">Old Redirect</a>
                <a href="/redir-ext">External Redirect</a>
                <a href="mailto:hi@x.com">Email</a>
                <a href="tel:123">Phone</a>
                <a href="#top">Top Anchor</a>
                <a href="https://external-one.test/page?utm_source=x">External 1</a>
                <a href="https://www.external-two.test/">External 2</a>
                <a href="/a#section">Page A Again</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path_clean == "/a":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Page A</title></head>
            <body>
                <a href="/c">Page C</a>
                <a href="/">Home</a>
                <a href="https://external-one.test/page">External 1 Again</a>
                <a href="https://external-three.test/x">External 3</a>
                <a rel="nofollow" href="/nf">NoFollow Page</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path_clean == "/c":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Page C</title></head>
            <body>
                <a href="/d">Page D</a>
                <a href="https://external-four.test/">External 4</a>
                <a href="/a">Page A</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path_clean == "/slow":
            # Sleep 2.0s to trigger crawler timeout (configured at 0.5s)
            time.sleep(2.0)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body>Slow Page</body></html>")

        elif path_clean == "/missing":
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>404 Not Found</body></html>")

        elif path_clean == "/old":
            self.send_response(301)
            self.send_header("Location", "/a")
            self.end_headers()

        elif path_clean == "/redir-ext":
            self.send_response(302)
            self.send_header("Location", "https://external-five.test/landing")
            self.end_headers()

        else:
            # For /nf, /d, /private/secret, /file.pdf if ever requested
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Other</body></html>")

    def log_message(self, format, *args):
        # Suppress server access log messages during tests
        pass


@pytest.fixture(scope="session")
def fake_site():
    """Start local ThreadingHTTPServer on 127.0.0.1 with random free port."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeSiteHandler)
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    port = server.server_port
    server.url = f"http://127.0.0.1:{port}/"

    yield server

    server.shutdown()
    server.server_close()
