# Plan for AI CAPTCHA Solver Integration

## Overview
Integrate AI CAPTCHA solver into existing headless Chrome scrapers by extracting and adapting code from ai-captcha-bypass repo. Use the same Selenium Chrome driver instance to detect, solve CAPTCHAs in real-time without launching separate browsers.

## Key Requirements
- **CAPTCHA Types**: Text, Complicated Text, reCAPTCHA v2, Puzzle, Audio.
- **AI Providers**: OpenAI (default), Google Gemini.
- **Integration**: Callable from scrapers (e.g., samsung_headless_scraper.py) using existing driver; pause on detection, solve, resume.
- **Output**: Save successful solves as GIFs in `successful_solves/`.
- **Environment**: Chrome (chromedriver), Selenium, API keys in `.env` (OPENAI_API_KEY, GOOGLE_API_KEY).
- **Ethical Note**: For legitimate scraping only; respect site ToS and limits.

## Project Structure Additions
- `headless-browser-scraper/captcha_solver.py`: Main solver, adapted from main.py.
- `headless-browser-scraper/ai_utils.py`: API calls, from ai_utils.py.
- `headless-browser-scraper/puzzle_solver.py`: Puzzle logic, from puzzle_solver.py.
- `headless-browser-scraper/screenshots/`: Temp CAPTCHA captures.
- `headless-browser-scraper/successful_solves/`: GIF recordings.
- Update `requirements.txt`: Add selenium, openai, google-generativeai, python-dotenv, pillow, imageio.
- Add `.env.example` for API keys.

## Implementation Steps
1. **Extract & Adapt Code**:
   - Clone ai-captcha-bypass temporarily; copy core files (main.py, ai_utils.py, puzzle_solver.py, etc.) to headless-browser-scraper/.
   - Modify to accept existing Chrome driver; remove new browser launches.
   - Adapt Selenium actions to use passed driver.

2. **Core Components**:
   - **Detection**: Check for CAPTCHA via selectors/XPath in current page.
   - **Capture**: Screenshot elements or download audio using driver. For headless Chrome on VPS (no GUI), use `driver.get_screenshot_as_file('path.png')` for full page or `element.screenshot('path.png')` (Selenium 4+). Add Chrome options: `--headless=new --no-sandbox --disable-dev-shm-usage --virtual-time-budget=5000`. Install xvfb if needed: `apt-get install xvfb`.
   - **AI Analysis**: Send capture + type-specific prompt to AI.
   - **Action**: Execute solution (type, click, slide) on same driver.
   - **Verification**: Confirm success; retry up to 3x or alert.
   - **Recording**: Capture GIF of solve process.

3. **Modular Design**:
   - Class: `CaptchaSolver(driver, provider='openai', model='gpt-4o')`.
   - Methods: `detect_type()`, `solve_recaptcha_v2()`, etc.
   - Load keys from `.env`; customizable prompts.

4. **Scraper Integration**:
   - In scrapers: `from captcha_solver import CaptchaSolver; solver = CaptchaSolver(driver); if solver.detect(): solver.solve()`.
   - Handle errors/timeouts inline.

5. **Testing**:
   - Benchmark on 2captcha.com/demo via Chrome.
   - Test: `python captcha_solver.py --type recaptcha_v2 --provider gemini` (simulate with driver).
   - Aim >80% success; integrate into scraper runs.

6. **Edge Cases & Improvements**:
   - Sequential CAPTCHAs; audio fallback.
   - API rate limiting/caching.
   - Log via `logging_config.py`.
   - Add hCaptcha support later.

## Challenges
- **API Costs**: Cache common solves.
- **Chrome Compatibility**: Use chromedriver; human-like actions (delays, curves).
- **Legal/ToS**: Comply with sites; no unauthorized bypass.

## Next Actions
- Extract/adapt repo files to project.
- Create dirs and skeleton.
- Implement reCAPTCHA v2 first.
- Update README with instructions.