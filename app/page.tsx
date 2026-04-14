"use client";

import { useState } from "react";
import { REPORT, NEWS_ITEMS, CONTENT_ITEMS, TRENDS, TOURISM_NEWS, WINE_NEWS } from "./data";
import type { NewsItem } from "./data";

// Category colors
const catColors: Record<string, string> = {
  "כלכלה": "bg-blue-600",
  "פוליטיקה": "bg-purple-600",
  "חברה": "bg-yellow-600",
  "צבא וביטחון": "bg-red-600",
  "טכנולוגיה": "bg-green-600",
  "תיירות": "bg-amber-600",
  "רשת חברתית": "bg-sky-500",
  "בידור": "bg-pink-500",
  "אירועים": "bg-indigo-500",
  "יין": "bg-rose-700",
};

const catBgColors: Record<string, string> = {
  "כלכלה": "border-blue-200 bg-blue-50",
  "פוליטיקה": "border-purple-200 bg-purple-50",
  "חברה": "border-yellow-200 bg-yellow-50",
  "צבא וביטחון": "border-red-200 bg-red-50",
  "טכנולוגיה": "border-green-200 bg-green-50",
  "תיירות": "border-amber-200 bg-amber-50",
  "רשת חברתית": "border-sky-200 bg-sky-50",
  "בידור": "border-pink-200 bg-pink-50",
  "אירועים": "border-indigo-200 bg-indigo-50",
  "יין": "border-rose-200 bg-rose-50",
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
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());

  const toggleFilter = (cat: string) => {
    setActiveFilters(prev => {
      const next = new Set(prev);
      if (cat === "all") return new Set(); // "הכל" clears all filters
      if (next.has(cat)) { next.delete(cat); } else { next.add(cat); }
      return next;
    });
  };
  const isAllSelected = activeFilters.size === 0;

  const categories = ["all", "כלכלה", "פוליטיקה", "חברה", "צבא וביטחון", "טכנולוגיה", "תיירות", "רשת חברתית", "אירועים", "בידור", "יין"];
  const socialItems = [...NEWS_ITEMS, ...CONTENT_ITEMS].filter(i => i.sourceName === "LinkedIn" || i.sourceName === "Facebook" || i.sourceName === "X" || i.sourceName === "Twitter");
  const entertainmentItems = [...NEWS_ITEMS, ...CONTENT_ITEMS].filter(i => i.category === "בידור" || i.sourceName === "Netflix" || i.sourceName === "Apple TV+");
  const eventsItems = [...NEWS_ITEMS, ...CONTENT_ITEMS].filter(i => i.category === "אירועים");
  const wineItems = [...NEWS_ITEMS, ...CONTENT_ITEMS, ...(WINE_NEWS || [])].filter(i => i.category === "יין");
  const allItems = [...NEWS_ITEMS, ...(TOURISM_NEWS || []), ...socialItems, ...entertainmentItems, ...eventsItems, ...wineItems];
  const uniqueAll = allItems.filter((item, idx, self) => self.findIndex(i => i.id === item.id) === idx);

  const getItemsForCategory = (cat: string): NewsItem[] => {
    if (cat === "תיירות") return TOURISM_NEWS || [];
    if (cat === "רשת חברתית") return socialItems;
    if (cat === "אירועים") return eventsItems;
    if (cat === "בידור") return entertainmentItems;
    if (cat === "יין") return wineItems;
    return [...NEWS_ITEMS, ...CONTENT_ITEMS].filter(i => i.category === cat);
  };

  const filteredItems = (() => {
    if (isAllSelected) return uniqueAll;
    const combined: NewsItem[] = [];
    activeFilters.forEach(cat => { combined.push(...getItemsForCategory(cat)); });
    return combined.filter((item, idx, self) => self.findIndex(i => i.id === item.id) === idx);
  })();
  // Keep filteredNews and filteredContent for the rendering below
  const filteredNews = filteredItems;
  const filteredContent: NewsItem[] = [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-l from-[#1a365d] to-[#2b6cb0] text-white">
        <div className="max-w-3xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-extrabold">🧠 Eldar Intelligence Hub</h1>
              <p className="text-white/80 text-sm mt-1">דוח מודיעין יומי — חדשות ותוכן מקצועי</p>
            </div>
            <div className="text-left">
              <p className="text-white/60 text-[10px]">עדכון אחרון</p>
              <p className="text-white font-bold text-sm">{new Date().toLocaleTimeString("he-IL", { hour: "2-digit", minute: "2-digit" })}</p>
              <p className="text-white/50 text-[10px]">עדכון הבא: {(() => { const now = new Date(); const times = [8.5,13,17,19,21]; const h = now.getHours() + now.getMinutes()/60; const next = times.find(t => t > h); if (!next) return "08:30"; const hr = Math.floor(next); const mn = (next - hr) * 60; return `${String(hr).padStart(2,"0")}:${String(mn).padStart(2,"0")}`; })()}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Breaking Bar */}
      <div className="bg-red-600 text-white">
        <div className="max-w-3xl mx-auto px-4 py-2">
          <span className="text-[13px] font-bold">⚡ מהיום: מלחמת איראן עלתה 35 מיליארד ₪ | Wiz — אקזיט $32B ל-Google | 108 הרחבות Chrome זדוניות | בן-גוריון נפתח — מחירים בשמיים</span>
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
            <div className="flex flex-wrap gap-2 mb-4">
              {categories.map(c => {
                const isActive = c === "all" ? isAllSelected : activeFilters.has(c);
                return (
                  <button key={c} onClick={() => toggleFilter(c)}
                    className={`px-3 py-1.5 rounded-full text-[12px] font-semibold transition-colors ${isActive ? "bg-[#1a365d] text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-100"}`}>
                    {c === "all" ? "הכל" : c}
                  </button>
                );
              })}
            </div>

            {/* All Items - single flat list */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-[#1a365d] flex items-center gap-2">
                  {filter === "all" ? "📊 כל התוכן" : filter}
                  <span className="bg-blue-100 text-blue-700 text-[11px] font-bold px-2 py-0.5 rounded-full">{filteredNews.length + filteredContent.length}</span>
                </h2>
              </div>
              {[...filteredNews, ...filteredContent.filter(i => !filteredNews.find(n => n.id === i.id))].map(item => <NewsCard key={item.id} item={item} />)}
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
