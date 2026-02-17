# 🎁 iMessage Wrapped

Your year in iMessage — emoji, reactions, and messaging stats.

![Example output](example.png)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/whyisjake/imessage-wrapped.git
cd imessage-wrapped

# Run it
python3 imessage-wrapped.py
```

## Requirements

- **macOS** (iMessage database only exists on Mac)
- **Python 3** (comes with macOS)
- **Full Disk Access** for your terminal app

### Granting Full Disk Access

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the `+` button
3. Add your terminal app (Terminal.app, iTerm, Warp, etc.)
4. Restart your terminal

## Usage

```bash
python3 imessage-wrapped.py        # defaults to last year
python3 imessage-wrapped.py 2024   # specific year
python3 imessage-wrapped.py 2023   # any year with data
```

## What You'll See

- **Total messages** sent and received
- **Reaction counts** — how many you give vs. receive
- **Your reaction style** — are you a 👍 person or a ❤️ person?
- **Custom emoji reactions** (iOS 17+)
- **Monthly message volume** — see your chattiest months
- **Top reactions overall** — what emoji fly around your conversations

## Privacy

- 🔒 **100% local** — your data never leaves your machine
- 📖 **Read-only** — the script can't modify your messages
- 🚫 **No dependencies** — just Python's standard library

## How It Works

Your iMessage history lives in a SQLite database at:

```
~/Library/Messages/chat.db
```

The script queries this database (read-only) to extract stats. Some fun quirks of the schema:

- **Dates** are stored as nanoseconds since January 1, 2001 (Apple's epoch)
- **Reactions** are stored as separate messages with `associated_message_type` codes:
  - 2000 = ❤️ Loved
  - 2001 = 👍 Liked
  - 2002 = 👎 Disliked
  - 2003 = 😂 Laughed
  - 2004 = ‼️ Emphasized
  - 2005 = ❓ Questioned
- **Custom emoji reactions** (iOS 17+) are in `associated_message_emoji`

## License

MIT — do whatever you want with it.

## Author

[Jake Spurlock](https://jakespurlock.com) — I built this in 30 minutes after my daughter said "I bet Dad could write this."

Blog post: [I Built My Own iMessage Wrapped](https://jakespurlock.com/2026/02/i-built-my-own-imessage-wrapped/)
