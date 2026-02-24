import type { Metadata } from "next";
import { Geist, Bodoni_Moda } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/navbar";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const bodoni = Bodoni_Moda({
  variable: "--font-bodoni",
  subsets: ["latin", "latin-ext"],
});

export const metadata: Metadata = {
  title: {
    default: "NovelVerse — Đọc truyện online",
    template: "%s | NovelVerse",
  },
  description:
    "Nền tảng đọc truyện chữ Trung Quốc và tiểu thuyết online hàng đầu Việt Nam.",
  keywords: [
    "đọc truyện",
    "truyện online",
    "tiểu thuyết",
    "truyện Trung Quốc",
    "NovelVerse",
  ],
  openGraph: {
    type: "website",
    locale: "vi_VN",
    siteName: "NovelVerse",
  },
  twitter: {
    card: "summary_large_image",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className={`${geistSans.variable} ${bodoni.variable} antialiased`}>
        <Navbar />
        <main>{children}</main>
        <Toaster />
      </body>
    </html>
  );
}
