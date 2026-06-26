# CarePlus Load Test

Load testing suite for the CarePlus Medical Assistant using [Locust](https://locust.io).

## Setup

```bash
pip install -r loadtest/requirements.txt
```

## Usage

### Web UI (recommended for first run)

```bash
locust -f loadtest/locustfile.py --host http://localhost:8000
```

Open http://localhost:8089, set **50 users** with a spawn rate of **5 users/sec**, and click Start.

### Headless (CI-friendly)

```bash
locust -f loadtest/locustfile.py --host http://localhost:8000 \
    --headless -u 50 -r 5 -t 2m
```

### With HTML report

```bash
locust -f loadtest/locustfile.py --host http://localhost:8000 \
    --headless -u 50 -r 5 -t 2m --html loadtest/report.html
```

## User Distribution

| User Type          | Weight | Share | Behavior                                   |
| ------------------ | ------ | ----- | ------------------------------------------ |
| `AuthenticatedUser`| 3      | ~75%  | Login, chat (appointments, meds, profiles) |
| `GuestUser`        | 1      | ~25%  | General health Q&A, no login               |

## Parameters

| Flag | Default | Description                         |
| ---- | ------- | ----------------------------------- |
| `-u` | —       | Total concurrent users              |
| `-r` | —       | Users spawned per second            |
| `-t` | —       | Test duration (e.g. `2m`, `30s`)    |

## Notes

- Chat endpoints hit the OpenAI API via the Agno agent, so response times will
  reflect LLM latency (~2-15s). Make sure your `OPENAI_API_KEY` rate limits can
  handle the load.
- The backend defaults to **4 Gunicorn workers** with a **120s timeout** and a
  DB pool of **20 + 30 overflow** connections.
- Authenticated users wait **3-8s** between requests; guests wait **5-12s**.
