"""Standard-library HTTP server for the first-pass modernized application."""

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from database import (
    add_customer,
    add_motor_policy,
    delete_motor_policy,
    initialize_database,
    inquire_customer,
    inquire_motor_policy,
    update_customer,
    update_motor_policy,
)


STATIC_DIR = Path(__file__).parent / "static"
MAX_BODY_BYTES = 64 * 1024


class ApiNotFound(Exception):
    """Raised when an API resource does not exist."""


def create_server(host="127.0.0.1", port=8080, db_path=None):
    initialize_database(db_path)
    server = ThreadingHTTPServer((host, port), RequestHandler)
    server.db_path = db_path
    return server


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def _dispatch(self, method):
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/" and method == "GET":
            self._serve_file(STATIC_DIR / "index.html")
            return
        if path.startswith("/static/") and method == "GET":
            self._serve_static(path.removeprefix("/static/"))
            return
        if path.startswith("/api/"):
            self._dispatch_api(method, path, parsed.query)
            return
        self.send_error(404, "Not found")

    def _dispatch_api(self, method, path, query):
        try:
            result, status = self._run_api(method, path, query)
            self._send_json(status, {"data": result})
        except ApiNotFound as error:
            self._send_json(404, {"error": str(error)})
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
        except Exception as error:  # pragma: no cover - defensive server boundary
            print(f"Unexpected API error: {error}")
            self._send_json(500, {"error": "The server could not complete the request"})

    def _run_api(self, method, path, query):
        parts = [unquote(part) for part in path.strip("/").split("/")]
        db_path = self.server.db_path
        query_values = parse_qs(query, keep_blank_values=True)

        if parts == ["api", "customers"] and method == "POST":
            return add_customer(self._read_json(), db_path), 201
        if len(parts) == 3 and parts[:2] == ["api", "customers"]:
            identifier = parts[2]
            if method == "GET":
                record = inquire_customer(identifier, db_path)
                if record is None:
                    raise ApiNotFound("Customer not found")
                return record, 200
            if method == "PUT":
                return update_customer(identifier, self._read_json(), db_path), 200

        if parts == ["api", "motor-policies"] and method == "POST":
            return add_motor_policy(self._read_json(), db_path), 201
        if len(parts) == 3 and parts[:2] == ["api", "motor-policies"]:
            identifier = parts[2]
            if method == "GET":
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

    def _serve_static(self, relative_path):
        root = STATIC_DIR.resolve()
        candidate = (root / unquote(relative_path)).resolve()
        if not candidate.is_relative_to(root):
            self.send_error(404, "Not found")
            return
        self._serve_file(candidate)

    def _serve_file(self, path):
        if not path.is_file():
            self.send_error(404, "Not found")
            return
        content = path.read_bytes()
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if mime_type.startswith("text/") or mime_type in {
            "application/javascript",
            "application/json",
        }:
            mime_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status, payload):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, _format, *_args):
        return


def main():
    parser = argparse.ArgumentParser(description="Run the Heirloom modern app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db")
    arguments = parser.parse_args()
    server = create_server(arguments.host, arguments.port, arguments.db)
    print(f"Modern app available at http://{arguments.host}:{arguments.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
