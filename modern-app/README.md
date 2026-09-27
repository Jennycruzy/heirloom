# Heirloom Modern

The repaired modernization of the verified SSC1 customer and SSP1
motor-policy workflows, plus the server for the whole judge site. The seed
records are invented hackathon test data; no running mainframe supplied them.

## Run

From the repository root:

```sh
python3 modern-app/seed.py
python3 modern-app/server.py --port 8080
```

| URL | Page |
| --- | --- |
| <http://127.0.0.1:8080/> | Project overview and findings |
| <http://127.0.0.1:8080/app/> | Clerk workspace |
| <http://127.0.0.1:8080/dashboard/> | Reconstructed legacy screens |
| <http://127.0.0.1:8080/api/health> | Health check with record counts |

Invented identifiers: customers `CUST000001` and `CUST000002`; policy
`POL001` held by `CUST000001` and `POL002` held by `CUST000002`.

## Workspace

- Customer: inquire, add, update. Motor policy: inquire, add, delete, update.
  Customer delete is absent because the SSC1 source does not offer it.
- Add locks the identifier: the application assigns it, as the legacy add
  programs do.
- Update is two steps: retrieve the live record, then edit and save.
- Motor inquiry, update and delete need both the policy and customer number.
- The legacy trace beside the form shows the source map with the fields the
  current step accepts, the COBOL behind the task, and the finding it repairs.
- Deep links: `/app/#customer/update/CUST000001` or
  `/app/#motor/inquire/POL001/CUST000001` (inquiry links run immediately).

## Server

One standard-library process serves the site, the API and the committed
evidence from a single origin. Only an explicit allowlist of files and
directories is reachable; the database, tests and legacy source are not.
Responses carry a strict Content Security Policy and related headers. The
application needs Python 3.11+ and nothing else.

## Test

```sh
python3 -m unittest discover -s modern-app/tests -v
node modern-app/tests/test_workflows.mjs
```
