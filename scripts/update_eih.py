#!/usr/bin/env python3
"""EIH v11 — Major update:
- Removed: שוק הון section, תעשייה section
- Fixed: מגמות (trends) now filled by GPT
- Changed: טכנולוגיה from Geektime/LetsAI + Epoch tech only
- Changed: תיירות — exotic destinations, road trips, resorts, unique experiences
- Added: רשת חברתית — Facebook Israel content
- Added: חברה — Epoch psychology
- Added: טכנולוגיה — Epoch science & technology
- Added: כלכלה — crypto market data
- Changed: בידור — theater, new movies, Netflix series, cinema, Apple TV
"""
import os, sys, json, base64, requests, time, re, html as html_mod
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus
from email.utils import parsedate_to_datetime

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

# Tokens from env or hardcoded
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GH_PAT", "")
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8736148084:AAGdhexvaFtJrJerI-yW90wlvfUXnbKxCgo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "479774667")

IST = timezone(timedelta(hours=3))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MAX_AGE_DAYS = 2  # Drop articles older than 48 hours to prevent stale news

# ============================================================
# PART 1: SCRAPING — All data comes from here, NOT from GPT
# ============================================================

def fetch_google_news(q, hl="he", gl="IL", ceid="IL:he", max_items=3):
    """Fetch real headlines from Google News RSS with Google News redirect links.
    
    FIX: Articles older than MAX_AGE_DAYS are dropped to prevent stale news.
    The RSS feed is iterated beyond max_items so we can fill up to max_items
    fresh articles even when early results are stale.
    """
    items = []
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=MAX_AGE_DAYS)
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"
        resp = requests.get(url, headers=UA, timeout=15)
        root = ET.fromstring(resp.content)
        for item in root.findall(".//item"):
            if len(items) >= max_items:
                break
            title = item.findtext("title", "").strip()
            pub_date = item.findtext("pubDate", "")
            # --- DATE FRESHNESS CHECK ---
            if pub_date:
                try:
                    pub_dt = parsedate_to_datetime(pub_date)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                    else:
                        pub_dt = pub_dt.astimezone(timezone.utc)
                    if pub_dt < cutoff:
                        print(f"    [SKIP stale {pub_dt.date()}] {title[:50]}")
                        continue
                except Exception:
                    pass  # unparseable date — allow through
            # ----------------------------
            source_el = item.find("source")
            source_name = source_el.text if source_el is not None else ""
            gnews_link = item.findtext("link", "").strip()
            if not gnews_link:
                gnews_link = f"https://www.google.com/search?q={quote_plus(title)}"
            desc = re.sub(r'<[^>]+>', '', item.findtext("description", ""))[:200]
            if title:
                items.append({
                    "title": title, "link": gnews_link, "source_name": source_name,
                    "description": desc, "pub_date": pub_date
                })
    except Exception as e:
        print(f"    GNews error: {e}")
    return items

def fetch_rss(url, max_items=3):
    """Fetch real articles from RSS feeds with direct URLs.
    
    FIX: pub_date is now captured so date-based sorting in select_news_items
    works correctly for RSS items (previously they had no pub_date field).
    """
    items = []
    try:
        resp = requests.get(url, headers=UA, timeout=15)
        root = ET.fromstring(resp.content)
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "")  # FIX: capture pub_date
            desc = re.sub(r'<[^>]+>', '', item.findtext("description", ""))[:200]
            if title and link:
                items.append({"title": title, "link": link, "description": desc, "pub_date": pub_date})
    except Exception as e:
        print(f"    RSS error: {e}")
    return items

def fetch_market_data():
    """Fetch real market data from public APIs — includes crypto."""
    market = {
        "indices": [], "currencies": [], "commodities": [],
        "israelHeadlines": [], "wallStreetHeadlines": [], "watchTomorrow": ""
    }
    
    symbols = {
        "indices": [
            ("^TA125.TA", "תל אביב 125"),
            ("^GSPC", "S&P 500"),
            ("^IXIC", "נאסדק"),
            ("^DJI", "דאו גונס"),
        ],
        "currencies": [
            ("USDILS=X", "דולר/שקל"),
            ("EURILS=X", "אירו/שקל"),
            ("EURUSD=X", "אירו/דולר"),
        ],
        "commodities": [
            ("CL=F", "נפט גולמי"),
            ("GC=F", "זהב"),
            ("BTC-USD", "ביטקוין"),
            ("ETH-USD", "את'ריום"),
            ("SOL-USD", "סולנה"),
        ]
    }
    
    for cat, syms in symbols.items():
        for symbol, name in syms:
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
                resp = requests.get(url, headers=UA, timeout=10)
                data = resp.json()
                result = data.get("chart", {}).get("result", [{}])[0]
                meta = result.get("meta", {})
                price = meta.get("regularMarketPrice", 0)
                prev = meta.get("previousClose", price)
                if prev and prev != 0:
                    change_pct = ((price - prev) / prev) * 100
                else:
                    change_pct = 0
                direction = "up" if change_pct > 0 else "down" if change_pct < 0 else "stable"
                
                if price > 10000:
                    value = f"{price:,.0f}"
                elif price > 100:
                    value = f"{price:,.2f}"
                else:
                    value = f"{price:.2f}"
                
                change_str = f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%"
                
                market[cat].append({
                    "name": name, "value": value, "change": change_str, "direction": direction
                })
                print(f"    Market: {name} = {value} ({change_str})")
            except Exception as e:
                print(f"    Market error {name}: {e}")
                market[cat].append({"name": name, "value": "N/A", "change": "0%", "direction": "stable"})
            time.sleep(0.3)
    
    return market

