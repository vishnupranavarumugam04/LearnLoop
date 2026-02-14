"use client"

import * as React from "react"
import { BuddyChat } from "@/components/BuddyChat"
import { useStats } from "@/context/stats-context"

export default function ChatPage() {
    const { refreshStats } = useStats()

    const handleXPUpdate = () => {
        refreshStats()
    }

    return (
        <div className="min-h-screen bg-background p-6">
            <div className="max-w-7xl mx-auto">
                <header className="mb-6">
                    <h1 className="text-3xl font-black tracking-tight">Chat with Your Buddy 💬</h1>
                    <p className="text-muted-foreground mt-1 font-medium">
                        Learn something new and earn XP through conversation!
                    </p>
                </header>
                
                <BuddyChat onXPUpdate={handleXPUpdate} />
            </div>
        </div>
    )
}
