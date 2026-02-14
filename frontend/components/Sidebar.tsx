"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useAuth } from "@/context/auth-context"
import { useStats } from "@/context/stats-context"
import {
    LayoutDashboard,
    BookOpen,
    User,
    MessageSquare,
    Network,
    Users,
    Settings,
    LogOut,
    Sparkles,
    Calendar // New
} from "lucide-react"
import { Button } from "@/components/ui/button"

const sidebarItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    { icon: MessageSquare, label: "My Buddy", href: "/buddy" },
    { icon: MessageSquare, label: "Chat", href: "/chat" },
    { icon: Calendar, label: "History", href: "/history" }, // New
    { icon: BookOpen, label: "Materials", href: "/materials" },
    { icon: Network, label: "Knowledge Graph", href: "/graph" },
    { icon: Users, label: "Study Rooms", href: "/rooms" },
    { icon: User, label: "Profile", href: "/profile" },
    { icon: Settings, label: "Settings", href: "/settings" },
]

const AVATAR_ICONS: Record<string, string> = {
    seedling: '🌱',
    sprout: '🌿',
    brain: '🧠',
    robot: '🤖',
    sparkles: '✨',
    rocket: '🚀',
    star: '⭐',
    ghost: '👻',
}

export function Sidebar() {
    const pathname = usePathname()
    const { user, logout } = useAuth()
    const { stats, levelTitle } = useStats()
    const level = stats.level

    return (
        <div className="flex h-screen w-64 flex-col border-r border-border bg-secondary text-foreground">
            <div className="flex h-16 items-center px-6 border-b border-border">
                <span className="mr-2 text-2xl">{AVATAR_ICONS[stats.buddyAvatar] || '🌱'}</span>
                <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600">
                    LearnLoop
                </span>
            </div>
            <div className="flex-1 overflow-y-auto py-4">
                <nav className="grid gap-1 px-2">
                    {sidebarItems.map((item, index) => (
                        <Link
                            key={index}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                                pathname === item.href ? "bg-primary text-primary-foreground shadow-md shadow-primary/20" : "text-muted-foreground"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            {item.label}
                        </Link>
                    ))}
                </nav>
            </div>
            <div className="p-4 border-t border-border">
                <div className="flex items-center gap-3 mb-4 px-2">
                    <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold uppercase">
                        {user?.name.charAt(0) || "U"}
                    </div>
                    <div className="flex flex-col">
                        <span className="text-sm font-medium truncate w-[140px]">{user?.name}</span>
                        <span className="text-xs text-muted-foreground">Level {level}</span>
                    </div>
                </div>
                <Button variant="ghost" className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10" onClick={logout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Log Out
                </Button>
            </div>
        </div>
    )
}
