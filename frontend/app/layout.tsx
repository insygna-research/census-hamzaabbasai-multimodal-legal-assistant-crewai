import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Multimodal Legal Assistant | Contract Risk Review",
  description: "Contract risk review with source evidence and human approval",
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
