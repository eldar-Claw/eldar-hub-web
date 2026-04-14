"use client";

import { useState } from "react";

// Types
interface NewsItem {
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
}

interface Trend {
  title: string;
  description: string;
  direction: "up" | "down" | "stable";
}

// Sample Data
const REPORT = {
  date: new Date().toLocaleDateString("he-IL", { weekday: "long", year: "numeric", month: "long", day: "numeric" }),
  executiveSummary: "היום חלו התפתחויות משמעותיות בזירה הכלכלית והביטחונית. שוק ההון הישראלי רשם עליות חדות על רקע נתוני מאקרו חיוביים, בעוד שבזירה הביטחונית נמשכת פעילות צה\"ל בגזרת הצפון. בתחום הטכנולוגיה, חברות AI ישראליות דיווחו על גיוסי ענק. הממשלה אישרה רפורמת דיור חדשה ושביתת מורים צפויה מחר.",
  conclusion: "המצב הכלכלי מציג סימנים חיוביים עם צמיחה בסקטור הטכנולוגיה. יש להמשיך לעקוב אחר ההתפתחויות הביטחוניות ופעולות בנק ישראל. רפורמת הדיור עשויה לשנות את שוק הנדל\"ן בפריפריה.",
  watchNext24h: "פרסום נתוני אינפלציה חודשיים מחר ב-10:00 | ישיבת קבינט ביטחוני | פרסום דוחות רבעוניים של בנקים | כנס טכנולוגיה בתל אביב | הצבעה בכנסת על חוק הגיוס",
};

