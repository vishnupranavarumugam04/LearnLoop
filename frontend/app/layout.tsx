import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/auth-context";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LearnLoop 2.0",
  description: "AI Learning Companion",
};

import { ThemeProvider } from "@/context/theme-context";
import { NotificationProvider } from "@/context/notification-context";
import { StatsProvider } from "@/context/stats-context";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-background text-foreground antialiased`}>
        <AuthProvider>
          <NotificationProvider>
            <StatsProvider>
              <ThemeProvider>
                {children}
              </ThemeProvider>
            </StatsProvider>
          </NotificationProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
