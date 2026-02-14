"use client"

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useRef } from "react"
import { useAuth } from "./auth-context"
import { useNotifications } from "./notification-context"

interface Stats {
    level: number
    total_xp: number
    streak_days: number
    buddyName: string
    buddyAvatar: string
    lastStudyDate: string | null
}

interface StatsContextType {
    stats: Stats
    levelTitle: string
    refreshStats: () => Promise<void>
}

const StatsContext = createContext<StatsContextType | undefined>(undefined)

const getLevelTitle = (lvl: number) => {
    if (lvl < 4) return "Seedling"
    if (lvl < 8) return "Sprout"
    if (lvl < 13) return "Teenager"
    if (lvl < 17) return "Expert"
    return "Master"
}

export function StatsProvider({ children }: { children: ReactNode }) {
    const { user } = useAuth()
    const { addNotification } = useNotifications()
    const [stats, setStats] = useState<Stats>({
        level: 1,
        total_xp: 0,
        streak_days: 0,
        buddyName: "Buddy",
        buddyAvatar: "seedling",
        lastStudyDate: null
    })
    const lastStatsRef = useRef<Stats | null>(null)
    const isFirstLoad = useRef(true)

    const fetchStats = useCallback(async () => {
        if (!user?.email) return

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/profile/${encodeURIComponent(user.email)}`)
            if (res.ok) {
                const data = await res.json()
                const newStats: Stats = {
                    level: data.level,
                    total_xp: data.total_xp,
                    streak_days: data.streak_days,
                    buddyName: data.buddy_name || "Buddy",
                    buddyAvatar: data.buddy_avatar || "seedling",
                    lastStudyDate: data.last_study_date
                }

                if (!isFirstLoad.current && lastStatsRef.current) {
                    const prev = lastStatsRef.current

                    // 1. XP Rise
                    if (newStats.total_xp > prev.total_xp) {
                        addNotification({
                            title: "XP Gained! ✨",
                            message: `You earned ${newStats.total_xp - prev.total_xp} XP!`,
                            type: 'success'
                        })
                    }

                    // 2. Level Rise
                    if (newStats.level > prev.level) {
                        addNotification({
                            title: "Level Up! 🏆",
                            message: `Congratulations! You've reached Level ${newStats.level}!`,
                            type: 'success'
                        })
                    }

                    // 3. Evolution Path Rise
                    const oldTitle = getLevelTitle(prev.level)
                    const newTitle = getLevelTitle(newStats.level)
                    if (oldTitle !== newTitle && newStats.level > prev.level) {
                        addNotification({
                            title: "Evolution Path! 🌱",
                            message: `Your Buddy has evolved into a ${newTitle}!`,
                            type: 'success'
                        })
                    }

                    // 4. Streak Rise
                    if (newStats.streak_days > prev.streak_days) {
                        addNotification({
                            title: "Streak Rise! 🔥",
                            message: `Your learning streak is now ${newStats.streak_days} days!`,
                            type: 'success'
                        })
                    }
                }

                lastStatsRef.current = newStats
                setStats(newStats)
                isFirstLoad.current = false
            }
        } catch (e) {
            console.error("Failed to fetch global stats", e)
        }
    }, [user?.email, addNotification])

    useEffect(() => {
        fetchStats()
        // Poll every 30 seconds for background updates
        const interval = setInterval(fetchStats, 30000)
        return () => clearInterval(interval)
    }, [fetchStats])

    // Study Reminder Logic
    const hasRemindedRef = useRef(false)
    useEffect(() => {
        if (!stats.lastStudyDate || hasRemindedRef.current) return

        const lastStudy = new Date(stats.lastStudyDate).getTime()
        const now = Date.now()
        const hoursSinceStudy = (now - lastStudy) / (1000 * 60 * 60)

        // Threshold: 24 hours
        if (hoursSinceStudy > 24) {
            addNotification({
                title: `${stats.buddyName} misses you! 🥺`,
                message: `It's been a while since your last session. Ready to study something new?`,
                type: 'warning'
            })
            hasRemindedRef.current = true
        }
    }, [stats.lastStudyDate, stats.buddyName, addNotification])

    return (
        <StatsContext.Provider value={{
            stats,
            levelTitle: getLevelTitle(stats.level),
            refreshStats: fetchStats
        }}>
            {children}
        </StatsContext.Provider>
    )
}

export const useStats = () => {
    const context = useContext(StatsContext)
    if (!context) {
        throw new Error("useStats must be used within a StatsProvider")
    }
    return context
}