const NEWS_ITEMS: NewsItem[] = [
  { id: 1, type: "news", category: "כלכלה", title: "הבורסה בתל אביב רשמה עלייה של 2.3% — השיא מתחילת השנה", summary: "מדד ת\"א 35 עלה ב-2.3% היום, מונע על ידי מניות הטכנולוגיה והבנקאות. העליות הגיעו על רקע נתוני תעסוקה חיוביים ותחזית צמיחה מעודכנת של בנק ישראל.", whyItMatters: "מדובר בשיא של המדד מתחילת 2026, מה שמצביע על אמון גובר של המשקיעים בכלכלה הישראלית.", implications: "עלייה בתשואות קרנות הפנסיה, חיזוק השקל, ואפשרות להנפקות חדשות.", importance: 9, sourceUrl: "https://www.globes.co.il", sourceName: "גלובס" },
  { id: 2, type: "news", category: "צבא וביטחון", title: "צה\"ל הרחיב פעילות בגזרת הצפון — תרגיל רחב היקף", summary: "צה\"ל פתח בתרגיל צבאי רחב היקף בגזרת הצפון, הכולל כוחות יבשה, אוויר וים. התרגיל נמשך שלושה ימים ומדמה תרחישי לחימה מורכבים.", whyItMatters: "התרגיל נערך על רקע מתיחות מתמשכת בגבול הצפון ומעביר מסר הרתעתי.", implications: "חיזוק המוכנות המבצעית, הגברת ההרתעה, ואפשרות להסלמה מדודה.", importance: 8, sourceUrl: "https://www.ynet.co.il", sourceName: "Ynet" },
  { id: 3, type: "news", category: "טכנולוגיה", title: "סטארטאפ ישראלי בתחום ה-AI גייס $200 מיליון בסבב C", summary: "חברת NovaMind AI הישראלית גייסה $200M בהובלת Sequoia Capital. החברה מפתחת מודלי שפה מתקדמים לשוק הארגוני ומתכננת הרחבה משמעותית.", whyItMatters: "הגיוס מציב את ישראל כשחקנית מרכזית בזירת ה-AI העולמית.", implications: "גיוס עובדים נרחב, חיזוק האקוסיסטם הישראלי, ותחרות מול חברות אמריקאיות.", importance: 8, sourceUrl: "https://www.geektime.co.il", sourceName: "Geektime" },
  { id: 4, type: "news", category: "פוליטיקה", title: "הממשלה אישרה תוכנית רפורמה בדיור — 50,000 יחידות חדשות", summary: "הקבינט אישר תוכנית דיור חדשה הכוללת בניית 50,000 יחידות דיור בפריפריה וקיצור הליכי תכנון ל-18 חודשים.", whyItMatters: "מדובר בצעד משמעותי לטיפול במשבר הדיור שפוקד את ישראל כבר שנים.", implications: "ירידה צפויה במחירי הדירות בפריפריה, הגירה פנימית, ותנופת בנייה.", importance: 7, sourceUrl: "https://www.haaretz.co.il", sourceName: "הארץ" },
  { id: 5, type: "news", category: "חברה", title: "שביתה ארצית במערכת החינוך — מחר לא ילמדו", summary: "ארגוני המורים הכריזו על שביתה ארצית ביום רביעי בעקבות מחלוקת על תנאי השכר. כ-1.5 מיליון תלמידים לא ילמדו.", whyItMatters: "השביתה משפיעה על מיליוני משפחות ומעלה לסדר היום את סוגיית תנאי המורים.", implications: "לחץ ציבורי על הממשלה, פגיעה כלכלית ביום עבודה, ואפשרות להסכם חדש.", importance: 7, sourceUrl: "https://www.kan.org.il", sourceName: "כאן חדשות" },
  { id: 6, type: "news", category: "כלכלה", title: "בנק ישראל: האינפלציה ירדה ל-2.1% — הנמוכה מזה שנתיים", summary: "הלמ\"ס פרסמה שמדד המחירים לצרכן ירד ב-0.2% בחודש האחרון, והאינפלציה השנתית ירדה ל-2.1%.", whyItMatters: "ירידת האינפלציה פותחת פתח להורדת ריבית ומקלה על עלות המחיה.", implications: "הורדת ריבית צפויה, הוזלת משכנתאות, וחיזוק הצריכה הפרטית.", importance: 8, sourceUrl: "https://www.calcalist.co.il", sourceName: "כלכליסט" },
  { id: 7, type: "news", category: "טכנולוגיה", title: "Intel תשקיע $10 מיליארד נוספים במפעל בישראל", summary: "Intel הודיעה על הרחבת ההשקעה במפעל קריית גת ב-$10B, מה שיהפוך אותו לאחד המתקדמים בעולם.", whyItMatters: "ההשקעה מחזקת את מעמד ישראל כמרכז ייצור שבבים עולמי.", implications: "אלפי משרות חדשות, חיזוק הפריפריה, והגברת ייצוא הטכנולוגיה.", importance: 9, sourceUrl: "https://www.pc.co.il", sourceName: "אנשים ומחשבים" },
  { id: 8, type: "news", category: "צבא וביטחון", title: "מערכת הגנה אווירית חדשה עברה ניסוי מוצלח", summary: "משרד הביטחון ורפאל ביצעו ניסוי מוצלח במערכת \"מגן שמיים\" ליירוט טילים בליסטיים.", whyItMatters: "המערכת משלימה את כיפת הברזל וחץ ומספקת שכבת הגנה נוספת.", implications: "חיזוק ההגנה האסטרטגית, פוטנציאל ייצוא ביטחוני, ושיפור ההרתעה.", importance: 7, sourceUrl: "https://www.ynet.co.il", sourceName: "Ynet" },
  { id: 9, type: "news", category: "פוליטיקה", title: "ישראל וסעודיה: סבב שיחות חדש בוושינגטון", summary: "נציגים ישראלים וסעודים נפגשו בוושינגטון לסבב שיחות נוסף בנושא נורמליזציה.", whyItMatters: "הסכם עם סעודיה יהיה פריצת דרך גיאופוליטית משמעותית.", implications: "שינוי מפת הבריתות האזורית, הזדמנויות כלכליות ותיירותיות.", importance: 8, sourceUrl: "https://www.haaretz.co.il", sourceName: "הארץ" },
  { id: 10, type: "news", category: "חברה", title: "מחקר: 40% מהישראלים מתכננים לעבוד מהבית באופן קבוע", summary: "סקר חדש מצא ש-40% מהעובדים מעדיפים עבודה היברידית קבועה. המגמה חזקה בהייטק ובשירותים.", whyItMatters: "שינוי דפוסי העבודה משפיע על תחבורה, נדל\"ן מסחרי ואיכות חיים.", implications: "ירידת ביקוש למשרדים, שיפור תחבורתי, ושינוי מפת המגורים.", importance: 6, sourceUrl: "https://www.walla.co.il", sourceName: "וואלה" },
];

