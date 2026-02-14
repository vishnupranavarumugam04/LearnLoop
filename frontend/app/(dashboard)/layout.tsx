"use client"

import { Sidebar } from "@/components/Sidebar";
import { NotificationBar } from "@/components/NotificationBar";
import { useAuth } from "@/context/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, isLoading } = useAuth()
    const router = useRouter()

    useEffect(() => {
        if (!isLoading && !user) {
            router.push("/login")
        }
    }, [user, isLoading, router])

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center bg-background dark:bg-slate-950 text-foreground dark:text-white">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
            </div>
        )
    }

    if (!user) return null

    return (
        <div className="flex min-h-screen bg-background">
            {/* Left Sidebar */}
            <aside className="hidden lg:block fixed left-0 top-0 bottom-0 z-50">
                <Sidebar />
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 lg:pl-64 flex flex-col">
                {/* Top Notification Bar */}
                <NotificationBar />

                {/* Page Content */}
                <main className="flex-1 pt-16 p-4 md:p-6 lg:p-8">
                    {children}
                </main>
            </div>
        </div>
    );
}
