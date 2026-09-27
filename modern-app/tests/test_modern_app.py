import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode


APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import database
import seed
import server


class TemporaryDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temporary_directory.name) / "test.sqlite3"
        seed.seed_database(self.db_path)

    def tearDown(self):
        self.temporary_directory.cleanup()


class DatabaseTests(TemporaryDatabaseTest):
    def test_add_customer_assigns_identifier(self):
        customer = {field: "" for field in database.CUSTOMER_FIELDS}
        customer.pop("customer_number")
        customer["first_name"] = "Generated"

        added = database.add_customer(customer, self.db_path)

        self.assertEqual(added["customer_number"], "0000000001")
        self.assertEqual(added["first_name"], "Generated")

    def test_add_motor_policy_assigns_identifier(self):
        policy = {field: "" for field in database.MOTOR_POLICY_FIELDS}
        policy.pop("policy_number")
        policy.update(customer_number="CUST000001", car_make="Generated")

        added = database.add_motor_policy(policy, self.db_path)

        self.assertEqual(added["policy_number"], "0000000001")
        self.assertEqual(added["customer_number"], "CUST000001")

    def test_seeded_customer_can_be_inquired_and_partially_updated(self):
        customer = database.inquire_customer("CUST000001", self.db_path)
        self.assertEqual(customer["first_name"], "Alice")

        updated = database.update_customer(
            "CUST000001", {"postcode": "zz1 1zz"}, self.db_path
        )
        self.assertEqual(updated["postcode"], "ZZ1 1ZZ")
        self.assertEqual(updated["last_name"], "Smith")

    def test_motor_policy_can_be_added_updated_and_deleted(self):
        policy = {
            field: "" for field in database.MOTOR_POLICY_FIELDS
        }
        policy.pop("policy_number")
        policy.update(customer_number="CUST000001", car_make="Fiction")
        added = database.add_motor_policy(policy, self.db_path)
        identifier = added["policy_number"]

        update = dict(policy)
        update["car_colour"] = "Blue"
        updated = database.update_motor_policy(
            identifier, update, self.db_path
        )
        self.assertEqual(updated["car_colour"], "Blue")
        self.assertEqual(
            database.delete_motor_policy(
                identifier, self.db_path, customer_number="CUST000001"
            ),
            updated,
        )
        self.assertIsNone(database.inquire_motor_policy(identifier, self.db_path))

    def test_validation_rejects_unknown_and_overlength_fields(self):
        with self.assertRaisesRegex(ValueError, "Unknown field"):
            database.update_customer(
                "CUST000001", {"invented_field": "value"}, self.db_path
            )
        with self.assertRaisesRegex(ValueError, "at most 10 characters"):
            database.update_customer(
                "CUST000001", {"first_name": "elevenchars"}, self.db_path
            )


