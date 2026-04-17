#!/usr/bin/env python3
"""
EIH Web Update Agent — GitHub Actions Version
Generates fresh data.ts with GPT, pushes to GitHub, triggers Vercel deploy.
Runs as a GitHub Actions workflow — no local dependencies needed.
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
# Configuration — from environment variables (GitHub Secrets)
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
    """Format date in Hebrew."""
    day_map = {1: "יום שני", 2: "יום שלישי", 3: "יום רביעי",
               4: "יום חמישי", 5: "יום שישי", 6: "יום שבת", 7: "יום ראשון"}
    months = ["", "בינואר", "בפברואר", "במרץ", "באפריל", "במאי", "ביוני",
              "ביולי", "באוגוסט", "בספטמבר", "באוקטובר", "בנובמבר", "בדצמבר"]
    day_name = day_map[dt.isoweekday()]
    return f"{day_name}, {dt.day} {months[dt.month]} {dt.year}"


def call_openai(system_prompt, user_prompt):
    """Call OpenAI API with retry logic."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    # Try multiple models in order of preference
    models = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-3.5-turbo"]
    
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 12000,
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
                    print(f"    ⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                resp.raise_for_status()
                print(f"    ✅ Success with model {model}")
                return resp.json()["choices"][0]["message"]["content"].strip()
            except requests.exceptions.HTTPError as e:
                if resp.status_code == 429:
                    wait_time = 10 * (attempt + 1)
                    print(f"    ⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif resp.status_code in (404, 400):
                    print(f"    ⚠️ Model {model} not available ({resp.status_code}), trying next...")
                    break  # Try next model
                else:
                    print(f"    ❌ HTTP error: {e}")
                    if attempt < 2:
                        time.sleep(5)
                        continue
                    raise
            except Exception as e:
                print(f"    ❌ Error: {e}")
                if attempt < 2:
                    time.sleep(5)
                    continue
                raise
    
    raise Exception("All models and retries exhausted")


def generate_data_ts():
    """Use GPT to generate a complete, fresh data.ts file."""
    now = datetime.now(IST)
    date_str = now.strftime("%Y-%m-%d %H:%M")
    hebrew_date = format_hebrew_date(now)
    time_str = now.strftime("%H:%M")
    update_str = now.strftime("%d.%-m.%Y %H:%M")

    system_prompt = """You are Sofia AI — Eldar Lev-Ran's intelligence agent. You generate the data.ts file for the Eldar Intelligence Hub (EIH) web application.

Your job: Create a COMPLETE, VALID TypeScript file with FRESH, REAL news data.

CRITICAL RULES:
1. Output ONLY valid TypeScript code — no markdown, no code fences, no explanations
2. Use REAL news from the last 24-48 hours. Use real source URLs from major Israeli and international news sites.
3. Hebrew content for titles, summaries, whyItMatters, implications
4. Follow the EXACT interfaces and structure provided
5. Include ALL sections: NEWS_ITEMS (10 items), CONTENT_ITEMS (8-10 items), TRENDS (3), WINE_NEWS (3), TOURISM_NEWS (5), MARKET_DATA (with real indices), INDUSTRY_NEWS (5+ items)
6. REPORT section MUST have: date: NEWS_DATE, breakingItems (5 STRINGS), executiveSummary, conclusion, watchNext24h
7. Each NewsItem needs: id, type, category, title, summary, whyItMatters, implications, importance (1-10), sourceUrl, sourceName
8. importance scores: 10=critical breaking, 8-9=very important, 6-7=notable, 5=informational
9. IDs: NEWS_ITEMS 1-10, CONTENT_ITEMS 11-20, TOURISM_NEWS 101-110, WINE_NEWS 201-210
10. MARKET_DATA must include real index values for today or latest available
11. All source URLs must be real, working URLs from major news sites
12. Write in Hebrew — simple language, no jargon

CRITICAL STRING SAFETY RULES:
- NEVER use unescaped double quotes inside double-quoted strings
- Instead of writing the Hebrew abbreviation for Tel Aviv stock exchange (tav-quotemark-alef), write תל אביב
- Instead of the Hebrew abbreviation for Nasdaq (nun-alef-samech-dalet-quotemark-kuf), write נאסדק
- Instead of ד' or ג' (with ASCII apostrophe) write ד׳ or ג׳ (with Hebrew geresh character ׳)
- Instead of מנכ"ל write מנכל or מנהל כללי
- Instead of ד"ר write דוקטור
- REPORT.breakingItems MUST be an array of STRINGS, NOT references to NEWS_ITEMS
- Each breakingItem must be a string like: "💰 כלכלה: headline text here"
- REPORT MUST include date: NEWS_DATE as first field
- NEVER put a double quote character inside a double-quoted string — it will break the TypeScript parser
"""

    user_prompt = f"""Generate the complete data.ts file for Eldar Intelligence Hub.

Current date/time: {hebrew_date} — {time_str} IST
LAST_UPDATED: "{update_str}"
NEWS_DATE: "{hebrew_date} — {time_str}"

Search topics to cover:
- Israel economy, startups, trade, tariffs
- Israel politics, Knesset, supreme court
- AI, cybersecurity, tech startups
- Israel security, military, ceasefire
- Society, jobs, leadership
- Fine wine market, Bordeaux, Burgundy, auctions
- Tourism, flights, hotels
- Industry deals, acquisitions, layoffs
- Stock markets: S&P 500, Nasdaq, Dow Jones, TA-35
- Entertainment: Netflix, Apple TV+, events

The file MUST start with:
// Eldar Intelligence Hub — Daily Data
// Auto-updated: {date_str} IST
// Generated by Sofia 🦞

Then include ALL TypeScript interfaces and ALL data exports.

INTERFACES:
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

EXPORTS ORDER:
1. export const NEWS_DATE = "...";
2. export const LAST_UPDATED = "...";
3. export const REPORT = {{ date: NEWS_DATE, breakingItems: [STRING, STRING, ...], executiveSummary: "...", conclusion: "...", watchNext24h: "..." }};
4. export const NEWS_ITEMS: NewsItem[] = [...];
5. export const CONTENT_ITEMS: NewsItem[] = [...];
6. export const TRENDS: Trend[] = [...];
7. export const WINE_NEWS: NewsItem[] = [...];
8. export const TOURISM_NEWS: NewsItem[] = [...];
9. export const MARKET_DATA: MarketData | null = {{ ... }};
10. export const INDUSTRY_NEWS: IndustryItem[] = [...];

REMEMBER: breakingItems must be STRINGS like "💰 כלכלה: headline", NOT NEWS_ITEMS[0] references!
REMEMBER: NEVER use double quotes inside double-quoted strings. No abbreviations with quotes.
Output ONLY TypeScript code. Start with the comment line."""

    print("  🤖 Calling GPT to generate data.ts...")
    content = call_openai(system_prompt, user_prompt)

    # Clean up — remove markdown fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    # Ensure it starts correctly
    if not content.startswith("//"):
        content = f"// Eldar Intelligence Hub — Daily Data\n// Auto-updated: {date_str} IST\n// Generated by Sofia 🦞\n\n" + content

    return content


def fix_typescript_issues(content):
    """Fix common GPT-generated TypeScript issues."""
    
    # 1. Fix ALL known Hebrew abbreviations with internal quotes
    abbreviations = {
        'ת"א': 'תל אביב',
        'נאסד"ק': 'נאסדק',
        'מנכ"ל': 'מנהל כללי',
        'ד"ר': 'דוקטור',
        'סמנכ"ל': 'סמנהל כללי',
        'בע"מ': 'בעמ',
        'עו"ד': 'עורך דין',
        'רו"ח': 'רואה חשבון',
        'יו"ר': 'יושב ראש',
        'כנ"ל': 'כנל',
        'ארה"ב': 'ארהב',
        'או"ם': 'האומות המאוחדות',
    }
    for abbr, replacement in abbreviations.items():
        content = content.replace(abbr, replacement)
    
    # 2. Fix Hebrew geresh: ד' => ד׳ (inside strings)
    for letter in 'אבגדהוזחטיכלמנסעפצקרשת':
        content = content.replace(f"{letter}',", f'{letter}׳",')
        content = content.replace(f"{letter}' ", f"{letter}׳ ")
    
    # 3. Fix REPORT.breakingItems if they reference NEWS_ITEMS
    if 'export const NEWS_ITEMS' in content:
        before_news = content.split('export const NEWS_ITEMS')[0]
        if 'NEWS_ITEMS[' in before_news:
            report_match = re.search(r'export const REPORT = \{.*?\};', content, re.DOTALL)
            if report_match:
                old_report = report_match.group(0)
                if 'NEWS_ITEMS[' in old_report:
                    items = re.findall(r'NEWS_ITEMS\[(\d+)\]', old_report)
                    news_match = re.search(r'export const NEWS_ITEMS: NewsItem\[\] = \[(.*?)\];', content, re.DOTALL)
                    if news_match:
                        titles = re.findall(r'title:\s*"([^"]*)"', news_match.group(1))
                        categories = re.findall(r'category:\s*"([^"]*)"', news_match.group(1))
                        
                        emojis = {"כלכלה": "💰", "פוליטיקה": "🏙️", "טכנולוגיה": "💻",
                                  "ביטחון": "🛡️", "חברה": "👥", "תיירות": "✈️", "יין": "🍷"}
                        
                        breaking = []
                        for idx_str in items[:5]:
                            idx = int(idx_str)
                            if idx < len(titles) and idx < len(categories):
                                cat = categories[idx]
                                emoji = emojis.get(cat, "📌")
                                breaking.append(f'{emoji} {cat}: {titles[idx]}')
                        
                        breaking_str = ',\n    '.join(f'"{s}"' for s in breaking)
                        
                        exec_s = re.search(r'executiveSummary:\s*\n?\s*"((?:[^"\\]|\\.)*)"', old_report)
                        concl = re.search(r'conclusion:\s*\n?\s*"((?:[^"\\]|\\.)*)"', old_report)
                        watch = re.search(r'watchNext24h:\s*\n?\s*"((?:[^"\\]|\\.)*)"', old_report)
                        
                        new_report = f'''export const REPORT = {{
  date: NEWS_DATE,
  breakingItems: [
    {breaking_str}
  ],
  executiveSummary:
    "{exec_s.group(1) if exec_s else 'סיכום יומי'}",
  conclusion:
    "{concl.group(1) if concl else 'מסקנות'}",
  watchNext24h:
    "{watch.group(1) if watch else 'מה לעקוב'}",
}};'''
                        content = content.replace(old_report, new_report)
                        print("    ✅ Fixed REPORT.breakingItems")
    
    # 4. Ensure REPORT has date: NEWS_DATE
    if 'export const REPORT' in content and 'export const NEWS_ITEMS' in content:
        before_news = content.split('export const NEWS_ITEMS')[0]
        if 'date: NEWS_DATE' not in before_news:
            content = content.replace('export const REPORT = {', 'export const REPORT = {\n  date: NEWS_DATE,')
            print("    ✅ Added date: NEWS_DATE to REPORT")
    
    # 5. Fix unbalanced quotes line by line
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
        if count % 2 != 0:
            print(f"    ⚠️ Odd quotes on line {i+1}: {stripped[:60]}...")
            if count == 3:
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
                    print(f"    ✅ Fixed by escaping middle quote")
            elif count == 5:
                # Multiple internal quotes — try to escape all internal ones
                positions = []
                j = 0
                while j < len(stripped):
                    if stripped[j] == '\\' and j + 1 < len(stripped):
                        j += 2
                        continue
                    if stripped[j] == '"':
                        positions.append(j)
                    j += 1
                # Escape all except first and last
                if len(positions) >= 3:
                    for pos in reversed(positions[1:-1]):
                        stripped = stripped[:pos] + '\\' + stripped[pos:]
                    lines[i] = line[:len(line)-len(line.strip())] + stripped
                    print(f"    ✅ Fixed by escaping internal quotes")
    
    content = '\n'.join(lines)
    return content


def validate_data_ts(content):
    """Basic validation of generated data.ts content."""
    checks = {
        "interfaces": "export interface NewsItem" in content,
        "NEWS_DATE": "export const NEWS_DATE" in content,
        "LAST_UPDATED": "export const LAST_UPDATED" in content,
        "REPORT": "export const REPORT" in content,
        "NEWS_ITEMS": "export const NEWS_ITEMS" in content,
        "CONTENT_ITEMS": "export const CONTENT_ITEMS" in content,
        "TRENDS": "export const TRENDS" in content,
        "WINE_NEWS": "export const WINE_NEWS" in content,
        "TOURISM_NEWS": "export const TOURISM_NEWS" in content,
        "MARKET_DATA": "export const MARKET_DATA" in content,
        "INDUSTRY_NEWS": "export const INDUSTRY_NEWS" in content,
        "breakingItems_strings": 'NEWS_ITEMS[' not in content.split('export const NEWS_ITEMS')[0] if 'export const NEWS_ITEMS' in content else True,
        "date_NEWS_DATE": "date: NEWS_DATE" in content,
    }
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    print(f"  📋 Validation: {passed}/{total} checks passed")
    for name, ok in checks.items():
        status = "✅" if ok else "❌"
        print(f"    {status} {name}")
    
    return passed >= 11


def push_to_github(content, commit_message=None):
    """Push updated data.ts to GitHub via API."""
    if not commit_message:
        now = datetime.now(IST)
        commit_message = f"🦞 EIH Update — {now.strftime('%d/%m/%Y %H:%M')} IST"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    
    print("  📥 Getting current file SHA...")
    resp = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=30)
    
    if resp.status_code == 200:
        current_sha = resp.json()["sha"]
    elif resp.status_code == 404:
        current_sha = None
    else:
        print(f"  ❌ GitHub GET error: {resp.status_code}")
        return False
    
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": GITHUB_BRANCH,
    }
    if current_sha:
        payload["sha"] = current_sha
    
    print("  📤 Pushing to GitHub...")
    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    
    if resp.status_code in (200, 201):
        sha = resp.json().get("content", {}).get("sha", "?")
        print(f"  ✅ GitHub push successful! SHA: {sha[:12]}")
        return True
    else:
        print(f"  ❌ GitHub PUT error: {resp.status_code} {resp.text[:200]}")
        return False