def scrape_all():
    """Scrape all news from all sources. Returns dict[category] -> list of items."""
    data = {}
    
    # Direct RSS feeds with real article URLs
    rss_feeds = [
        # כלכלה
        ("כלכלה", "גלובס", "https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederNode?iID=585"),
        ("כלכלה", "כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml"),
        # חברה
        ("חברה", "ynet", "https://www.ynet.co.il/Integration/StoryRss2.xml"),
        # פיתוח אישי — Farnam Street (fs.blog): mental models, decision-making, personal growth
        ("פיתוח אישי", "Farnam Street", "https://fs.blog/feed/"),
    ]
    
    for cat, name, url in rss_feeds:
        print(f"  RSS: {cat} — {name}")
        items = fetch_rss(url, 3)
        for i in items:
            i["source_name"] = name
            i["category"] = cat
        data.setdefault(cat, []).extend(items)
    
    # Google News queries — UPDATED sources per user request
    queries = {
        # כלכלה — includes crypto
        # FIX: replaced broad keyword query with site-scoped query for recency
        "כלכלה": [
            ("site:globes.co.il כלכלה", "he"),
            ("Israel economy GDP inflation", "en"),
            ("crypto bitcoin ethereum market today", "en"),
        ],
        # פוליטיקה
        # FIX: replaced broad keyword query (returned Feb 2026 Modi article) with site-scoped queries
        "פוליטיקה": [
            ("site:ynet.co.il פוליטיקה", "he"),
            ("site:walla.co.il פוליטיקה", "he"),
            ("site:epoch.org.il גיאו-פוליטיקה OR מדיניות חוץ OR דיפלומטיה", "he"),
        ],
        # ביטחון
        # FIX: replaced broad keyword query with site-scoped query for recency
        "ביטחון": [
            ("site:n12.co.il ביטחון צבא", "he"),
            ("site:walla.co.il ביטחון", "he"),
            ("Israel defense IDF", "en"),
        ],
        # חברה — Epoch psychology + philosophy + body-mind-spirit
        # FIX: replaced broad keyword query with site-scoped query for recency
        "חברה": [
            ("site:ynet.co.il חברה", "he"),
            ("site:epoch.org.il פסיכולוגיה OR מערכות יחסים OR התפתחות אישית", "he"),
            ("site:epoch.org.il פילוסופיה OR חברה OR היסטוריה OR רוחניות", "he"),
        ],
        # טכנולוגיה — ONLY from Geektime/LetsAI
        "טכנולוגיה": [
            ("site:geektime.co.il AI OR סטארטאפ OR טכנולוגיה", "he"),
            ("LetsAI Israel AI artificial intelligence", "en"),
            ("Israel tech AI startup 2026", "en"),
        ],
        # רשת חברתית — added Facebook
        "רשת חברתית": [
            ("CISO Israel cybersecurity LinkedIn", "en"),
            ("AI startup Israel LinkedIn", "en"),
            ("Facebook Israel viral post trending", "en"),
            ("פייסבוק ישראל ויראלי פוסט", "he"),
        ],
        # אירועים
        "אירועים": [
            ("כנס הייטק ישראל 2026", "he"),
            ("Israel tech conference event 2026", "en"),
            ("Tel Aviv AI Cyber conference 2026", "en"),
        ],
        # בידור — theater, movies, Netflix, Apple TV, cinema + Epoch culture
        "בידור": [
            ("Netflix new series movies 2026", "en"),
            ("Apple TV new shows 2026", "en"),
            ("סרטים חדשים קולנוע ישראל 2026", "he"),
            ("הצגות תיאטרון תל אביב 2026", "he"),
            ("site:epoch.org.il תרבות OR אמנות OR סרט OR ביקורת", "he"),
        ],
        # יין
        "יין": [
            ("Wine Spectator review 2026", "en"),
            ("wine market Liv-ex investment Bordeaux", "en"),
            ("Decanter Bordeaux Burgundy Barolo", "en"),
            ("DRC Lafite Sassicaia Krug Margaux wine", "en"),
        ],
        # תיירות — exotic destinations, road trips, resorts, unique experiences + PassportNews
        "תיירות": [
            ("site:passportnews.co.il תיירות OR מלונות OR תעופה OR טיסות", "he"),
            ("exotic travel destinations 2026 luxury resort", "en"),
            ("road trip adventure unique travel experience", "en"),
            ("best luxury resorts Maldives Bali Seychelles 2026", "en"),
        ],
    }
    
    for cat, qs in queries.items():
        for q, lang in qs:
            print(f"  GNews: {cat} — '{q[:40]}'")
            gl = "IL" if lang == "he" else "US"
            ceid = "IL:he" if lang == "he" else "US:en"
            items = fetch_google_news(q, lang, gl, ceid, 3)
            for i in items:
                i["category"] = cat
            data.setdefault(cat, []).extend(items)
            time.sleep(0.3)
    
    total = sum(len(v) for v in data.values())
    print(f"\n  Total scraped: {total} items, {len(data)} categories")
    for c, items in sorted(data.items()):
        print(f"    {c}: {len(items)}")
    return data

