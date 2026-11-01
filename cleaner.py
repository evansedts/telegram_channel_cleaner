"""Preview and delete a Telegram channel's published posts. Python 3.10+."""

import argparse
import asyncio
import getpass
from pathlib import Path

from dotenv import dotenv_values
from telethon import TelegramClient, errors, types
from telethon.sessions import StringSession


async def retry(operation):
    while True:
        try:
            return await operation()
        except errors.FloodWaitError as exc:
            print(f"Telegram rate limit: waiting {exc.seconds + 1} seconds.")
            await asyncio.sleep(exc.seconds + 1)


def read_config():
    env_path = Path(__file__).resolve().with_name(".env")
    config = dotenv_values(env_path)
    raw_id = (config.get("TELEGRAM_API_ID") or "").strip()
    api_hash = (config.get("TELEGRAM_API_HASH") or "").strip()
    if not raw_id.isascii() or not raw_id.isdecimal() or int(raw_id) <= 0:
        raise ValueError("Set TELEGRAM_API_ID to your numeric API ID in .env.")
    if len(api_hash) != 32 or any(c not in "0123456789abcdefABCDEF" for c in api_hash):
        raise ValueError("Set TELEGRAM_API_HASH to your 32-character API hash in .env.")
    phone = (config.get("TELEGRAM_PHONE") or "").strip()
    if phone and (not phone.startswith("+") or not phone[1:].isascii() or not phone[1:].isdecimal()):
        raise ValueError("Set TELEGRAM_PHONE in .env to +countrycode and number, or leave it blank.")
    return int(raw_id), api_hash, phone


async def main(delete):
    api_id, api_hash, phone = read_config()
    # Keep the login session in memory rather than saving account access to disk.
    client = TelegramClient(StringSession(), api_id, api_hash)
    try:
        await client.start(
            phone=lambda: phone or input("Your Telegram phone number, including country code: "),
            code_callback=lambda: getpass.getpass("Telegram login code (hidden): "),
            password=lambda: getpass.getpass("Telegram two-step password (if enabled): "),
        )
        me = await client.get_me()
        if me.bot:
            raise ValueError("Sign in with your personal admin account, not a bot token.")

        print("\nLoading channels you can manage...")
        channels = []
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if isinstance(entity, types.Channel) and entity.broadcast:
                rights = entity.admin_rights
                if entity.creator or (rights and rights.delete_messages):
                    channels.append(entity)
                    print(f"{len(channels)}. {entity.title!r} (ID {entity.id})")
        if not channels:
            print("No channels found where this account can delete posts.")
            return
        selection = int(input("Channel number: "))
        if not 1 <= selection <= len(channels):
            raise ValueError("Invalid channel number.")
        channel = channels[selection - 1]

        print("Scanning published history. Large channels may take a while...")
        ids = []
        async for message in client.iter_messages(channel, wait_time=1):
            # Telegram may prohibit deletion of channel-creation service records.
            if not isinstance(message, (types.MessageService, types.MessageEmpty)):
                ids.append(message.id)
        print(f"\nChannel: {channel.title!r}; ID: {channel.id}")
        print(f"Published posts in this snapshot: {len(ids)}")
        if not delete or not ids:
            print("Preview finished. Nothing deleted.")
            if ids:
                print("Run again with --delete to delete these posts.")
            return

        print("This permanently deletes these posts for ALL subscribers.")
        print("The channel and its subscribers remain. No backup is made.")
        phrase = f"DELETE {channel.id} {channel.title}"
        if input(f"Type exactly {phrase!r} to proceed: ") != phrase:
            print("Cancelled. Nothing deleted.")
            return

        for start in range(0, len(ids), 100):
            batch = ids[start:start + 100]
            await retry(lambda: client.delete_messages(channel, batch, revoke=True))
            print(f"Deletion requests accepted: {min(start + 100, len(ids))}/{len(ids)}")
            await asyncio.sleep(1)

        remaining = 0
        async for message in client.iter_messages(channel, wait_time=1):
            if not isinstance(message, (types.MessageService, types.MessageEmpty)):
                remaining += 1
        print(f"Finished. Published posts remaining: {remaining}.")
        if remaining:
            print("New or undeleted posts remain. Preview again before retrying.")
    finally:
        if client.is_connected():
            if await client.is_user_authorized():
                try:
                    await client.log_out()
                except errors.RPCError:
                    print("Logout failed; revoke this session in Telegram Settings > Devices.")
            await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delete", action="store_true", help="Enable deletion after typed confirmation")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.delete))
    except KeyboardInterrupt:
        print("\nStopped. Any posts already deleted stay deleted.")
    except (ValueError, errors.RPCError, OSError) as exc:
        print(f"Stopped: {exc}")
        raise SystemExit(1)
