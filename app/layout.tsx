import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Eldar Intelligence Hub",
  description: "דוח מודיעין יומי - חדשות ותוכן מקצועי",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="he" dir="rtl">
      <body className="bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
