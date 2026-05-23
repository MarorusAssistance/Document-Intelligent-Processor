import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Document Processor",
  description: "Intelligent Document Processing for supply chain",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
