# .NET Job Watcher V3

A non-AI job watcher. You directly configure each company and one or more job-board or API URLs in `config/companies.yaml`; the watcher fetches supported public feeds, filters .NET roles, and sends Telegram notifications.

## Quick start

1. Copy `.env.example` to `.env` and fill in Telegram settings.
2. Edit `config/companies.yaml`. Every company can contain multiple URL entries.
3. Install: `pip install -r requirements.txt`.
4. Run: `python -m main.check_jobs`.

## URL configuration

Each URL can be a public Greenhouse, Lever, Ashby, or SmartRecruiters careers page. Set `provider` only when auto-detection cannot infer it.

```yaml
companies:
  - name: Example Company
    enabled: true
    urls:
      - url: https://boards.greenhouse.io/example
      - url: https://jobs.lever.co/example
```

See `config/companies.yaml` for examples. No Gemini key or AI service is used.

