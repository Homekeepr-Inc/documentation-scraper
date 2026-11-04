## System context — read first

Read [SystemDesign.md](SystemDesign.md) before changing cross-repo behavior, deployment wiring, or service contracts. The VPS runs Caddy, Temporal server/database/UI, workers and workflow APIs (including isolated home-document and inspection services), the documentation scraper, and the admin console served by the Temporal API. Supabase owns Auth, application Postgres, Storage, and Edge functions; the public website and proxy Worker run on Cloudflare. See the shared design for configured routes, evidence, and deployment unknowns.