# ============================================================
# PART 2: SELECT BEST ITEMS
# ============================================================

def _parse_pub_date(item):
    """Return a UTC datetime for sorting; epoch-0 if unparseable."""
    try:
        dt = parsedate_to_datetime(item.get("pub_date", ""))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)

def select_news_items(data, max_per_cat=2, total_max=20):
    """Select best items from scraped data. Priority: RSS > Google News.
    
    FIX: Each group is sorted newest-first before slicing so that even if
    stale articles slip through (e.g. RSS feeds), the most recent ones are
    always preferred within each source tier.
    """
    news_cats = ["כלכלה", "פוליטיקה", "ביטחון", "חברה", "טכנולוגיה", "רשת חברתית", "אירועים", "בידור", "פיתוח אישי"]
    items = []
    idx = 1
    
    for cat in news_cats:
        cat_items = data.get(cat, [])
        rss_items = [i for i in cat_items if "news.google.com" not in i.get("link", "") and "google.com/search" not in i.get("link", "")]
        gnews_items = [i for i in cat_items if i not in rss_items]
        
        # FIX: sort each group newest-first before selecting
        rss_items   = sorted(rss_items,   key=_parse_pub_date, reverse=True)
        gnews_items = sorted(gnews_items, key=_parse_pub_date, reverse=True)
        
        # Prioritize Epoch in all relevant categories (enriching content > plain news)
        epoch_cats = ["חברה", "פוליטיקה", "בידור"]
        if cat in epoch_cats:
            epoch_items = [i for i in cat_items if "epoch" in i.get("source_name", "").lower() or "epoch" in i.get("link", "").lower()]
            other_items = [i for i in cat_items if i not in epoch_items]
            other_rss = [i for i in other_items if "news.google.com" not in i.get("link", "") and "google.com/search" not in i.get("link", "")]
            other_gnews = [i for i in other_items if i not in other_rss]
            # FIX: sort epoch/rss/gnews sub-groups newest-first too
            epoch_items = sorted(epoch_items, key=_parse_pub_date, reverse=True)
            other_rss   = sorted(other_rss,   key=_parse_pub_date, reverse=True)
            other_gnews = sorted(other_gnews, key=_parse_pub_date, reverse=True)
            # Epoch first (1 item), then RSS, then Google News
            selected = (epoch_items[:1] + other_rss + other_gnews)[:max_per_cat]
        else:
            selected = (rss_items + gnews_items)[:max_per_cat]
        
        for item in selected:
            items.append({
                "id": idx,
                "type": "news",
                "category": cat if cat != "ביטחון" else "צבא וביטחון",
                "title": item.get("title", ""),
                "summary": item.get("description", item.get("title", "")),
                "sourceUrl": item.get("link", "#"),
                "sourceName": item.get("source_name", ""),
                "importance": 7 if rss_items and item in rss_items else 6,
            })
            idx += 1
    
    return items[:total_max]

def select_wine_items(data, max_items=5):
    items = []
    for item in data.get("יין", [])[:max_items]:
        items.append({
            "id": 200 + len(items) + 1,
            "type": "news",
            "category": "יין",
            "title": item.get("title", ""),
            "summary": item.get("description", item.get("title", "")),
            "sourceUrl": item.get("link", "#"),
            "sourceName": item.get("source_name", ""),
            "importance": 6,
        })
    return items

def select_tourism_items(data, max_items=5):
    items = []
    raw = data.get("תיירות", [])
    # Prioritize PassportNews items first
    passport_items = [i for i in raw if "PassportNews" in i.get("source_name", "") or "passportnews" in i.get("link", "").lower()]
    other_items = [i for i in raw if i not in passport_items]
    selected = passport_items[:2] + other_items[:max_items - min(2, len(passport_items))]
    selected = selected[:max_items]
    for item in selected:
        is_passport = "PassportNews" in item.get("source_name", "") or "passportnews" in item.get("source_name", "").lower()
        items.append({
            "id": 300 + len(items) + 1,
            "type": "news",
            "category": "תיירות",
            "title": item.get("title", ""),
            "summary": item.get("description", item.get("title", "")),
            "sourceUrl": item.get("link", "#"),
            "sourceName": item.get("source_name", ""),
            "importance": 7 if is_passport else 6,
        })
    return items

def select_content_items(data, max_items=5):
    """Select deeper content items from various categories."""
    content_cats = ["טכנולוגיה", "כלכלה", "ביטחון", "חברה", "רשת חברתית"]
    items = []
    idx = 100
    for cat in content_cats:
        cat_items = data.get(cat, [])
        if len(cat_items) > 2:
            item = cat_items[2]
            items.append({
                "id": idx,
                "type": "content",
                "category": cat if cat != "ביטחון" else "צבא וביטחון",
                "title": item.get("title", ""),
                "summary": item.get("description", item.get("title", "")),
                "sourceUrl": item.get("link", "#"),
                "sourceName": item.get("source_name", ""),
                "importance": 6,
            })
            idx += 1
    return items[:max_items]