def trigger_vercel_deploy():
    """Trigger a new Vercel deployment via API using the latest GitHub commit."""
    print("  🚀 Triggering Vercel deployment...")
    
    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # Method: Create deployment from GitHub source
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
        deploy_id = data.get("id", "?")
        deploy_url = data.get("url", "?")
        print(f"  ✅ Vercel deploy triggered! ID: {deploy_id}")
        print(f"  🔗 {deploy_url}")
        return True
    else:
        error = resp.json().get("error", {}).get("message", resp.text[:200])
        print(f"  ⚠️ Vercel API deploy failed: {error}")
        print("  Trying deploy hook fallback...")
        return trigger_vercel_deploy_hook()


def trigger_vercel_deploy_hook():
    """Fallback: use Vercel deploy hook if API deploy fails."""
    # We'll create a deploy hook via API first
    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # List existing deploy hooks
    resp = requests.get(
        f"https://api.vercel.com/v1/projects/{VERCEL_PROJECT_ID}/deploy-hooks?teamId={VERCEL_ORG_ID}",
        headers=headers, timeout=30
    )
    
    hook_url = None
    if resp.status_code == 200:
        hooks = resp.json().get("deployHooks", [])
        for hook in hooks:
            if hook.get("name") == "sofia-auto-update":
                hook_url = hook.get("url")
                break
    
    if not hook_url:
        # Create a new deploy hook
        resp = requests.post(
            f"https://api.vercel.com/v1/projects/{VERCEL_PROJECT_ID}/deploy-hooks?teamId={VERCEL_ORG_ID}",
            headers=headers,
            json={"name": "sofia-auto-update", "ref": "main"},
            timeout=30
        )
        if resp.status_code in (200, 201):
            hook_url = resp.json().get("url")
    
    if hook_url:
        resp = requests.post(hook_url, timeout=30)
        if resp.status_code in (200, 201):
            print(f"  ✅ Deploy hook triggered successfully!")
            return True
    
    print("  ❌ All deploy methods failed")
    return False


