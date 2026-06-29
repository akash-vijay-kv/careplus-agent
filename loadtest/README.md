# CarePlus Load Tests

Load testing suite for the CarePlus Medical Assistant API using [Locust](https://locust.io).

## Setup

```bash
cd loadtest
pip install -r requirements.txt
```

## User Profiles

| Profile              | Weight | Description                                          |
|----------------------|--------|------------------------------------------------------|
| `AuthenticatedPatient` | 75%  | Logs in, creates a session, asks health questions    |
| `GuestVisitor`         | 25%  | Uses the chat without authentication (guest tools)   |
| `QuickBrowser`         | 0%   | Hits only lightweight endpoints (enable manually)    |

## Running

### Web UI (recommended for exploration)

```bash
locust -f locustfile.py --host http://localhost:8000
```

Open http://localhost:8089 and configure **50 users** with a spawn rate of **5 users/sec**.

### Headless (~50 concurrent users, 5-minute run)

```bash
locust -f locustfile.py --host http://localhost:8000 \
    --headless -u 50 -r 5 --run-time 5m
```

### Run only fast endpoints (skip LLM chat)

```bash
locust -f locustfile.py --host http://localhost:8000 \
    --headless -u 50 -r 10 --run-time 2m \
    --tags health session auth
```

## Notes

- Chat endpoints (`/api/chat`, `/api/chat/stream`) invoke an LLM, so response
  times will be in the **seconds** range. The wait times between tasks account
  for this.
- The upload endpoint (`/api/upload/blood-report`) is **not** included because
  it triggers OCR + LLM parsing which is expensive and rate-limited.
- Timeouts for chat requests are set to **120 seconds** to accommodate LLM
  latency under load.