# ============================================================
# PART 3: GPT — ONLY for analysis/insights, NOT for data
# ============================================================

def call_gpt(system, user, max_tokens=2000):
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    api_url = f"{base_url}/chat/completions"
    for model in ["gpt-4.1-mini", "gpt-4.1-nano", "gemini-2.5-flash"]:
        for attempt in range(3):
            try:
                print(f"    GPT {model} attempt {attempt+1} ({base_url[:40]}...)")
                resp = requests.post(api_url,
                    headers=headers, json={
                        "model": model, "temperature": 0.3, "max_tokens": max_tokens,
                        "response_format": {"type": "json_object"},
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]
                    }, timeout=60)
                if resp.status_code == 429:
                    time.sleep(10*(attempt+1)); continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt < 2: time.sleep(5); continue
                print(f"    Error: {e}")
    return None

def get_insights(news_items, market_headlines):
    """GPT generates insights — whyItMatters, implications, trends, summary. Uses item id for matching."""
    headlines = "\n".join(f"- id={i['id']}: [{i['category']}] {i['title']}" for i in news_items[:25])
    market_info = "\n".join(f"- {h}" for h in market_headlines[:10])
    
    prompt = f"""Here are today's real headlines from Israel (each has an id number):

{headlines}

Market data:
{market_info}

Generate JSON with analysis and insights for EACH headline by its id:
{{
  "insights": [
    {{"id": 1, "whyItMatters": "one sentence in Hebrew explaining WHY this matters to an Israeli business executive", "implications": "one sentence in Hebrew about practical implications or what to expect next"}}
  ],
  "trends": [
    {{"title": "trend name in Hebrew", "description": "detailed sentence in Hebrew explaining the trend", "direction": "up/down/stable"}}
  ],
  "executiveSummary": "2-3 sentences summary in Hebrew connecting the main stories",
  "conclusion": "1 sentence in Hebrew",
  "watchNext24h": "1 sentence in Hebrew",
  "breakingItems": ["emoji headline1", "emoji headline2", "emoji headline3", "emoji headline4", "emoji headline5"]
}}

CRITICAL RULES:
- insights: MUST include an entry for EVERY id listed above
- whyItMatters: explain WHY this headline matters — do NOT repeat the headline or summary
- implications: what are the practical consequences or what should we watch for — do NOT repeat the headline
- trends: exactly 3 macro trends with DETAILED descriptions (not empty!)
  - Each trend MUST have a meaningful title and a full descriptive sentence
  - Example: {{"title": "עליית הבינה המלאכותית בתעשייה", "description": "חברות טכנולוגיה ישראליות מאמצות פתרונות בינה מלאכותית בקצב מואץ, עם השפעה על שוק העבודה והתחרותיות", "direction": "up"}}
- breakingItems: top 5 headlines with emoji prefix
- ALL text in Hebrew using simple language
- NEVER use Hebrew abbreviations with double quotes (write תל אביב not ת"א)
- NEVER copy the headline text into whyItMatters or implications
"""
    
    raw = call_gpt(
        "You are a senior Hebrew intelligence analyst writing for Israeli business executives. For each headline, provide unique analysis explaining WHY it matters and its IMPLICATIONS. For trends, provide DETAILED descriptions. Never repeat the headline text. Never invent news.",
        prompt, 3500
    )
    
    if not raw:
        return None
    
    try:
        return json.loads(raw[raw.find('{'):raw.rfind('}')+1])
    except json.JSONDecodeError:
        if repair_json:
            repaired = repair_json(raw[raw.find('{'):raw.rfind('}')+1])
            return json.loads(repaired)
        return None

# ============================================================
# PART 3b: TRANSLATE — English titles/summaries to Hebrew
# ============================================================

def translate_items_to_hebrew(items):
    """Translate English title and summary fields to Hebrew using GPT.
    
    Called for items whose content is in English (e.g., פיתוח אישי from fs.blog).
    Sends all items in a single GPT call to minimise API round-trips.
    """
    if not items:
        return items
    
    # Build a compact list for the prompt
    entries = []
    for i, item in enumerate(items):
        entries.append(f'{i}: title="{item.get("title","")[:200]}" summary="{item.get("summary","")[:300]}"')
    entries_str = "\n".join(entries)
    
    raw = call_gpt(
        "You are a professional Hebrew translator. Translate the given English article titles and summaries to natural, fluent Hebrew. Return ONLY a JSON object.",
        f"""Translate each entry to Hebrew. Return JSON:
{{"translations": [
  {{"index": 0, "title": "Hebrew title", "summary": "Hebrew summary"}},
  ...
]}}

Entries to translate:
{entries_str}

Rules:
- Translate naturally and fluently into Hebrew
- Keep proper nouns (company names, people names) in their original form or common Hebrew transliteration
- summary should be a complete Hebrew sentence, not truncated
- Return ONLY the JSON object, nothing else""",
        1500
    )
    
    if not raw:
        print("    Translation: ⚠️ GPT failed, keeping original English")
        return items
    
    try:
        parsed = json.loads(raw[raw.find('{'):raw.rfind('}')+1])
    except json.JSONDecodeError:
        if repair_json:
            try:
                parsed = json.loads(repair_json(raw[raw.find('{'):raw.rfind('}')+1]))
            except Exception:
                print("    Translation: ⚠️ JSON parse failed, keeping original English")
                return items
        else:
            print("    Translation: ⚠️ JSON parse failed, keeping original English")
            return items
    
    translations = {t["index"]: t for t in parsed.get("translations", [])}
    for i, item in enumerate(items):
        if i in translations:
            t = translations[i]
            if t.get("title"):
                item["title"] = t["title"]
            if t.get("summary"):
                item["summary"] = t["summary"]
    
    print(f"    Translation: ✅ {len(translations)} items translated to Hebrew")
    return items

