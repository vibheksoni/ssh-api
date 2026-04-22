import json
from urllib import parse, request


BASE_URL = "http://localhost:8754"


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    host = "YOUR_SSH_HOST"
    username = "YOUR_SSH_USERNAME"
    password = "YOUR_SSH_PASSWORD"

    connect = post_json(
        f"{BASE_URL}/session/connect",
        {
            "host": host,
            "username": username,
            "password": password,
        },
    )
    session_id = connect["session_id"]

    try:
        query = parse.urlencode({"session_id": session_id})
        result = post_json(
            f"{BASE_URL}/command/exec?{query}",
            {"command": "hostname", "timeout": 30},
        )
        print(result)
    finally:
        req = request.Request(
            f"{BASE_URL}/session/disconnect/{session_id}",
            method="POST",
        )
        with request.urlopen(req, timeout=30):
            pass


if __name__ == "__main__":
    main()
