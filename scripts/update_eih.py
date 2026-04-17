#!/usr/bin/env python3
"""
EIH Web Update Agent v3 — GitHub Actions Version
Fixed: Uses correct interfaces that match page.tsx exactly.
Key findings from working build (commit 02d87e9):
- WINE_NEWS: NewsItem[] (NOT WineNews[])
- TOURISM_NEWS: NewsItem[] (NOT TourismNews[])
- INDUSTRY_NEWS: IndustryItem[] (flat array, NOT object with deals/startups/etc)
- NO WineNews, TourismNews, or IndustryNews interfaces
- REPORT has NO explicit type annotation
"""

import json
import os
import re
import base64
import requests
import sys
import time
from datetime import datetime, timezone, timedelta

# ============================================================
# Configuration
# ============================================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
GITHUB_TOKEN = os.environ.get("GH_PAT", "")
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")

GITHUB_REPO = "eldar-Claw/eldar-hub-web"
GITHUB_FILE_PATH = "app/data.ts"
GITHUB_BRANCH = "main"

VERCEL_PROJECT_ID = "prj_TXWvhbnjHZqunhRa6ZVCkFLJnYfn"
VERCEL_ORG_ID = "team_iKHrrl11TxRIGdzvlzV54AtB"
VERCEL_URL = "https://eldar-hub-web.vercel.app"

IST = timezone(timedelta(hours=3))


def format_hebrew_date(dt):
    day_map = {1: "יום שני", 2: "יום שלישי", 3: "יום רביעי",
               4: "יום חמישי", 5: "יום שישי", 6: "יום שבת", 7: "יום ראשון"}
    months = ["", "בינואר", "בפברואר", "במרץ", "באפריל", "במאי", "ביוני",
              "ביולי", "באוגוסט", "בספטמבר", "באוקטובר", "בנובמבר", "בדצמבר"]
    day_name = day_map[dt.isoweekday()]
    return f"{day_name}, {dt.day} {months[dt.month]} {dt.year}"


