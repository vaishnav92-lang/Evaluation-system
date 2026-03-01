# Aritzia Price Tracker

A simple Python tool that monitors Aritzia product pages for price drops and sends email alerts.

## How It Works

1. Reads product URLs from `watchlist.txt`
2. Uses Playwright (headless Chromium) to visit each page and extract the current price
3. Compares against the last known price stored in `price_history.json`
4. Sends an email alert if the price dropped

## Setup

### 1. Install dependencies

```bash
cd aritzia_tracker
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure email credentials

Copy the example env file and fill in your details:

```bash
cp .env.example .env
```

Edit `.env` with:
- **SENDER_EMAIL** — your Gmail address
- **SENDER_APP_PASSWORD** — a Gmail app password (not your regular password)
- **RECIPIENT_EMAIL** — where to receive alerts (can be the same address)

#### Getting a Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification if you haven't already
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Create a new app password for "Mail"
5. Copy the 16-character password into your `.env` file

### 3. Add products to track

Edit `watchlist.txt` and add Aritzia product URLs, one per line:

```
https://www.aritzia.com/us/en/product/the-effortless-pant%E2%84%A2/77775.html
https://www.aritzia.com/us/en/product/some-other-item/12345.html
```

Lines starting with `#` are ignored.

## Usage

### Run manually

```bash
cd aritzia_tracker
python main.py
```

### Run on a schedule (cron)

To check prices twice daily (8 AM and 8 PM), add this to your crontab (`crontab -e`):

```
0 8,20 * * * cd /path/to/aritzia_tracker && /path/to/python main.py >> /path/to/tracker.log 2>&1
```

Replace `/path/to/` with your actual paths. To find your Python path:

```bash
which python
```

## Files

| File | Purpose |
|---|---|
| `main.py` | Entry point — runs the price check |
| `scraper.py` | Playwright logic to extract prices from Aritzia pages |
| `notifier.py` | Sends email alerts via Gmail SMTP |
| `storage.py` | Reads/writes price history to JSON |
| `watchlist.txt` | Product URLs to track (one per line) |
| `price_history.json` | Auto-generated price history (do not edit) |
| `.env` | Your email credentials (not committed to git) |
