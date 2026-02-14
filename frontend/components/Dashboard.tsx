"use client"

import * as React from "react"
import { KnowledgeGraph } from "./KnowledgeGraph"
import { BuddyAvatar } from "./BuddyAvatar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Trophy, Flame, Clock, BookOpen, Users } from "lucide-react"
import { useAuth } from "@/context/auth-context"
import { useStats } from "@/context/stats-context"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"

export function Dashboard() {
    const { user } = useAuth()
    const { stats: globalStats, refreshStats } = useStats()
    const router = useRouter()
    const [localStats, setLocalStats] = React.useState({
        topics_mastered: 0,
        study_time: "0h 0m",
        active_rooms: []
    })

    const fetchDashboardData = async () => {
        const username = user?.email || "default_user";
        try {
            const graphRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/graph/?username=${encodeURIComponent(username)}`)
            if (graphRes.ok) {
                const graphData = await graphRes.json()
                setLocalStats(prev => ({
                    ...prev,
                    topics_mastered: graphData.mastery_summary?.mastered || 0,
                }))
            }

            const roomsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/rooms/`)
            if (roomsRes.ok) {
                const roomsData = await roomsRes.json()
                setLocalStats(prev => ({
                    ...prev,
                    active_rooms: roomsData || []
                }))
            }
        } catch (e) {
            console.error("Failed to fetch dashboard data", e)
        }
    }

    React.useEffect(() => {
        fetchDashboardData()
    }, [user])

    return (
        <div className="min-h-screen bg-background p-6 space-y-8">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black tracking-tight">Welcome back, {user?.name}! 👋</h1>
                    <p className="text-muted-foreground mt-1 font-medium">Your buddy {globalStats.buddyName} is ready to learn something new today.</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 bg-card p-2 rounded-full border shadow-sm px-4">
                        <Flame className={globalStats.streak_days > 0 ? "text-orange-500 h-5 w-5 animate-pulse" : "text-muted-foreground h-5 w-5"} />
                        <span className="font-bold">{globalStats.streak_days} Day Streak</span>
                    </div>
                    <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-bold uppercase shadow-sm">
                        {user?.name?.charAt(0) || "U"}
                    </div>
                </div>
            </header>

            {/* Centered Buddy Avatar */}
            <div className="flex justify-center">
                <Card className="w-full max-w-2xl h-[700px] bg-card/50 backdrop-blur-sm border-2">
                    <CardContent className="h-full p-0">
                        <BuddyAvatar autoListen={true} showTranscript={false} />
                    </CardContent>
                </Card>
            </div>

            {/* Stats Grid Below Buddy */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Left Column: Stats and Knowledge Graph */}
                <div className="space-y-6">
                    {/* Stats Cards */}
                    <div className="grid grid-cols-2 gap-4">
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">Topics Mastered</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{localStats.topics_mastered}</div>
                                <p className="text-xs text-muted-foreground">Keep growing your brain!</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">Total XP</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{globalStats.total_xp}</div>
                                <p className="text-xs text-muted-foreground">Level {globalStats.level}</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Knowledge Graph Preview */}
                    <KnowledgeGraph />
                </div>

                {/* Right Column: Study Rooms */}
                <div className="space-y-6">
                    {/* Active Rooms */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Users className="h-5 w-5 text-purple-500" />
                                Study Rooms
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {localStats.active_rooms.length > 0 ? (
                                <div className="space-y-3">
                                    {localStats.active_rooms.map((room: any) => (
                                        <div key={room.id} className="flex items-center justify-between p-2 rounded-lg bg-secondary border hover:border-primary transition-colors cursor-pointer">
                                            <div>
                                                <div className="font-medium text-sm">{room.name}</div>
                                                <div className="text-xs text-muted-foreground">{room.subject} • {room.participants.length} online</div>
                                            </div>
                                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                                                <Clock className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    ))}
                                    <Button
                                        variant="link"
                                        className="text-indigo-400 h-auto p-0 text-xs w-full"
                                        onClick={() => router.push("/rooms")}
                                    >
                                        View All Rooms
                                    </Button>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground">
                                    <p className="text-sm">No active study rooms.</p>
                                    <Button
                                        variant="link"
                                        className="text-indigo-400 h-auto p-0 text-xs"
                                        onClick={() => router.push("/rooms")}
                                    >
                                        Join a Room
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

            </div>
        </div>
    )
}
