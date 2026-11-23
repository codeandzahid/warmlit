# Warmlit plans — Free vs Paid

| Feature | Free | Paid |
|---|---|---|
| Chat (demo or your API key) | yes, daily limit | unlimited |
| Memory save + search | yes | yes |
| Read files, list files | yes | yes |
| Web fetch, skills search | yes | yes |
| Write files (local system) | no | yes, with approval |
| Run shell commands (local system) | no | yes, with approval |
| Open Chrome browser (local system) | no | yes |
| Scheduled jobs | no | yes |
| Connectors (when connected) | no | yes |

Daily limit for Free: `FREE_DAILY_LIMIT` in .env (default 50).

## How Paid works (local, offline)

1. Owner sets `LICENSE_SECRET` in .env (never share it).
2. Owner makes a key: `python3 tools/make_key.py --days 30`
3. Buyer pays the owner outside Warmlit (e.g. PayPal).
   No card data ever touches this code.
4. Owner sends the buyer `license.json`. Buyer puts it in `data/`.
5. Warmlit checks the key offline. Valid + not expired = Paid.
   Bad or expired = Free. Paying again = new key file, same install.

## Price

NOT SET YET. The owner must confirm the price before selling.
Nothing in this repo charges money.
