#!/usr/bin/env python3
"""
iMessage Wrapped — Your year in emoji and reactions

Usage: python3 imessage-wrapped.py [year]
Default: Current year - 1

Requires: Full Disk Access for Terminal
(System Settings → Privacy & Security → Full Disk Access)
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Default to last year
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.now().year - 1
DB_PATH = Path.home() / "Library/Messages/chat.db"
CONTACTS_DB_PATH = Path.home() / "Library/Application Support/AddressBook/AddressBook-v22.abcddb"

# iMessage stores dates as nanoseconds since 2001-01-01
APPLE_EPOCH_OFFSET = 978307200

# Tapback type mapping
TAPBACKS = {
    2000: "❤️",   # Loved
    2001: "👍",   # Liked
    2002: "👎",   # Disliked
    2003: "😂",   # Laughed
    2004: "‼️",   # Emphasized
    2005: "❓",   # Questioned
}

def get_db():
    """Connect to the iMessage database (read-only)."""
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("Make sure you're running this on a Mac with Messages.app configured.")
        sys.exit(1)
    try:
        return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    except sqlite3.OperationalError as e:
        print(f"❌ Can't open database: {e}")
        print("Grant Full Disk Access to your terminal in System Settings.")
        sys.exit(1)

def date_filter(year):
    """SQL WHERE clause for filtering by year."""
    return f"""
        datetime(date/1000000000 + {APPLE_EPOCH_OFFSET}, 'unixepoch') >= '{year}-01-01'
        AND datetime(date/1000000000 + {APPLE_EPOCH_OFFSET}, 'unixepoch') < '{year + 1}-01-01'
    """

def get_contact_name(contact_id):
    """
    Look up a contact's name from the Contacts database.
    Falls back to the contact_id (phone/email) if not found.
    """
    # Try multiple common Contacts database locations
    contacts_paths = [
        CONTACTS_DB_PATH,
        Path.home() / "Library/Application Support/AddressBook/Sources/*/AddressBook-v22.abcddb"
    ]

    for path_pattern in contacts_paths:
        # Handle glob patterns
        if '*' in str(path_pattern):
            import glob
            matching_paths = glob.glob(str(path_pattern))
            paths_to_try = [Path(p) for p in matching_paths]
        else:
            paths_to_try = [path_pattern]

        for contacts_path in paths_to_try:
            if not contacts_path.exists():
                continue

            try:
                contacts_db = sqlite3.connect(f"file:{contacts_path}?mode=ro", uri=True)
                cur = contacts_db.cursor()

                # Normalize the contact_id for comparison
                normalized_id = contact_id.strip()
                if normalized_id.startswith('+'):
                    # Try with and without country code
                    search_patterns = [normalized_id, normalized_id[1:], normalized_id[2:]]
                else:
                    search_patterns = [normalized_id]

                # Also add a digits-only pattern to handle formatted numbers like (503) 555-1234
                digits_only = ''.join(filter(str.isdigit, normalized_id))
                if digits_only and digits_only not in search_patterns:
                    if len(digits_only) == 11 and digits_only.startswith('1'):
                        search_patterns.extend([digits_only, digits_only[1:]])
                    else:
                        search_patterns.append(digits_only)

                # Query the Contacts database for a matching phone number or email
                for pattern in search_patterns:
                    cur.execute("""
                        SELECT ZABCDRECORD.ZFIRSTNAME, ZABCDRECORD.ZLASTNAME
                        FROM ZABCDRECORD
                        JOIN ZABCDPHONENUMBER ON ZABCDRECORD.Z_PK = ZABCDPHONENUMBER.ZOWNER
                        WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                            ZABCDPHONENUMBER.ZFULLNUMBER,
                            ' ', ''), '-', ''), '(', ''), ')', ''), '+', '') LIKE ?
                        LIMIT 1
                    """, (f"%{pattern}%",))
                    result = cur.fetchone()

                    if not result:
                        # Try email lookup
                        cur.execute("""
                            SELECT ZABCDRECORD.ZFIRSTNAME, ZABCDRECORD.ZLASTNAME
                            FROM ZABCDRECORD
                            JOIN ZABCDEMAILADDRESS ON ZABCDRECORD.Z_PK = ZABCDEMAILADDRESS.ZOWNER
                            WHERE ZABCDEMAILADDRESS.ZADDRESS = ?
                            LIMIT 1
                        """, (pattern,))
                        result = cur.fetchone()

                    if result:
                        first_name, last_name = result
                        contacts_db.close()
                        # Build full name
                        parts = [p for p in [first_name, last_name] if p]
                        return " ".join(parts) if parts else contact_id

                contacts_db.close()
            except (sqlite3.OperationalError, sqlite3.DatabaseError):
                # Database access failed, continue to next path
                continue

    # Return original contact_id if no name found
    return contact_id

def main():
    print(f"\n🎁 iMessage Wrapped {YEAR}\n")
    print("=" * 40)

    db = get_db()
    cur = db.cursor()

    # --- Message counts ---
    cur.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN is_from_me = 1 THEN 1 ELSE 0 END) as sent,
            SUM(CASE WHEN is_from_me = 0 THEN 1 ELSE 0 END) as received
        FROM message
        WHERE {date_filter(YEAR)} AND associated_message_type = 0
    """)
    total, sent, received = cur.fetchone()

    if total == 0:
        print(f"No messages found for {YEAR}.")
        print("Try a different year: python3 imessage-wrapped.py 2024")
        sys.exit(0)

    print(f"\n📱 Messages")
    print(f"   Total:    {total:,}")
    print(f"   Sent:     {sent:,}")
    print(f"   Received: {received:,}")

    # --- Reaction counts ---
    cur.execute(f"""
        SELECT
            SUM(CASE WHEN is_from_me = 1 THEN 1 ELSE 0 END) as given,
            SUM(CASE WHEN is_from_me = 0 THEN 1 ELSE 0 END) as received
        FROM message
        WHERE {date_filter(YEAR)} AND associated_message_type >= 2000
    """)
    given, got = cur.fetchone()
    given = given or 0
    got = got or 0

    print(f"\n💬 Reactions")
    print(f"   Given:    {given:,}")
    print(f"   Received: {got:,}")

    # --- Your tapback style (given) ---
    print(f"\n🏆 Your Reaction Style")
    cur.execute(f"""
        SELECT associated_message_type, COUNT(*) as cnt
        FROM message
        WHERE {date_filter(YEAR)}
        AND associated_message_type BETWEEN 2000 AND 2005
        AND is_from_me = 1
        GROUP BY associated_message_type
        ORDER BY cnt DESC
    """)
    rows = cur.fetchall()
    if rows:
        for row in rows:
            emoji = TAPBACKS.get(row[0], "?")
            print(f"   {emoji}  {row[1]:,}")
    else:
        print("   (no reactions given)")

    # --- Custom emoji reactions (given) ---
    cur.execute(f"""
        SELECT associated_message_emoji, COUNT(*) as cnt
        FROM message
        WHERE {date_filter(YEAR)}
        AND associated_message_emoji IS NOT NULL
        AND is_from_me = 1
        GROUP BY associated_message_emoji
        ORDER BY cnt DESC
        LIMIT 10
    """)
    customs = cur.fetchall()
    if customs:
        print(f"\n🎯 Your Custom Reactions")
        for emoji, cnt in customs:
            print(f"   {emoji}  {cnt}")

    # --- Monthly volume ---
    print(f"\n📈 Messages by Month")
    cur.execute(f"""
        SELECT
            strftime('%m', datetime(date/1000000000 + {APPLE_EPOCH_OFFSET}, 'unixepoch')) as month,
            COUNT(*) as cnt
        FROM message
        WHERE {date_filter(YEAR)} AND associated_message_type = 0
        GROUP BY month
        ORDER BY month
    """)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    data = {row[0]: row[1] for row in cur.fetchall()}
    max_cnt = max(data.values()) if data else 1

    for i, name in enumerate(months, 1):
        cnt = data.get(f"{i:02d}", 0)
        bar = "█" * int(20 * cnt / max_cnt) if cnt else ""
        print(f"   {name}  {bar} {cnt:,}")

    # --- Top reactions overall ---
    print(f"\n🌟 Top Reactions (All)")
    cur.execute(f"""
        SELECT
            COALESCE(associated_message_emoji,
                CASE associated_message_type
                    WHEN 2000 THEN '❤️'
                    WHEN 2001 THEN '👍'
                    WHEN 2002 THEN '👎'
                    WHEN 2003 THEN '😂'
                    WHEN 2004 THEN '‼️'
                    WHEN 2005 THEN '❓'
                END
            ) as emoji,
            COUNT(*) as cnt
        FROM message
        WHERE {date_filter(YEAR)} AND associated_message_type >= 2000
        GROUP BY emoji
        HAVING emoji IS NOT NULL
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for emoji, cnt in cur.fetchall():
        print(f"   {emoji}  {cnt:,}")

    # --- Blue vs Green Bubbles ---
    cur.execute(f"""
        SELECT
            service,
            COUNT(*) as cnt
        FROM message
        WHERE {date_filter(YEAR)} AND associated_message_type = 0
        AND service IS NOT NULL
        GROUP BY service
        ORDER BY cnt DESC
    """)
    bubble_rows = cur.fetchall()
    if bubble_rows:
        print(f"\n🔵🟢 Blue vs Green Bubbles")
        bubble_data = {row[0]: row[1] for row in bubble_rows}
        bubble_total = sum(bubble_data.values())
        imessage_cnt = bubble_data.get("iMessage", 0)
        sms_cnt = bubble_data.get("SMS", 0)
        imessage_pct = 100 * imessage_cnt / bubble_total if bubble_total else 0
        sms_pct = 100 * sms_cnt / bubble_total if bubble_total else 0
        print(f"   🔵 iMessage (blue):      {imessage_cnt:,}  ({imessage_pct:.1f}%)")
        print(f"   🟢 SMS/Android (green):  {sms_cnt:,}  ({sms_pct:.1f}%)")

    # --- Top green bubble contacts ---
    cur.execute(f"""
        SELECT
            h.id as contact,
            COUNT(*) as cnt
        FROM message m
        JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        JOIN chat c ON cmj.chat_id = c.ROWID
        JOIN chat_handle_join chj ON c.ROWID = chj.chat_id
        JOIN handle h ON chj.handle_id = h.ROWID
        WHERE {date_filter(YEAR)}
        AND m.associated_message_type = 0
        AND m.service = 'SMS'
        GROUP BY h.id
        ORDER BY cnt DESC
        LIMIT 10
    """)
    green_contacts = cur.fetchall()
    if green_contacts:
        print(f"\n📲 Top Green Bubble Contacts (consider Signal! 😎)")
        for contact, cnt in green_contacts:
            name = get_contact_name(contact)
            print(f"   {name}  {cnt:,}")

    # --- Top 10 most texted contacts (yearly) ---
    print(f"\n👥 Top 10 Most Texted")
    cur.execute(f"""
        SELECT
            h.id as contact,
            COUNT(*) as cnt
        FROM message m
        JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        JOIN chat c ON cmj.chat_id = c.ROWID
        JOIN chat_handle_join chj ON c.ROWID = chj.chat_id
        JOIN handle h ON chj.handle_id = h.ROWID
        WHERE {date_filter(YEAR)} AND m.associated_message_type = 0
        GROUP BY h.id
        ORDER BY cnt DESC
        LIMIT 10
    """)
    top_contacts = cur.fetchall()
    if top_contacts:
        for contact, cnt in top_contacts:
            name = get_contact_name(contact)
            print(f"   {name}  {cnt:,}")
    else:
        print("   (no contact data available)")

    # --- Top 10 most texted by month ---
    print(f"\n📅 Top 10  Most Texted by Month")
    for i, month_name in enumerate(months, 1):
        month_str = f"{i:02d}"
        cur.execute(f"""
            SELECT
                h.id as contact,
                COUNT(*) as cnt
            FROM message m
            JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
            JOIN chat c ON cmj.chat_id = c.ROWID
            JOIN chat_handle_join chj ON c.ROWID = chj.chat_id
            JOIN handle h ON chj.handle_id = h.ROWID
            WHERE {date_filter(YEAR)}
            AND m.associated_message_type = 0
            AND strftime('%m', datetime(m.date/1000000000 + {APPLE_EPOCH_OFFSET}, 'unixepoch')) = '{month_str}'
            GROUP BY h.id
            ORDER BY cnt DESC
            LIMIT 10
        """)
        month_data = cur.fetchall()
        if month_data:
            print(f"\n   {month_name}:")
            for contact, cnt in month_data:
                name = get_contact_name(contact)
                print(f"      {name}  {cnt:,}")

    print("\n" + "=" * 40)
    print(f"📊 Data from ~/Library/Messages/chat.db")
    print(f"🕐 Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    db.close()

if __name__ == "__main__":
    main()