# ============================================================
# PART 4: SANITIZE — Clean Hebrew abbreviations + HTML entities
# ============================================================

ABBREVS = {
    'ת"א':'תל אביב','נאסד"ק':'נאסדק','מנכ"ל':'מנהל כללי','צה"ל':'צהל',
    'שב"כ':'שבכ','הלמ"ס':'הלמס','סמנכ"ל':'סמנהל כללי','ד"ר':'דוקטור',
    'עו"ד':'עורך דין','רו"ח':'רואה חשבון','יו"ר':'יושב ראש',
    'ארה"ב':'ארצות הברית','או"ם':'האומות המאוחדות','מו"מ':'משא ומתן',
    'חו"ל':'חול','בע"מ':'בעמ','רמטכ"ל':'רמטכל','סנ"צ':'סנץ','תנ"ך':'תנך',
    'בד"כ':'בדרך כלל','כד"ב':'כדור בסיס','בג"ץ':'בגץ','ש"ח':'שקלים',
}

def sanitize(s):
    if not isinstance(s, str): return str(s) if s is not None else ""
    # Decode HTML entities
    s = html_mod.unescape(s)
    # Replace bullet chars with dash
    s = s.replace('\u2022', ' - ').replace('\xa0', ' ')
    for a, r in ABBREVS.items():
        s = s.replace(a, r)
    # Remove remaining Hebrew double-quote patterns
    s = re.sub(r'([\u0590-\u05FF])"([\u0590-\u05FF])', r'\1\2', s)
    # Remove broken/truncated HTML entities
    s = re.sub(r'&#\d*$', '', s)
    s = re.sub(r'&\w*$', '', s)
    # Clean up multiple spaces
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s

def ts(s):
    """Escape string for TypeScript."""
    s = sanitize(str(s))
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")

# ============================================================
# PART 5: BUILD TYPESCRIPT — NO market section, NO industry section
# ============================================================

