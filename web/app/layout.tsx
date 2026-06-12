import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TradeBuilt — AI Website Generator for Local Businesses",
  description:
    "Enter any local business and get a high-converting website with AI-generated copy, scored and ready to deploy — in seconds.",
  openGraph: {
    title: "TradeBuilt — AI Website Generator",
    description: "Generate a converting website for any local business in seconds.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} min-h-full flex flex-col antialiased`}>
        {children}
      </body>
    </html>
  );
}