const CONTENT_ITEMS: NewsItem[] = [
  { id: 11, type: "content", category: "טכנולוגיה", title: "מדריך: כך תבנו אסטרטגיית AI לארגון שלכם ב-2026", summary: "מאמר מקיף על הטמעת AI בארגונים, כולל ROI, כוח אדם ותשתיות.", whyItMatters: "AI הפך לכלי קריטי לתחרותיות עסקית.", implications: "הגברת פרודוקטיביות, חיסכון בעלויות.", importance: 7, sourceUrl: "https://www.geektime.co.il", sourceName: "Geektime", authorName: "יוסי כהן" },
  { id: 12, type: "content", category: "כלכלה", title: "ניתוח: למה הפד ירד מהריבית ומה זה אומר לישראל", summary: "ניתוח מעמיק של השפעת הורדת הריבית האמריקאית על הכלכלה הישראלית.", whyItMatters: "מדיניות הפד משפיעה ישירות על שוקי ההון.", implications: "ירידת תשואות אג\"ח, חיזוק שוק המניות.", importance: 7, sourceUrl: "https://www.calcalist.co.il", sourceName: "כלכליסט", authorName: "דנה אשכנזי" },
  { id: 13, type: "content", category: "טכנולוגיה", title: "סייבר 2026: האיומים החדשים שכל CISO צריך להכיר", summary: "סקירה של וקטורי תקיפה חדשים כולל AI-powered attacks ו-deepfake phishing.", whyItMatters: "איומי הסייבר מתפתחים מהר יותר מההגנות.", implications: "הגדלת תקציבי אבטחה, גיוס מומחים.", importance: 6, sourceUrl: "https://www.pc.co.il", sourceName: "אנשים ומחשבים", authorName: "מיכל לוי" },
  { id: 14, type: "content", category: "כלכלה", title: "FinTech ישראלי: 5 חברות שישנו את עולם התשלומים", summary: "סקירה של חמש חברות פינטק ישראליות שמפתחות פתרונות תשלום חדשניים.", whyItMatters: "ישראל מובילה בתחום הפינטק.", implications: "השקעות חדשות, שינוי דפוסי תשלום.", importance: 5, sourceUrl: "https://www.globes.co.il", sourceName: "גלובס", authorName: "שרון אביב" },
  { id: 15, type: "content", category: "פוליטיקה", title: "מבט מלמעלה: השפעת הבחירות באירופה על ישראל", summary: "ניתוח השלכות הבחירות באירופה על יחסי ישראל-אירופה.", whyItMatters: "אירופה שותפת סחר מרכזית של ישראל.", implications: "שינוי מדיניות סחר, השפעה על תהליכים מדיניים.", importance: 5, sourceUrl: "https://www.haaretz.co.il", sourceName: "הארץ", authorName: "עמית רז" },
];

const TRENDS: Trend[] = [
  { title: "עליית מניות הטכנולוגיה", description: "מגמת עלייה חדה במניות AI וסייבר ישראליות, עם גיוסים של מעל $500M ברבעון", direction: "up" },
  { title: "ירידה בריבית הצפויה", description: "בנק ישראל צפוי להוריד ריבית ברבעון הבא על רקע ירידת האינפלציה", direction: "down" },
  { title: "יציבות גיאופוליטית שברירית", description: "המצב הביטחוני בצפון נשאר מורכב אך מבוקר, עם מגעים דיפלומטיים פעילים", direction: "stable" },
];

// Category colors
const catColors: Record<string, string> = {
  "כלכלה": "bg-blue-600",
  "פוליטיקה": "bg-purple-600",
  "חברה": "bg-yellow-600",
  "צבא וביטחון": "bg-red-600",
  "טכנולוגיה": "bg-green-600",
};

const catBgColors: Record<string, string> = {
  "כלכלה": "border-blue-200 bg-blue-50",
  "פוליטיקה": "border-purple-200 bg-purple-50",
  "חברה": "border-yellow-200 bg-yellow-50",
  "צבא וביטחון": "border-red-200 bg-red-50",
  "טכנולוגיה": "border-green-200 bg-green-50",
};

function importanceColor(n: number) {
  if (n >= 8) return "bg-red-500";
  if (n >= 5) return "bg-yellow-500";
  return "bg-green-500";
}

function trendIcon(d: string) {
  if (d === "up") return "📈";
  if (d === "down") return "📉";
  return "➡️";
}

function trendColor(d: string) {
  if (d === "up") return "text-green-600";
  if (d === "down") return "text-red-600";
  return "text-blue-600";
}