def build_typescript(news_items, content_items, wine_items, tourism_items, 
                     market_data, insights, now):
    date_str = now.strftime("%H:%M %d.%m.%Y")
    news_date = now.strftime("%d.%m.%Y")
    
    # Apply insights to news items — match by id
    insight_map = {}
    if insights:
        for ins in insights.get("insights", []):
            ins_id = ins.get("id")
            if ins_id is not None:
                insight_map[int(ins_id)] = ins
    
    # Category-based fallback implications
    CATEGORY_FALLBACKS = {
        "כלכלה": "השפעה אפשרית על שוק ההון ועל הכלכלה הישראלית",
        "פוליטיקה": "עשוי להשפיע על מדיניות הממשלה ועל הציבור",
        "צבא וביטחון": "השלכות ביטחוניות שיש לעקוב אחריהן",
        "ביטחון": "השלכות ביטחוניות שיש לעקוב אחריהן",
        "חברה": "נושא חברתי שמשפיע על השיח הציבורי",
        "טכנולוגיה": "השפעה על תעשיית ההייטק והחדשנות",
        "רשת חברתית": "מגמה שכדאי לעקוב אחריה",
        "אירועים": "הזדמנות לנטוורקינג ולמידה מקצועית",
        "בידור": "משקף את מגמות התרבות והבידור",
        "תיירות": "השפעה על ענף התיירות והמלונאות בישראל",
        "יין": "מגמה שכדאי לעקוב לאוהבי יין ומשקיעים",
    }
    
    for item in news_items + content_items + wine_items + tourism_items:
        item_id = item.get("id", 0)
        ins = insight_map.get(item_id, {})
        cat = item.get("category", "")
        
        if ins.get("whyItMatters"):
            item["whyItMatters"] = ins["whyItMatters"]
        elif not item.get("whyItMatters") or item.get("whyItMatters") == item.get("summary"):
            item["whyItMatters"] = CATEGORY_FALLBACKS.get(cat, "כתבה שכדאי לעקוב אחריה")
        
        if ins.get("implications"):
            item["implications"] = ins["implications"]
        elif not item.get("implications"):
            item["implications"] = CATEGORY_FALLBACKS.get(cat, "ממשיכים לעקוב אחר התפתחויות")
    
    # Report
    report = insights or {}
    
    # Breaking items: always derive from actual news items (not GPT)
    # This ensures the red bar always reflects the CURRENT headlines
    CATEGORY_EMOJIS = {
        "כלכלה": "📈",
        "פוליטיקה": "🏛️",
        "צבא וביטחון": "⚔️",
        "ביטחון": "🛡️",
        "חברה": "👥",
        "טכנולוגיה": "🤖",
        "רשת חברתית": "🌐",
        "אירועים": "📅",
        "בידור": "🎬",
        "תיירות": "✈️",
        "יין": "🍷",
    }
    # Collect one headline per category to ensure variety
    seen_cats = set()
    breaking = []
    all_items = news_items + content_items + tourism_items + wine_items
    for item in all_items:
        cat = item.get("category", "")
        if cat not in seen_cats and len(breaking) < 5:
            emoji = CATEGORY_EMOJIS.get(cat, "📰")
            title = item.get("title", "")[:60]
            breaking.append(f"{emoji} {title}")
            seen_cats.add(cat)
    # If we still have fewer than 5, fill from remaining items
    for item in all_items:
        if len(breaking) >= 5:
            break
        title = item.get("title", "")[:60]
        # Check if this title is already in breaking
        if not any(title[:30] in b for b in breaking):
            cat = item.get("category", "")
            emoji = CATEGORY_EMOJIS.get(cat, "📰")
            breaking.append(f"{emoji} {title}")
    breaking_ts = ", ".join(f'"{ts(b)}"' for b in breaking[:5])
    
    exec_summary = report.get("executiveSummary", "")
    if not exec_summary or exec_summary == "עדכון חדשות יומי":
        top_titles = [i.get("title", "")[:60] for i in news_items[:3]]
        if top_titles:
            exec_summary = f"הכותרות המרכזיות היום: {top_titles[0]}"
            if len(top_titles) > 1:
                exec_summary += f". בנוסף: {top_titles[1]}"
            if len(top_titles) > 2:
                exec_summary += f". וגם: {top_titles[2]}"
        else:
            exec_summary = "סקירת חדשות יומית — ראו פירוט בכתבות למטה"
    conclusion = report.get("conclusion", "")
    if not conclusion:
        conclusion = "המשיכו לעקוב אחר ההתפתחויות במהלך היום"
    watch24 = report.get("watchNext24h", "")
    if not watch24:
        watch24 = "מעקב אחר התפתחויות בזירה הפוליטית-ביטחונית"
    
    # News items TypeScript
    def item_ts(i):
        return f'  {{ id: {i.get("id",0)}, type: "{ts(i.get("type","news"))}", category: "{ts(i.get("category",""))}", title: "{ts(i.get("title",""))}", summary: "{ts(i.get("summary",""))}", whyItMatters: "{ts(i.get("whyItMatters",""))}", implications: "{ts(i.get("implications",""))}", importance: {i.get("importance",5)}, sourceUrl: "{ts(i.get("sourceUrl","#"))}", sourceName: "{ts(i.get("sourceName",""))}" }}'
    
    news_ts = ",\n".join(item_ts(i) for i in news_items)
    content_ts = ",\n".join(item_ts(i) for i in content_items)
    wine_ts_str = ",\n".join(item_ts(i) for i in wine_items)
    tourism_ts_str = ",\n".join(item_ts(i) for i in tourism_items)
    
    # Trends — with strong fallback
    trends = report.get("trends", [])
    # Validate trends have real content and valid direction
    VALID_DIRECTIONS = {"up", "down", "stable"}
    for t in trends:
        if t.get("direction") not in VALID_DIRECTIONS:
            t["direction"] = "stable"
    valid_trends = [t for t in trends if t.get("description") and len(t.get("description", "")) > 5]
    if len(valid_trends) < 3:
        valid_trends = [
            {"title": "עליית הבינה המלאכותית", "description": "חברות ישראליות מאמצות פתרונות בינה מלאכותית בקצב מואץ, עם השפעה על שוק העבודה והתחרותיות הגלובלית", "direction": "up"},
            {"title": "מתיחות גיאופוליטית", "description": "ההתפתחויות הביטחוניות באזור ממשיכות להשפיע על הכלכלה, התיירות וסביבת העסקים בישראל", "direction": "stable"},
            {"title": "שוק הקריפטו", "description": "המטבעות הדיגיטליים ממשיכים לתפוס מקום מרכזי בשיח הכלכלי עם תנודתיות גבוהה ורגולציה מתפתחת", "direction": "up"},
        ]
    trends_ts = ",\n".join(
        f'  {{ title: "{ts(t.get("title",""))}", description: "{ts(t.get("description",""))}", direction: "{t.get("direction","stable")}" }}'
        for t in valid_trends[:3]
    )
    
    # Market data
    def midx(i):
        return f'    {{ name: "{ts(i.get("name",""))}", value: "{ts(i.get("value",""))}", change: "{ts(i.get("change",""))}", direction: "{i.get("direction","stable")}" }}'
    
    indices = ",\n".join(midx(i) for i in market_data.get("indices", []))
    currencies = ",\n".join(midx(i) for i in market_data.get("currencies", []))
    commodities = ",\n".join(midx(i) for i in market_data.get("commodities", []))
    
    # Market headlines from scraped data
    il_headlines = [i["title"][:60] for i in (
        [x for x in news_items if x.get("category") == "כלכלה"][:3]
    )]
    ws_headlines = [i["title"][:60] for i in (
        [x for x in news_items + content_items if "stock" in x.get("title","").lower() or "market" in x.get("title","").lower() or "crypto" in x.get("title","").lower()][:3]
    )]
    if not il_headlines:
        il_headlines = [i["title"][:60] for i in news_items[:3]]
    if not ws_headlines:
        ws_headlines = [i["title"][:60] for i in news_items[3:6]]
    
    il_h = ", ".join(f'"{ts(h)}"' for h in il_headlines)
    ws_h = ", ".join(f'"{ts(h)}"' for h in ws_headlines)
    watch_tomorrow = market_data.get("watchTomorrow", watch24 or "מעקב אחר שווקים")
    
    # NO INDUSTRY section anymore
    
    typescript = f"""// Eldar Intelligence Hub — Daily Data
// Auto-updated: {date_str} IST
// Generated by Sofia v11 — Real Data Only, GPT for Insights Only
export interface NewsItem {{
  id: number;
  type: "news" | "content";
  category: string;
  title: string;
  summary: string;
  whyItMatters: string;
  implications: string;
  importance: number;
  sourceUrl: string;
  sourceName: string;
  authorName?: string;
}}

export interface Trend {{
  title: string;
  description: string;
  direction: "up" | "down" | "stable";
}}

export interface MarketIndex {{
  name: string;
  value: string;
  change: string;
  direction: "up" | "down" | "stable";
}}

export interface MarketData {{
  date: string;
  indices: MarketIndex[];
  currencies: MarketIndex[];
  commodities: MarketIndex[];
  israelHeadlines: string[];
  wallStreetHeadlines: string[];
  watchTomorrow: string;
}}

export const NEWS_DATE = "{news_date}";

export const LAST_UPDATED = "{date_str}";

export const REPORT = {{
  date: NEWS_DATE,
  breakingItems: [{breaking_ts}],
  executiveSummary: "{ts(exec_summary)}",
  conclusion: "{ts(conclusion)}",
  watchNext24h: "{ts(watch24)}",
}};

export const NEWS_ITEMS: NewsItem[] = [
{news_ts}
];

export const CONTENT_ITEMS: NewsItem[] = [
{content_ts}
];

export const TRENDS: Trend[] = [
{trends_ts}
];

export const WINE_NEWS: NewsItem[] = [
{wine_ts_str}
];

export const TOURISM_NEWS: NewsItem[] = [
{tourism_ts_str}
];

export const MARKET_DATA: MarketData = {{
  date: NEWS_DATE,
  indices: [
{indices}
  ],
  currencies: [
{currencies}
  ],
  commodities: [
{commodities}
  ],
  israelHeadlines: [{il_h}],
  wallStreetHeadlines: [{ws_h}],
  watchTomorrow: "{ts(watch_tomorrow)}",
}};
"""
    return typescript

