import type { Metadata } from "next";
import AppShell from "./AppShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "GAIS",
  description: "Adaptive learning dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