// Components
function NewsCard({ item }: { item: NewsItem }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`border rounded-xl p-4 mb-3 transition-all hover:shadow-md cursor-pointer ${catBgColors[item.category] || "bg-white border-gray-200"}`} onClick={() => setOpen(!open)}>
      <div className="flex items-center justify-between mb-2">
        <span className={`${catColors[item.category] || "bg-gray-500"} text-white text-[11px] font-bold px-3 py-0.5 rounded-full`}>{item.category}</span>
        <span className={`${importanceColor(item.importance)} text-white text-[11px] font-bold px-2 py-0.5 rounded-lg`}>{item.importance}/10</span>
      </div>
      <h3 className="text-[15px] font-bold text-gray-900 mb-2 leading-snug">
        <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="hover:text-blue-700" onClick={e => e.stopPropagation()}>{item.title}</a>
      </h3>
      <p className="text-[13px] text-gray-600 leading-relaxed mb-2">{item.summary}</p>
      {open && (
        <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
          <p className="text-[13px] text-blue-700 font-semibold">💡 למה זה חשוב: <span className="font-normal text-gray-700">{item.whyItMatters}</span></p>
          <p className="text-[13px] text-gray-500">📊 השלכות: {item.implications}</p>
        </div>
      )}
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-200/60">
        {item.authorName && <span className="text-[11px] text-gray-400">✍️ {item.authorName}</span>}
        <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-[12px] text-blue-600 font-semibold hover:underline" onClick={e => e.stopPropagation()}>
          קרא עוד ← {item.sourceName}
        </a>
      </div>
    </div>
  );
}

// Tabs
type Tab = "dashboard" | "history" | "sources" | "settings";

