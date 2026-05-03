"""Generate a Pyrogram session string for the userbot.

Run this script ONCE on your local machine:
    python session_generator.py

It will ask for your phone number and verification code,
then print a SESSION_STRING to paste into your .env file.

⚠️  NEVER share your session string — it grants full access to your account.
"""

from pyrogram import Client


def main() -> None:
    print("=" * 50)
    print("  Pyrogram Session String Generator")
    print("=" * 50)
    print()

    api_id = int(input("Enter API_ID: ").strip())
    api_hash = input("Enter API_HASH: ").strip()

    print()
    print("A Telegram login prompt will follow.")
    print("Enter your phone number and the code you receive.")
    print()

    with Client(
        name="session_gen",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    ) as app:
        session_string = app.export_session_string()

    print()
    print("=" * 50)
    print("  ✅ SESSION_STRING generated successfully!")
    print("=" * 50)
    print()
    print(session_string)
    print()
    print("Copy the string above and paste it into your .env file")
    print("as SESSION_STRING=<the string>")
    print()
    print("⚠️  Keep this string SECRET — it grants full account access.")


if __name__ == "__main__":
    main()
