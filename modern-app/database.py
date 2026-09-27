"""SQLite data layer for the first-pass SSC1 and SSP1 modernization."""

import sqlite3
from collections import OrderedDict
from pathlib import Path


DB_PATH = Path(__file__).parent / "db" / "heirloom.sqlite3"

CUSTOMER_FIELDS = OrderedDict(
    [
        ("customer_number", 10),
        ("first_name", 10),
        ("last_name", 20),
        ("date_of_birth", 10),
        ("house_name", 20),
        ("house_number", 4),
        ("postcode", 8),
        ("home_phone", 20),
        ("mobile_phone", 20),
        ("email", 27),
    ]
)

MOTOR_POLICY_FIELDS = OrderedDict(
    [
        ("policy_number", 10),
        ("customer_number", 10),
        ("issue_date", 10),
        ("expiry_date", 10),
        ("car_make", 20),
        ("car_model", 20),
        ("car_value", 6),
        ("registration", 7),
        ("car_colour", 8),
        ("engine_cc", 8),
        ("manufacture_date", 10),
        ("accident_count", 6),
        ("policy_premium", 6),
    ]
)


def connect(db_path=None):
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _columns(fields, primary_key):
    definitions = []
    for name, maximum in fields.items():
        parts = [name, "TEXT"]
        if name == primary_key:
            parts.append("PRIMARY KEY")
        parts.append(f"CHECK (length({name}) <= {maximum})")
        definitions.append(" ".join(parts))
    return definitions


