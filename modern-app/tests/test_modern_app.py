import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path


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
        policy.update(
            policy_number="TESTPOL001",
            customer_number="CUST000001",
            car_make="Fiction",
        )
        added = database.add_motor_policy(policy, self.db_path)
        self.assertEqual(added["policy_number"], "TESTPOL001")

        updated = database.update_motor_policy(
            "TESTPOL001", {"car_colour": "Blue"}, self.db_path
        )
        self.assertEqual(updated["car_colour"], "Blue")
        self.assertEqual(
            database.delete_motor_policy("TESTPOL001", self.db_path), updated
        )
        self.assertIsNone(database.inquire_motor_policy("TESTPOL001", self.db_path))

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
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
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
        self.assertIn(b"Heirloom Modern", content)

        response, content = self.request("GET", "/static/app.js")
        self.assertEqual(response.status, 200)
        self.assertIn(b"CUST000001", content)

    def test_customer_inquiry_returns_seeded_record(self):
        response, content = self.request("GET", "/api/customers/CUST000001")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "application/json; charset=utf-8")
        self.assertEqual(json.loads(content)["data"]["last_name"], "Smith")

    def test_motor_inquiry_and_missing_api_route_use_json(self):
        response, content = self.request("GET", "/api/motor-policies/POL001")
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(content)["data"]["customer_number"], "CUST000001")

        response, content = self.request("GET", "/api/customers")
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(content), {"error": "API route not found"})

    def test_post_requires_json_and_returns_created_record(self):
        customer = {
            field: "" for field in database.CUSTOMER_FIELDS
        }
        customer.update(customer_number="TESTCUST01", first_name="Fiction")
        response, content = self.request("POST", "/api/customers", customer)
        self.assertEqual(response.status, 201)
        self.assertEqual(json.loads(content)["data"]["customer_number"], "TESTCUST01")

        self.connection.request("POST", "/api/customers", body="{}")
        response = self.connection.getresponse()
        content = response.read()
        self.assertEqual(response.status, 400)
        self.assertEqual(
            json.loads(content)["error"], "Content-Type must be application/json"
        )


if __name__ == "__main__":
    unittest.main()