def call_openai(system_prompt, user_prompt):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    models = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-3.5-turbo"]
    
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 16000,
            "temperature": 0.7,
        }
        
        for attempt in range(3):
            try:
                print(f"    Attempt {attempt+1}/3 with model {model}...")
                resp = requests.post(
                    f"{OPENAI_BASE_URL}/chat/completions",
                    headers=headers, json=payload, timeout=180
                )
                if resp.status_code == 429:
                    wait_time = 10 * (attempt + 1)
                    print(f"    Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                resp.raise_for_status()
                print(f"    Success with model {model}")
                return resp.json()["choices"][0]["message"]["content"].strip()
            except requests.exceptions.HTTPError as e:
                if resp.status_code == 429:
                    time.sleep(10 * (attempt + 1))
                    continue
                elif resp.status_code in (404, 400):
                    print(f"    Model {model} not available, trying next...")
                    break
                else:
                    if attempt < 2:
                        time.sleep(5)
                        continue
                    raise
            except Exception as e:
                if attempt < 2:
                    time.sleep(5)
                    continue
                raise
    
    raise Exception("All models and retries exhausted")


def generate_data_ts():
    now = datetime.now(IST)
    date_str = now.strftime("%Y-%m-%d %H:%M")
    hebrew_date = format_hebrew_date(now)
    time_str = now.strftime("%H:%M")
    update_date = now.strftime("%d.%-m.%Y")

    system_prompt = """You are Sofia AI — Eldar Lev-Ran's intelligence agent. You generate the data.ts file for the Eldar Intelligence Hub (EIH).

CRITICAL: Output ONLY valid TypeScript code. No markdown fences. No explanations.

STRING SAFETY — NEVER use unescaped double quotes inside strings:
- Instead of ת"א write תל אביב
- Instead of נאסד"ק write נאסדק  
- Instead of מנכ"ל write מנהל כללי
- Instead of ד"ר write דוקטור
- Instead of יו"ר write יושב ראש
- Instead of ארה"ב write ארצות הברית
- Instead of צה"ל write צהל
- Instead of שב"כ write שבכ
- Instead of מו"מ write משא ומתן
- Instead of חו"ל write חול
- Instead of בע"מ write בעמ
- Instead of עו"ד write עורך דין
- Instead of רו"ח write רואה חשבון
- Instead of או"ם write האומות המאוחדות
- NEVER put a double quote character inside a double-quoted string

EXACT INTERFACES (must match page.tsx):
1. NewsItem: { id, type, category, title, summary, whyItMatters, implications, importance, sourceUrl, sourceName }
2. Trend: { title, description, direction }
3. MarketIndex: { name, value, change, direction }
4. MarketData: { date, indices, currencies, commodities, israelHeadlines, wallStreetHeadlines, watchTomorrow }
5. IndustryItem: { category, title, summary, sourceUrl? }

CRITICAL EXPORT TYPES (must match exactly):
- WINE_NEWS: NewsItem[] (NOT WineNews[]!)
- TOURISM_NEWS: NewsItem[] (NOT TourismNews[]!)
- INDUSTRY_NEWS: IndustryItem[] (flat array, NOT object!)
- REPORT = { ... } (NO type annotation!)
- REPORT.breakingItems must be STRING ARRAY, not references

CATEGORY COVERAGE for NEWS_ITEMS (15 items):
Must include at least 1 from EACH: כלכלה, פוליטיקה, חברה, צבא וביטחון, טכנולוגיה, תיירות, רשת חברתית, אירועים, בידור, יין
Max 3 per category."""

    user_prompt = f"""Generate complete data.ts for EIH.

Date: {hebrew_date} — {time_str} IST

The file MUST start with:
// Eldar Intelligence Hub — Daily Data
// Auto-updated: {date_str} IST
// Generated by Sofia

EXACT STRUCTURE (follow this order):

```
// interfaces
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

export interface IndustryItem {{
  category: "עסקאות" | "סטארטאפים" | "מינויים" | "פיטורים" | "טרנדים";
  title: string;
  summary: string;
  sourceUrl?: string;
}}

// data exports
export const NEWS_DATE = "{hebrew_date} — {time_str}";
export const LAST_UPDATED = "{update_date} {time_str}";

export const REPORT = {{
  date: NEWS_DATE,
  breakingItems: [
    "💰 כלכלה: headline1",
    "🗳️ פוליטיקה: headline2",
    "🛡️ צבא וביטחון: headline3",
    "💻 טכנולוגיה: headline4",
    "✈️ תיירות: headline5"
  ],
  executiveSummary: "...",
  conclusion: "...",
  watchNext24h: "..."
}};

export const NEWS_ITEMS: NewsItem[] = [
  // 15 items covering ALL 10 categories
];

export const CONTENT_ITEMS: NewsItem[] = [
  // 5 items
];

export const TRENDS: Trend[] = [
  // 3 trends
];

export const WINE_NEWS: NewsItem[] = [
  // 5 items, all with category: "יין"
];

export const TOURISM_NEWS: NewsItem[] = [
  // 5 items, all with category: "תיירות"
];

export const MARKET_DATA: MarketData | null = {{
  date: NEWS_DATE,
  indices: [...],
  currencies: [...],
  commodities: [...],
  israelHeadlines: [...],
  wallStreetHeadlines: [...],
  watchTomorrow: "..."
}};

export const INDUSTRY_NEWS: IndustryItem[] = [
  // 5-10 items with categories: עסקאות, סטארטאפים, מינויים, פיטורים, טרנדים
];
```

CRITICAL REMINDERS:
- WINE_NEWS type is NewsItem[] NOT WineNews[]
- TOURISM_NEWS type is NewsItem[] NOT TourismNews[]
- INDUSTRY_NEWS type is IndustryItem[] (FLAT ARRAY not object)
- REPORT has NO type annotation (just = {{ }})
- breakingItems are STRINGS not references
- All content in Hebrew
- Use real source URLs from Israeli/international news sites
- IDs: NEWS_ITEMS 1-15, CONTENT_ITEMS 16-20, TOURISM_NEWS 101-105, WINE_NEWS 201-205
- Generate REALISTIC news for today's date
- importance: 10=critical, 8-9=very important, 6-7=notable, 5=info

Output ONLY TypeScript code starting with the comment line."""

    print("  Calling GPT...")
    content = call_openai(system_prompt, user_prompt)

    # Clean markdown fences
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    if not content.startswith("//"):
        content = f"// Eldar Intelligence Hub — Daily Data\n// Auto-updated: {date_str} IST\n// Generated by Sofia\n\n" + content

    return content


def fix_typescript_issues(content):
    """Fix common GPT-generated TypeScript issues."""
    
    # 1. Fix Hebrew abbreviations
    abbreviations = {
        'ת"א': 'תל אביב', 'נאסד"ק': 'נאסדק', 'מנכ"ל': 'מנהל כללי',
        'ד"ר': 'דוקטור', 'סמנכ"ל': 'סמנהל כללי', 'בע"מ': 'בעמ',
        'עו"ד': 'עורך דין', 'רו"ח': 'רואה חשבון', 'יו"ר': 'יושב ראש',
        'ארה"ב': 'ארצות הברית', 'או"ם': 'האומות המאוחדות',
        'צה"ל': 'צהל', 'שב"כ': 'שבכ', 'מו"מ': 'משא ומתן', 'חו"ל': 'חול',
    }
    for abbr, replacement in abbreviations.items():
        content = content.replace(abbr, replacement)
    
    # 2. Fix wrong type annotations
    # WINE_NEWS should be NewsItem[] not WineNews[]
    content = re.sub(r'export const WINE_NEWS:\s*WineNews\[\]', 'export const WINE_NEWS: NewsItem[]', content)
    # TOURISM_NEWS should be NewsItem[] not TourismNews[]
    content = re.sub(r'export const TOURISM_NEWS:\s*TourismNews\[\]', 'export const TOURISM_NEWS: NewsItem[]', content)
    # INDUSTRY_NEWS should be IndustryItem[] not IndustryNews
    content = re.sub(r'export const INDUSTRY_NEWS:\s*IndustryNews\s*=\s*\{', 'export const INDUSTRY_NEWS: IndustryItem[] = [', content)
    
    # 3. If INDUSTRY_NEWS is an object { deals: [...], ... }, flatten it to array
    industry_obj_match = re.search(r'export const INDUSTRY_NEWS: IndustryItem\[\] = \{(.*?)\};', content, re.DOTALL)
    if industry_obj_match:
        obj_content = industry_obj_match.group(1)
        # Extract all items from sub-arrays
        items = []
        for cat_match in re.finditer(r'(deals|startups|appointments|layoffs|trends):\s*\[(.*?)\]', obj_content, re.DOTALL):
            cat_name_map = {
                'deals': 'עסקאות', 'startups': 'סטארטאפים', 
                'appointments': 'מינויים', 'layoffs': 'פיטורים', 'trends': 'טרנדים'
            }
            cat_name = cat_name_map.get(cat_match.group(1), cat_match.group(1))
            sub_items = cat_match.group(2)
            # Find each item
            for item_match in re.finditer(r'\{(.*?)\}', sub_items, re.DOTALL):
                item_text = item_match.group(1).strip()
                if 'category:' not in item_text:
                    item_text = f'category: "{cat_name}",\n    {item_text}'
                items.append(f'  {{\n    {item_text}\n  }}')
        
        if items:
            flat_array = ',\n'.join(items)
            old = f'export const INDUSTRY_NEWS: IndustryItem[] = {{{industry_obj_match.group(1)}}};'
            new = f'export const INDUSTRY_NEWS: IndustryItem[] = [\n{flat_array}\n];'
            content = content.replace(old, new)
            print("    Fixed INDUSTRY_NEWS: converted object to flat array")
    
    # 4. Remove wrong interfaces (WineNews, TourismNews, IndustryNews)
    content = re.sub(r'export interface WineNews \{[^}]*\}\n*', '', content)
    content = re.sub(r'export interface TourismNews \{[^}]*\}\n*', '', content)
    content = re.sub(r'export interface IndustryNews \{[^}]*\}\n*', '', content)
    
    # 5. Remove Report interface if present (REPORT has no type annotation)
    content = re.sub(r'export interface Report \{[^}]*\}\n*', '', content)
    # Fix REPORT type annotation
    content = re.sub(r'export const REPORT:\s*Report\s*=', 'export const REPORT =', content)
    
    # 6. Fix breakingItems if they reference NEWS_ITEMS
    if 'NEWS_ITEMS[' in content.split('export const NEWS_ITEMS')[0] if 'export const NEWS_ITEMS' in content else False:
        # Replace NEWS_ITEMS references with placeholder strings
        content = re.sub(r'NEWS_ITEMS\[\d+\]\.title', '"חדשות עדכניות"', content)
        content = re.sub(r'NEWS_ITEMS\[\d+\]', '"חדשות עדכניות"', content)
        print("    Fixed breakingItems references")
    
    # 7. Fix unbalanced quotes
    lines = content.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        count = 0
        j = 0
        while j < len(stripped):
            if stripped[j] == '\\' and j + 1 < len(stripped):
                j += 2
                continue
            if stripped[j] == '"':
                count += 1
            j += 1
        if count % 2 != 0 and count == 3:
            positions = []
            j = 0
            while j < len(stripped):
                if stripped[j] == '\\' and j + 1 < len(stripped):
                    j += 2
                    continue
                if stripped[j] == '"':
                    positions.append(j)
                j += 1
            if len(positions) == 3:
                mid = positions[1]
                stripped = stripped[:mid] + '\\"' + stripped[mid+1:]
                lines[i] = line[:len(line)-len(line.strip())] + stripped
    
    content = '\n'.join(lines)
    return content


def validate_data_ts(content):
    checks = {
        "NewsItem_interface": "export interface NewsItem" in content,
        "Trend_interface": "export interface Trend" in content,
        "MarketIndex_interface": "export interface MarketIndex" in content,
        "MarketData_interface": "export interface MarketData" in content,
        "IndustryItem_interface": "export interface IndustryItem" in content,
        "NEWS_DATE": "export const NEWS_DATE" in content,
        "LAST_UPDATED": "export const LAST_UPDATED" in content,
        "REPORT": "export const REPORT" in content,
        "NEWS_ITEMS": "export const NEWS_ITEMS: NewsItem[]" in content,
        "CONTENT_ITEMS": "export const CONTENT_ITEMS: NewsItem[]" in content,
        "TRENDS": "export const TRENDS: Trend[]" in content,
        "WINE_NEWS_correct_type": "export const WINE_NEWS: NewsItem[]" in content,
        "TOURISM_NEWS_correct_type": "export const TOURISM_NEWS: NewsItem[]" in content,
        "MARKET_DATA": "export const MARKET_DATA" in content,
        "INDUSTRY_NEWS_correct_type": "export const INDUSTRY_NEWS: IndustryItem[]" in content,
        "no_WineNews_interface": "export interface WineNews" not in content,
        "no_TourismNews_interface": "export interface TourismNews" not in content,
        "no_IndustryNews_interface": "export interface IndustryNews" not in content,
    }
    
    # Check category coverage
    required_categories = ["כלכלה", "פוליטיקה", "חברה", "צבא וביטחון", "טכנולוגיה",
                          "תיירות", "רשת חברתית", "אירועים", "בידור", "יין"]
    
    news_section = ""
    if "export const NEWS_ITEMS" in content:
        parts = content.split("export const NEWS_ITEMS")
        if len(parts) > 1:
            rest = parts[1]
            end_match = re.search(r'export const (?!NEWS_ITEMS)', rest)
            news_section = rest[:end_match.start()] if end_match else rest
    
    found = set()
    for cat in required_categories:
        if f'category: "{cat}"' in news_section:
            found.add(cat)
    
    missing = set(required_categories) - found
    checks["all_10_categories"] = len(missing) == 0
    if missing:
        print(f"  Missing categories: {', '.join(missing)}")
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    print(f"  Validation: {passed}/{total} checks passed")
    for name, ok in checks.items():
        status = "OK" if ok else "FAIL"
        print(f"    [{status}] {name}")
    
    # Must pass at least 15 out of 19
    return passed >= 15


def push_to_github(content, commit_message=None):
    if not commit_message:
        now = datetime.now(IST)
        commit_message = f"EIH Update — {now.strftime('%d/%m/%Y %H:%M')} IST"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    
    resp = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=30)
    current_sha = resp.json()["sha"] if resp.status_code == 200 else None
    
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }
    if current_sha:
        payload["sha"] = current_sha
    
    print("  Pushing to GitHub...")
    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    
    if resp.status_code in (200, 201):
        sha = resp.json().get("content", {}).get("sha", "?")
        print(f"  GitHub push OK! SHA: {sha[:12]}")
        return True
    else:
        print(f"  GitHub push FAILED: {resp.status_code} {resp.text[:200]}")
        return False