def verify_deployment():
    """Check if the site is accessible."""
    import time
    print("  ⏳ Waiting 30s for deployment to complete...")
    time.sleep(30)
    
    try:
        resp = requests.get(VERCEL_URL, timeout=30)
        if resp.status_code == 200:
            now = datetime.now(IST)
            expected_date = now.strftime("%d.%-m.%Y")
            if expected_date in resp.text:
                print(f"  ✅ Site is live with today's date ({expected_date})")
            else:
                print(f"  ⚠️ Site is live but may need a few more minutes to update")
            return True
        else:
            print(f"  ⚠️ Site returned status: {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Verification error: {e}")
        return False


# ============================================================
# MAIN
# ============================================================
def main():
    now = datetime.now(IST)
    print("=" * 60)
    print(f"🦞 EIH Web Update — {now.strftime('%d/%m/%Y %H:%M')} IST")
    print(f"   Running via GitHub Actions")
    print("=" * 60)
    
    # Validate secrets
    missing = []
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not GITHUB_TOKEN:
        missing.append("GH_PAT")
    if not VERCEL_TOKEN:
        missing.append("VERCEL_TOKEN")
    
    if missing:
        print(f"❌ Missing secrets: {', '.join(missing)}")
        return False
    
    # Step 1: Generate
    print("\n📰 Step 1: Generating fresh data.ts...")
    try:
        data_ts_content = generate_data_ts()
        print(f"  📄 Generated {len(data_ts_content)} characters")
    except Exception as e:
        print(f"  ❌ Generation failed: {e}")
        return False
    
    # Step 2: Fix
    print("\n🔧 Step 2: Fixing TypeScript issues...")
    data_ts_content = fix_typescript_issues(data_ts_content)
    
    # Step 3: Validate
    print("\n✅ Step 3: Validating...")
    if not validate_data_ts(data_ts_content):
        print("  ❌ Validation failed")
        return False
    
    # Step 4: Push to GitHub
    print("\n📤 Step 4: Pushing to GitHub...")
    if not push_to_github(data_ts_content):
        print("  ❌ Push failed")
        return False
    
    # Step 5: Trigger Vercel deploy
    print("\n🚀 Step 5: Triggering Vercel deploy...")
    trigger_vercel_deploy()
    
    # Step 6: Verify
    print("\n🌐 Step 6: Verifying...")
    verify_deployment()
    
    print("\n" + "=" * 60)
    print("✅ EIH Web Update complete!")
    print(f"🔗 {VERCEL_URL}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
