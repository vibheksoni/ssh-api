# Examples

This directory contains minimal examples for using `SSH ~ Api` once the service is running locally.

Assumptions:

- the API is running on `http://localhost:8754`
- you are connecting to a target Linux machine through `POST /session/connect`

Files:

- [`curl-connect-and-run.sh`](./curl-connect-and-run.sh): shell example using curl
- [`python_basic_session.py`](./python_basic_session.py): Python example using `requests`
- [`javascript_basic_session.mjs`](./javascript_basic_session.mjs): JavaScript example using fetch
