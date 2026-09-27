# Heirloom VPS deployment

One isolated Python service on loopback port 8300 serves the whole site:
the landing page at `/`, the clerk workspace at `/app/`, the reconstructed
legacy screens at `/dashboard/`, the committed evidence under `/evidence/`,
and the JSON API under `/api/`. Nginx terminates TLS and proxies every path to
that service, which exposes only an explicit allowlist of files.

The SQLite file lives outside the Git checkout at
`/var/lib/heirloom/heirloom.sqlite3`. Deployment must seed only invented demo
records and must never copy a developer database or environment file.

Public host: `heirloom.54-154-121-30.sslip.io` (TLS managed by Certbot).

## Update an existing deployment

```sh
cd /opt/heirloom
sudo git pull --recurse-submodules
sudo systemctl restart heirloom
curl -fsS https://heirloom.54-154-121-30.sslip.io/api/health
```

To reset the demo to its four invented records:

```sh
sudo -u ubuntu python3 modern-app/seed.py --db /var/lib/heirloom/heirloom.sqlite3
```
