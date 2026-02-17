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
    
    print("\n" + "=" * 40)
    print(f"📊 Data from ~/Library/Messages/chat.db")
    print(f"🕐 Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    db.close()

if __name__ == "__main__":
    main()
