# Heirloom VPS deployment

The public deployment uses one isolated Python service on loopback port 8300.
Nginx exposes the modern application at `/`, the API and static assets through
the same origin, and the source-reconstruction dashboard at `/dashboard/`.

The SQLite file lives outside the Git checkout at
`/var/lib/heirloom/heirloom.sqlite3`. Deployment must seed only invented demo
records and must never copy a developer database or environment file.

The expected public host is `heirloom.54-154-121-30.sslip.io`. TLS is managed
on the VPS after the HTTP route has been verified.
