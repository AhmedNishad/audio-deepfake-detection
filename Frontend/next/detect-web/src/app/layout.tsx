import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Detect Deepfakes",
  description: "Detect and tag audio deepfake recordings here",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Link className="text-blue-500 hover:underline" style={{position: 'absolute', top: 10, left: 10 }}
         href="/">Home</Link>
        {children}
      </body>
    </html>
  );
}
