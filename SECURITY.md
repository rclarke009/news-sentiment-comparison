# Security

This document describes security practices for the News Sentiment Comparison project.

## Secrets and credentials

- **Never commit** `.env`, `.env.local`, or any file containing API keys, passwords, or tokens.
- Store secrets in environment variables or a secrets manager (e.g. Render env vars, HashiCorp Vault).
- Use `.env.example` as a template only; never put real values there.
- Rotate keys if you suspect exposure (NewsAPI, Groq/OpenAI, MongoDB, `CRON_SECRET_KEY`).

## Pre-commit and CI checks

Run the secret-scanning script before committing:

```bash
./scripts/check_secrets.sh
```

Add it to your workflow (e.g. pre-commit hook or CI step) to reduce the risk of committing secrets.

## Production vs development

- **API docs** (`/docs`, `/redoc`, `/openapi.json`) are disabled when `ENV=production` or `RENDER=true`.
- **Debug logging** in the frontend runs only when `import.meta.env.DEV` is true (e.g. `npm run dev`); production builds do not log debug output.

## Secure configuration

- **CORS**: Allowed origins come from `CORS_ORIGINS`; methods and headers are restricted (no `*`).
- **Security headers**: The API adds `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, and `Referrer-Policy` to responses.
- **Collection endpoint**: `POST /api/v1/collect` requires the `X-Cron-Secret` header matching `CRON_SECRET_KEY`. Unauthorized attempts are logged with client IP.

## Dependency hygiene

- Python dependencies are pinned in `requirements.txt`. Periodically run `pip-audit` or `safety check` and update vulnerable packages.
- Frontend: run `npm audit` and address reported issues.

## Reporting vulnerabilities

If you discover a vulnerability, please report it responsibly (e.g. private disclosure to the maintainers) rather than opening a public issue. Include steps to reproduce and impact.

## Incident response

1. Rotate any potentially exposed secrets immediately.
2. Check logs for suspicious activity (e.g. unauthorized `/collect` attempts, unusual traffic).
3. Update dependencies if a vulnerability is in a library.
4. Document the incident and mitigations for future reference.