def _create_schema(connection):
    customer_columns = ",\n                ".join(
        _columns(CUSTOMER_FIELDS, "customer_number")
    )
    policy_columns = _columns(MOTOR_POLICY_FIELDS, "policy_number")
    policy_columns.append(
        "FOREIGN KEY (customer_number) REFERENCES customers (customer_number)"
    )
    motor_columns = ",\n                ".join(policy_columns)
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS customers (
            {customer_columns}
        );
        CREATE TABLE IF NOT EXISTS motor_policies (
            {motor_columns}
        );
        """
    )


def initialize_database(db_path=None):
    with connect(db_path) as connection:
        _create_schema(connection)


def reset_database(db_path=None):
    with connect(db_path) as connection:
        connection.execute("DROP TABLE IF EXISTS motor_policies")
        connection.execute("DROP TABLE IF EXISTS customers")
        _create_schema(connection)


def _validated_payload(
    data,
    fields,
    *,
    require_all=False,
    forbidden=(),
    nonblank=(),
    uppercase=(),
):
    if not isinstance(data, dict):
        raise ValueError("Payload must be an object")
    unknown = sorted(set(data) - set(fields))
    if unknown:
        raise ValueError(f"Unknown field(s): {', '.join(unknown)}")
    if require_all:
        missing = [field for field in fields if field not in data]
        if missing:
            raise ValueError(f"Missing field(s): {', '.join(missing)}")
    rejected = [field for field in forbidden if field in data]
    if rejected:
        raise ValueError(f"Field cannot be changed: {', '.join(rejected)}")
    if not data:
        raise ValueError("At least one field is required")

    clean = {}
    for field, value in data.items():
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")
        if len(value) > fields[field]:
            raise ValueError(
                f"{field} must be at most {fields[field]} characters"
            )
        clean[field] = value.upper() if field in uppercase else value

    for field in nonblank:
        if field in clean and not clean[field].strip():
            raise ValueError(f"{field} must not be blank")
    return clean


def _integrity_error(error, entity):
    message = str(error).lower()
    if "foreign key" in message:
        return ValueError("Referenced customer does not exist")
    if "unique" in message:
        return ValueError(f"A {entity} with that identifier already exists")
    return ValueError(f"Could not save {entity}")


def _insert(table, fields, data, db_path, entity):
    names = list(fields)
    placeholders = ", ".join("?" for _ in names)
    try:
        with connect(db_path) as connection:
            connection.execute(
                f"INSERT INTO {table} ({', '.join(names)}) VALUES ({placeholders})",
                [data[name] for name in names],
            )
    except sqlite3.IntegrityError as error:
        raise _integrity_error(error, entity) from None


def _seed_customer(data, db_path=None):
    """Insert one deterministic invented fixture with its documented ID."""
    clean = _validated_payload(
        data,
        CUSTOMER_FIELDS,
        require_all=True,
        nonblank=("customer_number",),
        uppercase=("postcode",),
    )
    _insert("customers", CUSTOMER_FIELDS, clean, db_path, "customer")
    return inquire_customer(clean["customer_number"], db_path)


def _seed_motor_policy(data, db_path=None):
    """Insert one deterministic invented fixture with its documented ID."""
    clean = _validated_payload(
        data,
        MOTOR_POLICY_FIELDS,
        require_all=True,
        nonblank=("policy_number", "customer_number"),
    )
    _insert(
        "motor_policies",
        MOTOR_POLICY_FIELDS,
        clean,
        db_path,
        "motor policy",
    )
    return inquire_motor_policy(
        clean["policy_number"],
        db_path,
        customer_number=clean["customer_number"],
    )


def _next_identifier(connection, table, primary_key):
    values = connection.execute(
        f"SELECT {primary_key} FROM {table}"
    ).fetchall()
    numeric = [int(row[0]) for row in values if row[0].isdigit()]
    next_value = max(numeric, default=0) + 1
    if next_value > 9_999_999_999:
        raise ValueError(f"No {primary_key} identifiers remain")
    return f"{next_value:010d}"


def _insert_with_generated_identifier(
    table, fields, primary_key, data, db_path, entity
):
    names = list(fields)
    try:
        with connect(db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            identifier = _next_identifier(connection, table, primary_key)
            record = {primary_key: identifier, **data}
            placeholders = ", ".join("?" for _ in names)
            connection.execute(
                f"INSERT INTO {table} ({', '.join(names)}) VALUES ({placeholders})",
                [record[name] for name in names],
            )
    except sqlite3.IntegrityError as error:
        raise _integrity_error(error, entity) from None
    return identifier


def add_customer(data, db_path=None):
    add_fields = OrderedDict(
        (name, maximum)
        for name, maximum in CUSTOMER_FIELDS.items()
        if name != "customer_number"
    )
    clean = _validated_payload(
        data,
        add_fields,
        require_all=True,
        uppercase=("postcode",),
    )
    identifier = _insert_with_generated_identifier(
        "customers",
        CUSTOMER_FIELDS,
        "customer_number",
        clean,
        db_path,
        "customer",
    )
    return inquire_customer(identifier, db_path)


def inquire_customer(customer_number, db_path=None):
    if not isinstance(customer_number, str) or not customer_number.strip():
        raise ValueError("customer_number must not be blank")
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM customers WHERE customer_number = ?",
            (customer_number,),
        ).fetchone()
    return dict(row) if row is not None else None


def _update(table, primary_key, identifier, data, db_path, entity):
    assignments = ", ".join(f"{field} = ?" for field in data)
    try:
        with connect(db_path) as connection:
            cursor = connection.execute(
                f"UPDATE {table} SET {assignments} WHERE {primary_key} = ?",
                [*data.values(), identifier],
            )
            if cursor.rowcount == 0:
                raise ValueError(f"{entity.capitalize()} does not exist")
    except sqlite3.IntegrityError as error:
        raise _integrity_error(error, entity) from None


def update_customer(customer_number, data, db_path=None):
    clean = _validated_payload(
        data,
        CUSTOMER_FIELDS,
        forbidden=("customer_number",),
        uppercase=("postcode",),
    )
    _update(
        "customers", "customer_number", customer_number, clean, db_path, "customer"
    )
    return inquire_customer(customer_number, db_path)


def add_motor_policy(data, db_path=None):
    add_fields = OrderedDict(
        (name, maximum)
        for name, maximum in MOTOR_POLICY_FIELDS.items()
        if name != "policy_number"
    )
    clean = _validated_payload(
        data,
        add_fields,
        require_all=True,
        nonblank=("customer_number",),
    )
    identifier = _insert_with_generated_identifier(
        "motor_policies",
        MOTOR_POLICY_FIELDS,
        "policy_number",
        clean,
        db_path,
        "motor policy",
    )
    return inquire_motor_policy(
        identifier, db_path, customer_number=clean["customer_number"]
    )


def inquire_motor_policy(policy_number, db_path=None, customer_number=None):
    if not isinstance(policy_number, str) or not policy_number.strip():
        raise ValueError("policy_number must not be blank")
    with connect(db_path) as connection:
        if customer_number is None:
            row = connection.execute(
                "SELECT * FROM motor_policies WHERE policy_number = ?",
                (policy_number,),
            ).fetchone()
        else:
            row = connection.execute(
                """SELECT * FROM motor_policies
                   WHERE policy_number = ? AND customer_number = ?""",
                (policy_number, customer_number),
            ).fetchone()
    return dict(row) if row is not None else None


def update_motor_policy(policy_number, data, db_path=None):
    clean = _validated_payload(
        data,
        MOTOR_POLICY_FIELDS,
        forbidden=("policy_number",),
        nonblank=("customer_number",),
    )
    if "customer_number" not in clean:
        raise ValueError("customer_number is required for motor policy update")
    assignments = ", ".join(f"{field} = ?" for field in clean)
    try:
        with connect(db_path) as connection:
            cursor = connection.execute(
                f"""UPDATE motor_policies SET {assignments}
                    WHERE policy_number = ? AND customer_number = ?""",
                [*clean.values(), policy_number, clean["customer_number"]],
            )
            if cursor.rowcount == 0:
                raise ValueError("Motor policy does not exist")
    except sqlite3.IntegrityError as error:
        raise _integrity_error(error, "motor policy") from None
    return inquire_motor_policy(
        policy_number, db_path, customer_number=clean["customer_number"]
    )


def delete_motor_policy(policy_number, db_path=None, customer_number=None):
    record = inquire_motor_policy(
        policy_number, db_path, customer_number=customer_number
    )
    if record is None:
        raise ValueError("Motor policy does not exist")
    with connect(db_path) as connection:
        if customer_number is None:
            connection.execute(
                "DELETE FROM motor_policies WHERE policy_number = ?",
                (policy_number,),
            )
        else:
            connection.execute(
                """DELETE FROM motor_policies
                   WHERE policy_number = ? AND customer_number = ?""",
                (policy_number, customer_number),
            )
    return record
