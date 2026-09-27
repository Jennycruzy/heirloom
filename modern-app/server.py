"""Standard-library HTTP server for the Heirloom judge site and modern app.

One process serves everything a reviewer needs from a single origin:

- ``/``            the project landing page (``site/``)
- ``/app/``        the modernized clerk workspace (``modern-app/static/``)
- ``/dashboard/``  the source-reconstructed legacy screens (``dashboard/``)
- ``/evidence/``   committed, machine-readable evidence files
- ``/api/``        the SSC1 customer and SSP1 motor-policy JSON API
"""

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from database import (
    add_customer,
    add_motor_policy,
    count_records,
    delete_motor_policy,
    initialize_database,
    inquire_customer,
    inquire_motor_policy,
    update_customer,
    update_motor_policy,
)


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"
MAX_BODY_BYTES = 64 * 1024

# Exact public files. Nothing outside these files and the directories below is
# reachable over HTTP, so the database, tests and legacy source stay private.
PUBLIC_FILES = {
    "/": REPO_ROOT / "site" / "index.html",
    "/app/": STATIC_DIR / "index.html",
    "/dashboard/": REPO_ROOT / "dashboard" / "index.html",
    "/catalogue/genapp.json": REPO_ROOT / "catalogue" / "genapp.json",
    "/evidence/findings.json": REPO_ROOT / "evidence" / "findings.json",
    "/evidence/verification.json": REPO_ROOT / "evidence" / "verification.json",
    "/evidence/parity.json": REPO_ROOT / "parity" / "result.json",
    "/evidence/mapping.json": REPO_ROOT / "parity" / "mapping.json",
}
PUBLIC_DIRECTORIES = {
    "/assets/": REPO_ROOT / "site" / "assets",
    "/static/": STATIC_DIR,
    "/dashboard/": REPO_ROOT / "dashboard",
}
PUBLIC_EXTENSIONS = {
    ".css", ".html", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mjs", ".png",
    ".svg", ".txt", ".woff2",
}
PRIVATE_NAMES = {"test.mjs"}
REDIRECTS = {"/app": "/app/", "/dashboard": "/dashboard/"}

CONTENT_TYPES = {
    ".mjs": "text/javascript",
    ".js": "text/javascript",
    ".woff2": "font/woff2",
    ".svg": "image/svg+xml",
}

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; "
        "script-src 'self'; font-src 'self'; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


class ApiNotFound(Exception):
    """Raised when an API resource does not exist."""


def create_server(host="127.0.0.1", port=8080, db_path=None):
    initialize_database(db_path)
    server = ThreadingHTTPServer((host, port), RequestHandler)
    server.daemon_threads = True
    server.db_path = db_path
    return server


def resolve_public_path(path):
    """Map a URL path to a public file, or return None."""
    if path in PUBLIC_FILES:
        return PUBLIC_FILES[path]
    for prefix, directory in PUBLIC_DIRECTORIES.items():
        if not path.startswith(prefix):
            continue
        root = directory.resolve()
        candidate = (root / unquote(path.removeprefix(prefix))).resolve()
        if (
            candidate.is_relative_to(root)
            and candidate.suffix in PUBLIC_EXTENSIONS
            and candidate.name not in PRIVATE_NAMES
            and candidate.is_file()
        ):
            return candidate
    return None


