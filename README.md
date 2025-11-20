# Bug Reporter + n8n starter

Tiny Flask app that captures bug reports via a form or JSON API, validates inputs, and forwards the raw payload to an n8n webhook for further automation.

## Project structure
```
app/
	__init__.py
	main.py        # Flask routes and webhook forwarding
templates/
	index.html     # Single-page bug form
Dockerfile
requirements.txt
.env.example
README.md
docker-compose.yml   # Optional: app + ngrok tunnel
test/
	sample_bug.json
	send_sample_request.sh
```

## Quick start (local Python)
1. **Create a virtual environment**
	 ```bash
	 python3 -m venv .venv
	 source .venv/bin/activate
	 ```
2. **Install deps**
	 ```bash
	 pip install -r requirements.txt
	 ```
3. **Configure environment**
	 ```bash
	 cp .env.example .env
	 export FLASK_APP=app.main
	 export FLASK_ENV=development
	 export N8N_WEBHOOK_URL="https://<your-n8n-host>/webhook/bug-reporter"
	 ```
4. **Run the server**
	 ```bash
	 flask run --host 0.0.0.0 --port 5000
	 ```
5. **Visit the form**: http://localhost:5000

## API usage
- `POST /api/report` accepts either JSON or `multipart/form-data` / `application/x-www-form-urlencoded`.
- Required fields: `title`, `description`, `priority` (`low|medium|high`).
- Returns `{ "status":"ok","tracking_id":"BUG-YYYYMMDD-N" }` when successful.
- Health-check: `GET /health` → `{ "status":"ok"... }`

### Test via curl
```bash
chmod +x test/send_sample_request.sh
./test/send_sample_request.sh
```
(Requires `jq`. Remove the pipe if not installed.)

## Docker
```bash
docker build -t bug-reporter .
docker run -p 5000:5000 --env-file .env bug-reporter
```

## docker-compose (Flask + ngrok)
1. Populate `.env` from `.env.example` and add `NGROK_AUTHTOKEN` (grab from https://dashboard.ngrok.com/get-started/your-authtoken).
2. Start both services:
	 ```bash
	 docker compose up --build
	 ```
3. Inspect the public URL via the ngrok UI at http://localhost:4040.

## Exposing the app publicly
- **ngrok CLI**
	```bash
	ngrok http 5000  # requires ngrok installed locally
	```
	Use the forwarded HTTPS URL as your `N8N_WEBHOOK_URL` or to let others submit bugs.
- **n8n tunnel** (ships with n8n)
	```bash
	n8n tunnel --port 5000
	```
	This generates a temporary public URL that you can plug into any workflow.

## Sample payload for n8n webhook
When configuring your n8n workflow, you can simulate the inbound data (the same payload the Flask API forwards) like this:
```bash
curl -X POST "$N8N_WEBHOOK_URL" \
	-H "Content-Type: application/json" \
	-H "X-Bug-Tracking-Id: BUG-EXAMPLE-1" \
	-d '{
				"title": "Submit button glitch",
				"description": "Clicking submit twice fires duplicate API calls.",
				"priority": "medium",
				"email": "qa@example.com",
				"screenshot_url": "https://example.com/glitch.png"
			}'
```

## Notes
- If `N8N_WEBHOOK_URL` is empty the app still accepts bugs but simply logs that forwarding is disabled.
- Add HTTPS, auth, and persistence before production use.