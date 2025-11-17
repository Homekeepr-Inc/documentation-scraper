See SerpAPI design doc: [click here](../docs/serpapi-system-design.md)

## ManualsLib + CAPTCHA solving

When SerpApi returns a ManualsLib product result, the orchestrator now routes that URL through `download_manual_from_product_page`, which keeps the existing headless browser session alive and calls the shared AI CAPTCHA bridge whenever a reCAPTCHA challenge appears. There is no need to run `ai-captcha-bypass/main.py` separately; the solver is invoked in-process.

Make sure the AI solver environment variables are available (usually via `.env`) so `ai_utils.py` can reach your preferred provider:

- `OPENAI_API_KEY` (required when `AI_CAPTCHA_PROVIDER=openai`)
- `GOOGLE_API_KEY` (required when `AI_CAPTCHA_PROVIDER=gemini`)
- `OPENROUTER_API_KEY` (required when `AI_CAPTCHA_PROVIDER=openrouter`)
- `OPENROUTER_BASE_URL` (optional; defaults to `https://openrouter.ai/api/v1`)
- `AI_CAPTCHA_PROVIDER` (`gemini` by default)
- `AI_CAPTCHA_MODEL` (optional override of the provider default)
- `AI_CAPTCHA_COMPLEX_MODEL` (optional vision model used for harder tile instructions)
- `AI_REQUEST_THROTTLE_SECONDS` (optional; defaults to `0.25` so OpenRouter/OpenAI calls stay under their rate limits)

With those values set, invoking the SerpApi orchestrator is all that’s required to navigate ManualsLib, solve its CAPTCHA, and download the PDF. The AJAX download payload is now consumed immediately, so the PDF download begins as soon as the reCAPTCHA puzzle is cleared. PDFs are written into a throwaway directory created by `headless-browser-scraper/utils.py:create_temp_download_dir()` (under `headless-browser-scraper/temp/…`) before being validated/ingested; inspect that folder while the run is active if you need the raw file, or customize the helper if you want a persistent download location.