def cache_policy(path):
    if path.suffix == ".woff2":
        return "public, max-age=604800"
    return "no-cache"


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "Heirloom"
    sys_version = ""

    def do_GET(self):
        self._dispatch("GET")

    def do_HEAD(self):
        self._dispatch("HEAD")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def end_headers(self):
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        super().end_headers()

    def _dispatch(self, method):
        parsed = urlsplit(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            self._dispatch_api(method, path, parsed.query)
            return
        if method not in {"GET", "HEAD"}:
            self._send_text(405, "Method not allowed", method)
            return
        if path in REDIRECTS:
            location = REDIRECTS[path] + (f"?{parsed.query}" if parsed.query else "")
            self.send_response(308)
            self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        public_file = resolve_public_path(path)
        if public_file is None or not public_file.is_file():
            self._send_text(404, "Not found", method)
            return
        self._serve_file(public_file, method)

    def _dispatch_api(self, method, path, query):
        try:
            result, status = self._run_api(method, path, query)
            self._send_json(status, {"data": result}, method)
        except ApiNotFound as error:
            self._send_json(404, {"error": str(error)}, method)
        except ValueError as error:
            self._send_json(400, {"error": str(error)}, method)
        except Exception as error:  # pragma: no cover - defensive server boundary
            print(f"Unexpected API error: {error!r}", flush=True)
            self._send_json(
                500, {"error": "The server could not complete the request"}, method
            )

    def _run_api(self, method, path, query):
        parts = [unquote(part) for part in path.strip("/").split("/")]
        db_path = self.server.db_path
        query_values = parse_qs(query, keep_blank_values=True)
        reading = method in {"GET", "HEAD"}

        if parts == ["api", "health"] and reading:
            return {"status": "ok", "records": count_records(db_path)}, 200

        if parts == ["api", "customers"] and method == "POST":
            return add_customer(self._read_json(), db_path), 201
        if len(parts) == 3 and parts[:2] == ["api", "customers"]:
            identifier = parts[2]
            if reading:
                record = inquire_customer(identifier, db_path)
                if record is None:
                    raise ApiNotFound("Customer not found")
                return record, 200
            if method == "PUT":
                try:
                    record = update_customer(identifier, self._read_json(), db_path)
                except ValueError as error:
                    if str(error) == "Customer does not exist":
                        raise ApiNotFound("Customer not found") from error
                    raise
                return record, 200

        if parts == ["api", "motor-policies"] and method == "POST":
            return add_motor_policy(self._read_json(), db_path), 201
        if len(parts) == 3 and parts[:2] == ["api", "motor-policies"]:
            identifier = parts[2]
            if reading:
                customer_number = self._customer_number(query_values)
                record = inquire_motor_policy(
                    identifier, db_path, customer_number=customer_number
                )
                if record is None:
                    raise ApiNotFound("Motor policy not found")
                return record, 200
            if method == "PUT":
                try:
                    record = update_motor_policy(
                        identifier, self._read_json(), db_path
                    )
                except ValueError as error:
                    if str(error) == "Motor policy does not exist":
                        raise ApiNotFound("Motor policy not found") from error
                    raise
                return record, 200
            if method == "DELETE":
                customer_number = self._customer_number(query_values)
                try:
                    record = delete_motor_policy(
                        identifier, db_path, customer_number=customer_number
                    )
                except ValueError as error:
                    if str(error) == "Motor policy does not exist":
                        raise ApiNotFound("Motor policy not found") from error
                    raise
                return record, 200

        raise ApiNotFound("API route not found")

    @staticmethod
    def _customer_number(query_values):
        values = query_values.get("customer_number", [])
        if len(values) != 1 or not values[0].strip():
            raise ValueError("customer_number query parameter is required")
        return values[0]

    def _read_json(self):
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json")
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Content-Length is required")
        try:
            length = int(raw_length)
        except ValueError as error:
            raise ValueError("Content-Length must be an integer") from error
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("Request body must be no larger than 64 KiB")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Request body must contain valid UTF-8 JSON") from error
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object")
        return data

    def _serve_file(self, path, method):
        content = path.read_bytes()
        mime_type = (
            CONTENT_TYPES.get(path.suffix)
            or mimetypes.guess_type(path.name)[0]
            or "application/octet-stream"
        )
        if mime_type.startswith("text/") or mime_type == "application/json":
            mime_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", cache_policy(path))
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(content)

    def _send_json(self, status, payload, method="GET"):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(content)

    def _send_text(self, status, message, method="GET"):
        content = f"{message}\n".encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        if status == 405:
            self.send_header("Allow", "GET, HEAD")
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(content)

    def log_message(self, _format, *_args):
        return


def main():
    parser = argparse.ArgumentParser(description="Run the Heirloom site and app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db")
    arguments = parser.parse_args()
    server = create_server(arguments.host, arguments.port, arguments.db)
    base = f"http://{arguments.host}:{arguments.port}"
    print(f"Heirloom landing page:   {base}/")
    print(f"Clerk workspace:         {base}/app/")
    print(f"Legacy screen dashboard: {base}/dashboard/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
