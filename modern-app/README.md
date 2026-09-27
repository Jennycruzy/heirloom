# Heirloom Modern

First-pass modernization of the verified SSC1 customer and SSP1 motor-policy
workflows. The seed records are invented hackathon test data; no running
mainframe supplied them.

## Run

From the repository root:

```sh
python3 modern-app/seed.py
python3 modern-app/server.py --port 8080
```

Open <http://127.0.0.1:8080/>.

Use `CUST000001` for a customer inquiry or `POL001` for a motor-policy inquiry.

## Test

```sh
python3 -m unittest discover -s modern-app/tests -v
```

The application uses only Python 3.11 standard-library modules and
browser-native HTML, CSS, and JavaScript.