# ============================================================
# PART 6: SEND TELEGRAM NOTIFICATION
# ============================================================

def send_telegram(news_items, wine_items, tourism_items, insights, now):
    """Send a short Telegram notification that EIH ran successfully."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  Telegram: ⚠️ No token/chat_id")
        return False
    
    day_map = {1:"שני",2:"שלישי",3:"רביעי",4:"חמישי",5:"שישי",6:"שבת",7:"ראשון"}
    date_str = f"יום {day_map[now.isoweekday()]}, {now.day}.{now.month:02d}.{now.year} | {now.strftime('%H:%M')}"
    
    total = len(news_items) + len(wine_items) + len(tourism_items)
    
    msg = f"""✅ *EIH עודכן בהצלחה*
📅 {date_str}
📊 {total} כתבות עודכנו
🔗 [צפה באתר](https://eldar-hub-web.vercel.app)

_Sofia v11_ 🦞"""
    
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=15
        )
        ok = resp.json().get("ok", False)
        return ok
    except Exception as e:
        print(f"  Telegram error: {e}")
        return False

# ============================================================
# PART 7: PUSH TO GITHUB + VERIFY
# ============================================================

def push_to_github(typescript, now):
    gh = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    resp = requests.get(
        "https://api.github.com/repos/eldar-Claw/eldar-hub-web/contents/app/data.ts?ref=main",
        headers=gh, timeout=30
    )
    sha = resp.json().get("sha", "")
    
    payload = {
        "message": f"🧠 EIH v11 Update — {now.strftime('%d/%m/%Y %H:%M')} IST — Real Data",
        "content": base64.b64encode(typescript.encode()).decode(),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha
    
    resp = requests.put(
        "https://api.github.com/repos/eldar-Claw/eldar-hub-web/contents/app/data.ts",
        headers=gh, json=payload, timeout=30
    )
    return resp.status_code in (200, 201), resp.status_code

# ============================================================
# MAIN
# ============================================================

def main():
    now = datetime.now(IST)
    day_map = {1:"יום שני",2:"יום שלישי",3:"יום רביעי",4:"יום חמישי",5:"יום שישי",6:"יום שבת",7:"יום ראשון"}
    months = ["","בינואר","בפברואר","במרץ","באפריל","במאי","ביוני","ביולי","באוגוסט","בספטמבר","באוקטובר","בנובמבר","בדצמבר"]
    hdate = f"{day_map[now.isoweekday()]}, {now.day} {months[now.month]} {now.year}"
    tstr = now.strftime("%H:%M")
    
    print(f"=== EIH v11 — {hdate} {tstr} ===")
    print("=== REAL DATA ONLY — GPT for insights only (v11) ===\n")
    
    # Step 1: Scrape all news
    print("[1] Scraping real news...")
    scraped = scrape_all()
    
    # Step 2: Fetch real market data (includes crypto)
    print("\n[2] Fetching real market data (+ crypto)...")
    market_data = fetch_market_data()
    
    # Step 3: Select best items (no GPT)
    print("\n[3] Selecting items...")
    news_items = select_news_items(scraped, max_per_cat=2, total_max=17)
    content_items = select_content_items(scraped, max_items=5)
    wine_items = select_wine_items(scraped, max_items=5)
    tourism_items = select_tourism_items(scraped, max_items=5)
    
    print(f"  News: {len(news_items)}, Content: {len(content_items)}, Wine: {len(wine_items)}, Tourism: {len(tourism_items)}")
    
    # Step 3b: Translate פיתוח אישי items (English → Hebrew)
    print("\n[3b] Translating פיתוח אישי items to Hebrew...")
    pituch_ishi_items = [i for i in news_items if i.get("category") == "פיתוח אישי"]
    if pituch_ishi_items:
        translated = translate_items_to_hebrew(pituch_ishi_items)
        # Update in-place within news_items
        id_to_translated = {i["id"]: i for i in translated}
        for item in news_items:
            if item["id"] in id_to_translated:
                item["title"] = id_to_translated[item["id"]]["title"]
                item["summary"] = id_to_translated[item["id"]]["summary"]
    else:
        print("    No פיתוח אישי items found, skipping translation")

    # Step 4: GPT for insights ONLY
    print("\n[4] GPT — Insights only...")
    market_headlines = [f"{i['name']}: {i['value']} ({i['change']})" for i in 
                        market_data.get("indices", []) + market_data.get("commodities", [])]
    insights = get_insights(news_items + wine_items + tourism_items, market_headlines)
    if insights:
        print("  Insights: ✅")
        # Verify trends have content
        trends = insights.get("trends", [])
        for t in trends:
            print(f"    Trend: {t.get('title', 'N/A')} — {t.get('description', 'EMPTY')[:50]}")
    else:
        print("  Insights: ⚠️ GPT failed, using defaults")
    
    # Step 5: Build TypeScript (NO industry)
    print("\n[5] Building TypeScript...")
    typescript = build_typescript(
        news_items, content_items, wine_items, tourism_items,
        market_data, insights, now
    )
    print(f"  Generated: {len(typescript)} chars")
    
    # Save locally (backup)
    with open("/tmp/v11_data.ts", "w") as f:
        f.write(typescript)
    
    # CRITICAL: Also write to the local app/data.ts so Vercel build picks up new data
    local_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data.ts")
    # Fallback: if running from repo root, try relative path
    if not os.path.isdir(os.path.dirname(local_data_path)):
        local_data_path = os.path.join(os.getcwd(), "app", "data.ts")
    try:
        os.makedirs(os.path.dirname(local_data_path), exist_ok=True)
        with open(local_data_path, "w", encoding="utf-8") as f:
            f.write(typescript)
        print(f"  Local write: ✅ ({local_data_path})")
    except Exception as e:
        print(f"  Local write: ❌ ({e})")
    
    # Validate — NO INDUSTRY_NEWS check
    checks = ["NEWS_DATE","LAST_UPDATED","REPORT","NEWS_ITEMS","CONTENT_ITEMS","TRENDS","WINE_NEWS","TOURISM_NEWS","MARKET_DATA"]
    ok = all(f"export const {c}" in typescript for c in checks)
    print(f"  Validation: {'✅ 9/9' if ok else '❌'}")
    
    if not ok:
        print("  ABORT: validation failed")
        return
    
    # Step 6: Push to GitHub (for persistence across runs)
    print("\n[6] Pushing to GitHub...")
    success, status = push_to_github(typescript, now)
    print(f"  Push: {'✅' if success else '❌'} ({status})")
    
    # Step 7: Send Telegram notification ONLY if push succeeded
    if success:
        print("\n[7] Sending Telegram...")
        tg_ok = send_telegram(news_items, wine_items, tourism_items, insights, now)
        print(f"  Telegram: {'✅' if tg_ok else '❌'}")
    else:
        print("\n[7] Skipping Telegram — push failed")
        print("  ABORT: push failed")
        return
    
    # Step 8: Verify local data.ts matches what we generated
    print("\n[8] Verifying local data.ts...")
    try:
        with open(local_data_path, "r", encoding="utf-8") as f:
            local_content = f.read()
        if local_content == typescript:
            print("  Verify: ✅ local data.ts matches generated content")
        else:
            print("  Verify: ⚠️ local data.ts differs — overwriting again")
            with open(local_data_path, "w", encoding="utf-8") as f:
                f.write(typescript)
    except Exception as e:
        print(f"  Verify: ❌ ({e})")
    
    print(f"\n=== DONE! v11 — Real Data ===")

if __name__ == "__main__":
    main()