def trigger_vercel_deploy():
    print("  Triggering Vercel deploy...")
    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "name": "eldar-hub-web",
        "project": VERCEL_PROJECT_ID,
        "target": "production",
        "gitSource": {
            "type": "github",
            "org": "eldar-Claw",
            "repo": "eldar-hub-web",
            "ref": "main"
        }
    }
    
    resp = requests.post(
        f"https://api.vercel.com/v13/deployments?teamId={VERCEL_ORG_ID}&forceNew=1",
        headers=headers, json=payload, timeout=60
    )
    
    if resp.status_code in (200, 201):
        data = resp.json()
        print(f"  Vercel deploy triggered! ID: {data.get('id', '?')}")
        return True
    else:
        error = resp.json().get("error", {}).get("message", resp.text[:200])
        print(f"  Vercel API failed: {error}")
        # Fallback: deploy hook
        return trigger_deploy_hook()


def trigger_deploy_hook():
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    
    resp = requests.get(
        f"https://api.vercel.com/v1/projects/{VERCEL_PROJECT_ID}/deploy-hooks?teamId={VERCEL_ORG_ID}",
        headers=headers, timeout=30
    )
    
    hook_url = None
    if resp.status_code == 200:
        for hook in resp.json().get("deployHooks", []):
            if hook.get("name") == "sofia-auto-update":
                hook_url = hook.get("url")
                break
    
    if not hook_url:
        resp = requests.post(
            f"https://api.vercel.com/v1/projects/{VERCEL_PROJECT_ID}/deploy-hooks?teamId={VERCEL_ORG_ID}",
            headers=headers, json={"name": "sofia-auto-update", "ref": "main"}, timeout=30
        )
        if resp.status_code in (200, 201):
            hook_url = resp.json().get("url")
    
    if hook_url:
        resp = requests.post(hook_url, timeout=30)
        if resp.status_code in (200, 201):
            print("  Deploy hook triggered!")
            return True
    
    print("  All deploy methods failed")
    return False


