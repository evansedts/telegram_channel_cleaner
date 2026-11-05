# Telegram Channel Cleaner

Delete all published posts, including old posts, from a Telegram channel you manage. Requires Python 3.10+ and a Telegram account with permission to delete channel posts.

## Watch this Tutorial

https://youtu.be/nD5oZWBx5wA

## Setup

1. Clone or download this repository and open its folder in VS Code.
2. Open **Terminal > New Terminal** in the project folder and install dependencies:

   ```sh
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to a new file named `.env` in the project folder. Fill in your details:

   ```dotenv
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE=
   ```

   Get your API ID and hash from [Telegram API development tools](https://my.telegram.org). Use your account API credentials, not a BotFather token. The phone number is optional; if provided, include the country code (for example, `+256700000000`).

## Run

Preview the channel and post count without deleting anything:

```sh
python cleaner.py
```

Delete all published posts after confirmation:

```sh
python cleaner.py --delete
```

Enter your Telegram login code and two-step password if requested. Select your channel, check its title and ID, then type the confirmation shown.

If your system uses `python3` or `py`, use that instead of `python` in the commands above.

## Notes

- Deletion is permanent for all subscribers. No backup is made; the channel and subscribers remain.
- Scheduled posts, linked-group comments and service records are excluded. Pause posting during cleanup.
- Telegram rate limits may cause waiting.
- Keep `.env` private. It is excluded by `.gitignore`; commit only the blank `.env.example` template. Enter login codes and passwords when prompted.
- No login session is saved to disk. Sign in each run. If interrupted, check **Telegram Settings > Devices** and remove any leftover session.
