# Stage 3 parity report

Date: 27 September 2026

## Scope and evidence boundary

This assessment compares the modern application with the verified,
source-derived catalogue for SSC1 and SSP1. The legacy mainframe application
was not executed, so this report does not claim live mainframe equivalence.

The committed catalogue remains unchanged and authoritative.

## Task coverage

| Catalogue task | Modern action | Evidence | Result |
| --- | --- | --- | --- |
| T-SSC1-1 Inquire Customer | `GET /api/customers/<customer_number>` | Automated HTTP test and browser screenshot | Implemented |
| T-SSC1-2 Add Customer | `POST /api/customers` | Automated HTTP lifecycle test | Implemented |
| T-SSC1-4 Update Customer | `PUT /api/customers/<customer_number>` | Automated HTTP lifecycle test | Implemented |
| T-SSP1-1 Inquire Motor Policy | `GET /api/motor-policies/<policy_number>` | Automated HTTP test and browser screenshot | Implemented |
| T-SSP1-2 Add Motor Policy | `POST /api/motor-policies` | Automated HTTP lifecycle test | Implemented |
| T-SSP1-3 Delete Motor Policy | `DELETE /api/motor-policies/<policy_number>` | Automated HTTP lifecycle test | Implemented |
| T-SSP1-4 Update Motor Policy | `PUT /api/motor-policies/<policy_number>` | Automated HTTP lifecycle test | Implemented |

Customer deletion is deliberately absent because the SSC1 catalogue exposes
options 1, 2, and 4 only. An automated test confirms that a customer DELETE
request returns a JSON 404 rather than creating an unsupported action.

## Validation coverage

- Exact catalogue-derived customer and motor-policy field sets are enforced.
- All catalogue-derived maximum lengths are enforced in the data layer and
  SQLite schema.
- Values remain text; uncertain date and numeric semantics are not invented.
- Customer and policy identifiers, and the motor-policy customer reference,
  must be nonblank.
- Motor policies require an existing customer.
- Customer postcodes are uppercased before storage, matching the verified
  source behavior.
- Unknown fields, invalid JSON, wrong content types, missing records,
  duplicate identifiers, and unsupported API routes return clear errors.

## Verification

Command:

```sh
python3 -m unittest discover -s modern-app/tests -v
```

Result: 10 tests passed.

Additional check:

```sh
node --check modern-app/static/app.js
```

Result: JavaScript syntax check passed.

Browser evidence:

- `watsonx_sessions/heirloom_stage3_modern_app_first_run.jpeg`
- `watsonx_sessions/heirloom_stage3_customer_inquiry.jpeg`
- `watsonx_sessions/heirloom_stage3_motor_policy_inquiry.jpeg`
- `watsonx_sessions/heirloom_stage3_customer_add.jpeg`

## Outcome

All seven confirmed SSC1 and SSP1 catalogue tasks are present in the modern
application and passed the available source-grounded checks. No intentional or
observed parity gap was introduced. Human browser checks confirmed customer
inquiry, motor-policy inquiry, and customer creation before final review.
