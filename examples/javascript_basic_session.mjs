const baseUrl = "http://localhost:8754";

const host = "YOUR_SSH_HOST";
const username = "YOUR_SSH_USERNAME";
const password = "YOUR_SSH_PASSWORD";

const connectResponse = await fetch(`${baseUrl}/session/connect`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    host,
    username,
    password
  })
});

if (!connectResponse.ok) {
  throw new Error(`Connect failed: ${await connectResponse.text()}`);
}

const connectData = await connectResponse.json();
const sessionId = connectData.session_id;

try {
  const resultResponse = await fetch(`${baseUrl}/command/exec?session_id=${encodeURIComponent(sessionId)}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      command: "hostname",
      timeout: 30
    })
  });

  if (!resultResponse.ok) {
    throw new Error(`Command failed: ${await resultResponse.text()}`);
  }

  console.log(await resultResponse.json());
} finally {
  await fetch(`${baseUrl}/session/disconnect/${encodeURIComponent(sessionId)}`, {
    method: "POST"
  });
}