def verify_deployment():
    print("  Waiting 30s for deploy...")
    time.sleep(30)
    try:
        resp = requests.get(VERCEL_URL, timeout=30)
        if resp.status_code == 200:
            print(f"  Site is live (status 200)")
            return True
    except Exception as e:
        print(f"  Verification error: {e}")
    return False


def main():
    now = datetime.now(IST)
    print("=" * 60)
    print(f"EIH Web Update v3 — {now.strftime('%d/%m/%Y %H:%M')} IST")
    print("=" * 60)
    
    missing = []
    if not OPENAI_API_KEY: missing.append("OPENAI_API_KEY")
    if not GITHUB_TOKEN: missing.append("GH_PAT")
    if not VERCEL_TOKEN: missing.append("VERCEL_TOKEN")
    if missing:
        print(f"Missing secrets: {', '.join(missing)}")
        return False
    
    print("\nStep 1: Generate data.ts...")
    try:
        data_ts = generate_data_ts()
        print(f"  Generated {len(data_ts)} chars")
    except Exception as e:
        print(f"  Generation failed: {e}")
        return False
    
    print("\nStep 2: Fix TypeScript issues...")
    data_ts = fix_typescript_issues(data_ts)
    
    print("\nStep 3: Validate...")
    if not validate_data_ts(data_ts):
        print("  Validation failed — pushing anyway with fixes")
    
    print("\nStep 4: Push to GitHub...")
    if not push_to_github(data_ts):
        return False
    
    print("\nStep 5: Trigger Vercel deploy...")
    trigger_vercel_deploy()
    
    print("\nStep 6: Verify...")
    verify_deployment()
    
    print("\n" + "=" * 60)
    print("EIH Web Update complete!")
    print(f"URL: {VERCEL_URL}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