export default function Home() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [filter, setFilter] = useState<string>("all");

  const categories = ["all", "כלכלה", "פוליטיקה", "חברה", "צבא וביטחון", "טכנולוגיה"];
  const filteredNews = filter === "all" ? NEWS_ITEMS : NEWS_ITEMS.filter(i => i.category === filter);
  const filteredContent = filter === "all" ? CONTENT_ITEMS : CONTENT_ITEMS.filter(i => i.category === filter);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-l from-[#1a365d] to-[#2b6cb0] text-white">
        <div className="max-w-3xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-extrabold">🧠 Eldar Intelligence Hub</h1>
          <p className="text-white/80 text-sm mt-1">דוח מודיעין יומי — חדשות ותוכן מקצועי</p>
        </div>
      </header>

      {/* Breaking Bar */}
      <div className="bg-red-600 text-white">
        <div className="max-w-3xl mx-auto px-4 py-2">
          <span className="text-[13px] font-bold">⚡ מהיום: הבורסה בשיא שנתי | צה&quot;ל בתרגיל בצפון | Intel — $10B לישראל</span>
        </div>
      </div>

      {/* Nav Tabs */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 flex gap-1">
          {[
            { id: "dashboard" as Tab, label: "📊 דשבורד", },
            { id: "history" as Tab, label: "📅 היסטוריה" },
            { id: "sources" as Tab, label: "📡 מקורות" },
            { id: "settings" as Tab, label: "⚙️ הגדרות" },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${tab === t.id ? "border-blue-600 text-blue-700" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-6">

        {tab === "dashboard" && (
          <>
            {/* Executive Summary */}
            <div className="bg-white rounded-xl p-5 mb-6 shadow-sm border border-gray-100">
              <h2 className="text-lg font-bold text-[#1a365d] mb-3 border-r-4 border-blue-600 pr-3">תקציר מנהלים</h2>
              <p className="text-[14px] text-gray-700 leading-7">{REPORT.executiveSummary}</p>
              <p className="text-[12px] text-gray-400 mt-3">{REPORT.date}</p>
            </div>

            {/* Category Filter */}
            <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
              {categories.map(c => (
                <button key={c} onClick={() => setFilter(c)}
                  className={`whitespace-nowrap px-3 py-1.5 rounded-full text-[12px] font-semibold transition-colors ${filter === c ? "bg-[#1a365d] text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-100"}`}>
                  {c === "all" ? "הכל" : c}
                </button>
              ))}
            </div>

            {/* News */}
            <div className="mb-6">
              <h2 className="text-lg font-bold text-[#1a365d] mb-4 flex items-center gap-2">
                📰 חדשות מרכזיות
                <span className="bg-blue-100 text-blue-700 text-[11px] font-bold px-2 py-0.5 rounded-full">{filteredNews.length}</span>
              </h2>
              {filteredNews.map(item => <NewsCard key={item.id} item={item} />)}
            </div>

            {/* Content */}
            <div className="mb-6">
              <h2 className="text-lg font-bold text-[#1a365d] mb-4 flex items-center gap-2">
                📋 תוכן מקצועי
                <span className="bg-blue-100 text-blue-700 text-[11px] font-bold px-2 py-0.5 rounded-full">{filteredContent.length}</span>
              </h2>
              {filteredContent.map(item => <NewsCard key={item.id} item={item} />)}
            </div>

            {/* Trends */}
            <div className="mb-6">
              <h2 className="text-lg font-bold text-[#1a365d] mb-4">📈 מגמות מרכזיות</h2>
              <div className="grid gap-3">
                {TRENDS.map((t, i) => (
                  <div key={i} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{trendIcon(t.direction)}</span>
                      <h3 className={`font-bold text-[15px] ${trendColor(t.direction)}`}>{t.title}</h3>
                    </div>
                    <p className="text-[13px] text-gray-600 leading-relaxed">{t.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Conclusion */}
            <div className="bg-green-50 border border-green-200 rounded-xl p-5 mb-4">
              <h2 className="text-lg font-bold text-[#1a365d] mb-3">✅ סיכום ניהולי</h2>
              <p className="text-[14px] text-gray-700 leading-7">{REPORT.conclusion}</p>
            </div>

            {/* Watch Next */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 mb-6">
              <h2 className="text-lg font-bold text-[#1a365d] mb-3">👁️ מה לעקוב ב-24 שעות</h2>
              <p className="text-[14px] text-blue-900 leading-7">{REPORT.watchNext24h}</p>
            </div>
          </>
        )}

        {tab === "history" && (
          <div className="space-y-3">
            <h2 className="text-lg font-bold text-[#1a365d] mb-4">📅 דוחות קודמים</h2>
            {[0, 1, 2, 3, 4].map(i => {
              const d = new Date(Date.now() - i * 86400000);
              return (
                <div key={i} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-blue-700">📅 {d.toLocaleDateString("he-IL", { weekday: "long", day: "numeric", month: "long" })}</span>
                    <span className="text-[11px] text-gray-400">15 פריטים</span>
                  </div>
                  <p className="text-[13px] text-gray-600 line-clamp-2">תקציר מנהלים ליום {d.toLocaleDateString("he-IL")} — התפתחויות בכלכלה, ביטחון וטכנולוגיה...</p>
                </div>
              );
            })}
          </div>
        )}

        {tab === "sources" && (
          <div className="space-y-3">
            <h2 className="text-lg font-bold text-[#1a365d] mb-4">📡 ניהול מקורות</h2>
            {[
              { name: "Ynet", cat: "חדשות", status: "active" },
              { name: "הארץ", cat: "חדשות", status: "active" },
              { name: "כלכליסט", cat: "כלכלה", status: "active" },
              { name: "גלובס", cat: "כלכלה", status: "error" },
              { name: "Geektime", cat: "טכנולוגיה", status: "active" },
              { name: "אנשים ומחשבים", cat: "טכנולוגיה", status: "active" },
              { name: "כאן חדשות", cat: "חדשות", status: "disabled" },
              { name: "TechCrunch", cat: "טכנולוגיה", status: "active" },
              { name: "Reuters", cat: "חדשות", status: "active" },
              { name: "BBC News", cat: "חדשות", status: "active" },
              { name: "וואלה", cat: "חדשות", status: "active" },
            ].map((s, i) => (
              <div key={i} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${s.status === "active" ? "bg-green-500" : s.status === "error" ? "bg-red-500" : "bg-gray-300"}`} />
                  <div>
                    <span className="font-semibold text-sm text-gray-900">{s.name}</span>
                    <span className="text-[11px] text-gray-400 mr-2">· {s.cat}</span>
                  </div>
                </div>
                <div className={`w-10 h-5 rounded-full relative cursor-pointer transition-colors ${s.status !== "disabled" ? "bg-blue-600" : "bg-gray-300"}`}>
                  <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-all ${s.status !== "disabled" ? "right-0.5" : "left-0.5"}`} />
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "settings" && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-[#1a365d] mb-4">⚙️ הגדרות</h2>
            {[
              { label: "📧 כתובת מייל", value: "eldar@el-dar.co.il", type: "email" },
              { label: "⏰ שעת שליחת דוח", value: "07:00", type: "time" },
              { label: "🔑 OpenAI API Key", value: "sk-...****", type: "password" },
              { label: "🖥️ כתובת Backend", value: "http://localhost:3001", type: "url" },
            ].map((s, i) => (
              <div key={i} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
                <label className="text-sm font-semibold text-gray-700 mb-2 block">{s.label}</label>
                <input type={s.type} defaultValue={s.value} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" dir="ltr" />
              </div>
            ))}
            <button className="w-full bg-[#2b6cb0] text-white py-3 rounded-xl font-bold text-sm hover:bg-[#1a365d] transition-colors">
              💾 שמור הגדרות
            </button>
            <div className="text-center mt-6 text-gray-400 text-[12px]">
              Eldar Intelligence Hub v1.0.0 MVP<br/>נוצר על ידי Shofia 🦞
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="bg-[#1a365d] text-white/60 text-center py-4 text-[11px]">
        נוצר על ידי Shofia 🦞 | Eldar Intelligence Hub | {REPORT.date}
      </footer>
    </div>
  );
}
