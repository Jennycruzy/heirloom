# Stage 7 deployment record

Date: 27 September 2026

## Public URLs

- Modern application: <https://heirloom.54-154-121-30.sslip.io/>
- Source-reconstruction dashboard: <https://heirloom.54-154-121-30.sslip.io/dashboard/>

## Isolation and data boundary

Heirloom runs as its own system service on loopback port 8300. Nginx exposes
only the application, static assets, API, dashboard, and committed catalogue.
The SQLite database is outside the Git checkout at
`/var/lib/heirloom/heirloom.sqlite3` and contains only the two explicitly
invented customers and two invented policies created by `modern-app/seed.py`.
No environment file or developer database was copied to the server.

## Verification performed

- Nginx configuration test: passed.
- Heirloom system service: active.
- Public HTTP routing: passed before TLS activation.
- HTTPS certificate issuance and installation: passed.
- HTTPS home page from the VPS: passed.
- HTTPS dashboard from the VPS: passed.
- External HTTPS home page from the development computer: HTTP 200.
- External HTTPS dashboard content check: passed.
- Headless Chrome dashboard render: passed after configuring Nginx to serve
  `.mjs` modules as `application/javascript`; the rendered page displayed the
  verified catalogue status and six-screen count instead of placeholders.
- External composite-key motor-policy API check for invented identifiers
  `CUST000001` and `POL001`: passed.

The general web-preview service did not accept the `sslip.io` hostname, so it
was not treated as deployment evidence. Direct HTTPS checks from both the VPS
and the development computer succeeded.
