"""
These are invented hackathon test records, not records extracted from or
produced by a running mainframe.
"""

from database import add_customer, add_motor_policy, reset_database


CUSTOMERS = [
    {
        "customer_number": "CUST000001",
        "first_name": "Alice",
        "last_name": "Smith",
        "date_of_birth": "1990-01-01",
        "house_name": "Maple House",
        "house_number": "123",
        "postcode": "SW1A 1AA",
        "home_phone": "1234567890",
        "mobile_phone": "0987654321",
        "email": "alice.smith@example.com",
    },
    {
        "customer_number": "CUST000002",
        "first_name": "Bob",
        "last_name": "Johnson",
        "date_of_birth": "1985-05-15",
        "house_name": "Oak Cottage",
        "house_number": "456",
        "postcode": "NW1 1BB",
        "home_phone": "5551234567",
        "mobile_phone": "5557654321",
        "email": "bob.johnson@example.com",
    },
]

MOTOR_POLICIES = [
    {
        "policy_number": "POL001",
        "customer_number": "CUST000001",
        "issue_date": "2023-01-01",
        "expiry_date": "2024-01-01",
        "car_make": "Toyota",
        "car_model": "Camry",
        "car_value": "25000",
        "registration": "ABC1234",
        "car_colour": "Silver",
        "engine_cc": "2000",
        "manufacture_date": "2020-01-01",
        "accident_count": "0",
        "policy_premium": "1200",
    },
    {
        "policy_number": "POL002",
        "customer_number": "CUST000002",
        "issue_date": "2022-06-15",
        "expiry_date": "2023-06-15",
        "car_make": "Ford",
        "car_model": "Mustang",
        "car_value": "35000",
        "registration": "XYZ7890",
        "car_colour": "Red",
        "engine_cc": "5000",
        "manufacture_date": "2018-01-01",
        "accident_count": "1",
        "policy_premium": "1800",
    },
]


def seed_database(db_path=None):
    reset_database(db_path)
    for customer in CUSTOMERS:
        add_customer(customer, db_path)
    for policy in MOTOR_POLICIES:
        add_motor_policy(policy, db_path)
    return {"customers": len(CUSTOMERS), "motor_policies": len(MOTOR_POLICIES)}


if __name__ == "__main__":
    result = seed_database()
    print(
        f"Seeded {result['customers']} customers and "
        f"{result['motor_policies']} motor policies as invented test records."
    )