class HttpTests(TemporaryDatabaseTest):
    def setUp(self):
        super().setUp()
        self.httpd = server.create_server("127.0.0.1", 0, self.db_path)
        self.thread = threading.Thread(
            target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
        )
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.httpd.server_port, timeout=5
        )

    def tearDown(self):
        self.connection.close()
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        super().tearDown()

    def request(self, method, path, payload=None):
        headers = {}
        body = None
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        self.connection.request(method, path, body=body, headers=headers)
        response = self.connection.getresponse()
        content = response.read()
        return response, content

    def test_home_page_and_javascript_are_served(self):
        response, content = self.request("GET", "/")
        self.assertEqual(response.status, 200)
        self.assertIn(b"Can the clerk still do their job?", content)

        response, content = self.request("GET", "/app/")
        self.assertEqual(response.status, 200)
        self.assertIn(b"Heirloom Modern", content)

        response, content = self.request("GET", "/static/app.js")
        self.assertEqual(response.status, 200)
        self.assertIn(b"CUST000001", content)
        self.assertTrue(response.getheader("Content-Type").startswith("text/javascript"))

        response, content = self.request("GET", "/static/workflows.mjs")
        self.assertEqual(response.status, 200)
        self.assertIn(b"load-update", content)

    def test_dashboard_and_evidence_share_the_same_origin(self):
        response, content = self.request("GET", "/dashboard/")
        self.assertEqual(response.status, 200)
        self.assertIn(b"lib.mjs", self.request("GET", "/dashboard/app.mjs")[1])

        response, content = self.request("GET", "/catalogue/genapp.json")
        self.assertEqual(response.status, 200)
        self.assertEqual(len(json.loads(content)["screens"]), 6)

        response, content = self.request("GET", "/evidence/findings.json")
        self.assertEqual(response.status, 200)
        self.assertEqual(len(json.loads(content)["findings"]), 6)

        response, content = self.request("GET", "/evidence/mapping.json")
        self.assertEqual(response.status, 200)
        self.assertEqual(set(json.loads(content)), {"SSC1", "SSP1"})

        response, _ = self.request("GET", "/app")
        self.assertEqual(response.status, 308)
        self.assertEqual(response.getheader("Location"), "/app/")

    def test_every_page_shares_one_menu(self):
        menus = {}
        for page in server.SITE_PAGES:
            with self.subTest(page=page):
                response, content = self.request("GET", page)
                self.assertEqual(response.status, 200)
                html = content.decode("utf-8")
                start = html.index('<nav id="site-nav"')
                menu = html[start:html.index("</nav>", start)]
                menus[page] = menu.replace(' aria-current="page"', "")
                self.assertIn('src="/assets/nav.mjs"', html)
        self.assertEqual(len(set(menus.values())), 1, "pages must share the same menu")

        response, _ = self.request("GET", "/findings")
        self.assertEqual(response.status, 308)
        self.assertEqual(response.getheader("Location"), "/findings/")

    def test_private_files_are_never_served(self):
        for path in (
            "/dashboard/test.mjs",
            "/dashboard/README.md",
            "/static/../database.py",
            "/static/%2e%2e/server.py",
            "/assets/../index.html",
            "/modern-app/database.py",
            "/legacy/cics-genapp/base/src/lgtestc1.cbl",
            "/evidence/../README.md",
            "/.env",
        ):
            with self.subTest(path=path):
                response, _ = self.request("GET", path)
                self.assertEqual(response.status, 404)

    def test_responses_carry_security_headers_and_support_head(self):
        response, content = self.request("HEAD", "/")
        self.assertEqual(response.status, 200)
        self.assertEqual(content, b"")
        self.assertGreater(int(response.getheader("Content-Length")), 0)
        self.assertIn("default-src 'self'", response.getheader("Content-Security-Policy"))
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")

        response, _ = self.request("POST", "/")
        self.assertEqual(response.status, 405)

        response, _ = self.request("GET", "/api/customers/CUST000001")
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_health_reports_record_counts(self):
        response, content = self.request("GET", "/api/health")
        self.assertEqual(response.status, 200)
        self.assertEqual(
            json.loads(content)["data"],
            {"status": "ok", "records": {"customers": 2, "motor_policies": 2}},
        )

    def test_updating_a_missing_customer_is_not_found(self):
        response, content = self.request(
            "PUT", "/api/customers/CUST999999", {"first_name": "Nobody"}
        )
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(content), {"error": "Customer not found"})

    def test_customer_inquiry_returns_seeded_record(self):
        response, content = self.request("GET", "/api/customers/CUST000001")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "application/json; charset=utf-8")
        self.assertEqual(json.loads(content)["data"]["last_name"], "Smith")

    def test_motor_inquiry_and_missing_api_route_use_json(self):
        query = urlencode({"customer_number": "CUST000001"})
        response, content = self.request(
            "GET", f"/api/motor-policies/POL001?{query}"
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)["data"]["customer_number"], "CUST000001")

        response, content = self.request("GET", "/api/customers")
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(content), {"error": "API route not found"})

    def test_post_requires_json_and_returns_created_record(self):
        customer = {field: "" for field in database.CUSTOMER_FIELDS}
        customer.pop("customer_number")
        customer.update(first_name="Fiction")
        response, content = self.request("POST", "/api/customers", customer)
        self.assertEqual(response.status, 201)
        self.assertEqual(json.loads(content)["data"]["customer_number"], "0000000001")

        self.connection.request("POST", "/api/customers", body="{}")
        response = self.connection.getresponse()
        content = response.read()
        self.assertEqual(response.status, 400)
        self.assertEqual(
            json.loads(content)["error"], "Content-Type must be application/json"
        )

    def test_customer_add_update_inquire_lifecycle(self):
        customer = {field: "" for field in database.CUSTOMER_FIELDS}
        customer.pop("customer_number")
        customer.update(
            first_name="Fiction",
            postcode="ab1 2cd",
        )

        response, content = self.request("POST", "/api/customers", customer)
        self.assertEqual(response.status, 201)
        created = json.loads(content)["data"]
        identifier = created["customer_number"]
        self.assertEqual(created["postcode"], "AB1 2CD")

        update = {
            field: value
            for field, value in customer.items()
            if field != "customer_number"
        }
        update["last_name"] = "Updated"
        response, content = self.request(
            "PUT", f"/api/customers/{identifier}", update
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)["data"]["last_name"], "Updated")

        response, content = self.request("GET", f"/api/customers/{identifier}")
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)["data"]["first_name"], "Fiction")

        response, content = self.request("DELETE", f"/api/customers/{identifier}")
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(content), {"error": "API route not found"})

    def test_motor_policy_add_update_inquire_delete_lifecycle(self):
        policy = {field: "" for field in database.MOTOR_POLICY_FIELDS}
        policy.pop("policy_number")
        policy.update(
            customer_number="CUST000001",
            car_make="Fiction",
        )

        response, content = self.request("POST", "/api/motor-policies", policy)
        self.assertEqual(response.status, 201)
        created = json.loads(content)["data"]
        identifier = created["policy_number"]
        self.assertEqual(created["car_make"], "Fiction")

        update = {
            field: value
            for field, value in policy.items()
            if field != "policy_number"
        }
        update["car_colour"] = "Blue"
        response, content = self.request(
            "PUT", f"/api/motor-policies/{identifier}", update
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)["data"]["car_colour"], "Blue")

        query = urlencode({"customer_number": "CUST000001"})
        response, content = self.request(
            "GET", f"/api/motor-policies/{identifier}?{query}"
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)["data"]["customer_number"], "CUST000001")

        response, content = self.request(
            "DELETE", f"/api/motor-policies/{identifier}?{query}"
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)["data"]["policy_number"], identifier)

        response, content = self.request(
            "GET", f"/api/motor-policies/{identifier}?{query}"
        )
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(content), {"error": "Motor policy not found"})

    def test_motor_policy_requires_an_existing_customer(self):
        policy = {field: "" for field in database.MOTOR_POLICY_FIELDS}
        policy.pop("policy_number")
        policy.update(
            customer_number="MISSING001",
        )
        response, content = self.request("POST", "/api/motor-policies", policy)
        self.assertEqual(response.status, 400)
        self.assertEqual(
            json.loads(content), {"error": "Referenced customer does not exist"}
        )

    def test_motor_inquiry_requires_matching_customer_and_policy(self):
        query = urlencode({"customer_number": "CUST000002"})
        response, content = self.request(
            "GET", f"/api/motor-policies/POL001?{query}"
        )
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(content), {"error": "Motor policy not found"})

    def test_motor_delete_does_not_remove_another_customers_policy(self):
        query = urlencode({"customer_number": "CUST000002"})
        response, content = self.request(
            "DELETE", f"/api/motor-policies/POL001?{query}"
        )
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(content), {"error": "Motor policy not found"})
        self.assertIsNotNone(database.inquire_motor_policy("POL001", self.db_path))

    def test_motor_update_uses_customer_and_policy_as_the_key(self):
        policy = database.inquire_motor_policy("POL001", self.db_path)
        update = {
            field: value
            for field, value in policy.items()
            if field != "policy_number"
        }
        update["customer_number"] = "CUST000002"
        update["car_colour"] = "Blue"

        response, content = self.request(
            "PUT", "/api/motor-policies/POL001", update
        )

        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(content), {"error": "Motor policy not found"})
        unchanged = database.inquire_motor_policy("POL001", self.db_path)
        self.assertEqual(unchanged["customer_number"], "CUST000001")
        self.assertEqual(unchanged["car_colour"], "Silver")


if __name__ == "__main__":
    unittest.main()
