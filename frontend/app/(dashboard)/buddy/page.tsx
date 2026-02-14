"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Sparkles, Brain, GraduationCap, Zap, ChevronRight, MessageSquare, Edit2, History } from "lucide-react"
import { useAuth } from "@/context/auth-context"
import { useStats } from "@/context/stats-context"
import { useRouter } from "next/navigation"
import { BuddyCustomizationModal } from "@/components/BuddyCustomizationModal"

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

// Brain Growing Indicator Component
function BrainGrowingIndicator() {
    const { user } = useAuth()
    const [materials, setMaterials] = React.useState<any[]>([])
    const [loading, setLoading] = React.useState(true)

    React.useEffect(() => {
        const fetchMaterials = async () => {
            if (!user) return
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/material/?user_id=${encodeURIComponent(user.email)}`)
                if (res.ok) {
                    const data = await res.json()
                    setMaterials(data)
                }
            } catch (e) {
                console.error("Failed to fetch materials for brain growing", e)
            } finally {
                setLoading(false)
            }
        }
        fetchMaterials()
    }, [user])

    const getStageProgress = (stage: string) => {
        // Map learning_stage to progress percentage - realistic values based on actual learning
        const stageMap: Record<string, number> = {
            'uploaded': 0,        // Just uploaded, no learning yet
            'buddy_taught': 33,   // Buddy explained it to you
            'user_taught': 66,    // You explained it back to buddy
            'mastered': 100,      // Fully mastered
        }
        return stageMap[stage] || 0
    }

    // Calculate total brain growth (average of all materials)
    const totalProgress = materials.length > 0
        ? materials.reduce((sum, m) => sum + getStageProgress(m.learning_stage || 'uploaded'), 0) / materials.length
        : 0

    if (loading) {
        return (
            <div className="mt-4 flex items-center gap-3">
                <div className="relative">
                    <Brain className="h-6 w-6 text-purple-200 animate-pulse" />
                </div>
                <div>
                    <span className="text-xs text-purple-100 font-bold uppercase tracking-wider">Brain Growing</span>
                    <p className="text-[10px] text-purple-200 opacity-70">Analyzing your learning...</p>
                </div>
            </div>
        )
    }

    if (materials.length === 0) {
        return (
            <div className="mt-4 flex items-center gap-3">
                <div className="relative">
                    <Brain className="h-6 w-6 text-purple-200 opacity-40" />
                </div>
                <div>
                    <span className="text-xs text-purple-100 font-bold uppercase tracking-wider">Brain Growing</span>
                    <p className="text-[10px] text-purple-200 opacity-70">Upload materials to start growing!</p>
                </div>
            </div>
        )
    }

    return (
        <div className="mt-4">
            <div className="flex items-center gap-3 mb-3">
                <div className="relative">
                    {/* Animated Brain Icon with pulsing growth effect */}
                    <div className="absolute inset-0 bg-emerald-400 rounded-full blur-md opacity-30 animate-pulse" style={{ animationDuration: '2s' }} />
                    <Brain className={`h-6 w-6 relative z-10 transition-all duration-500 ${totalProgress > 75 ? 'text-emerald-300' :
                        totalProgress > 50 ? 'text-emerald-400' :
                            totalProgress > 25 ? 'text-purple-300' :
                                'text-purple-200'
                        }`} />
                </div>
                <div className="flex-1">
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-purple-100 font-bold uppercase tracking-wider">Brain Growing</span>
                        <span className="text-[10px] text-emerald-300 font-bold">{Math.round(totalProgress)}%</span>
                    </div>
                    {/* Organic growth bar */}
                    <div className="mt-1 h-1.5 bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
                        <div
                            className="h-full bg-gradient-to-r from-purple-400 via-emerald-400 to-emerald-300 transition-all duration-1000 ease-out rounded-full"
                            style={{ width: `${totalProgress}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Neural Network style material indicators */}
            <div className="flex flex-wrap gap-1">
                {materials.map((material, idx) => {
                    const progress = getStageProgress(material.learning_stage || 'uploaded')
                    const pulseDelay = idx * 0.2

                    return (
                        <div
                            key={material.id || idx}
                            className="relative group"
                            title={`${material.filename}`}
                        >
                            {/* Synaptic connection effect */}
                            <div
                                className="absolute -inset-1 bg-gradient-to-r from-purple-400/20 to-emerald-400/20 rounded-lg blur opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                                style={{ animationDelay: `${pulseDelay}s` }}
                            />

                            {/* Neuron node */}
                            <div className="relative w-6 h-6 rounded-full overflow-hidden bg-white/5 border border-white/10 backdrop-blur-sm">
                                {/* Growing fill with organic animation */}
                                <div
                                    className={`absolute bottom-0 left-0 right-0 transition-all duration-700 ease-out ${progress >= 100 ? 'bg-gradient-to-t from-emerald-400 to-emerald-300' :
                                        progress >= 75 ? 'bg-gradient-to-t from-emerald-500 to-purple-400' :
                                            progress >= 50 ? 'bg-gradient-to-t from-purple-400 to-purple-300' :
                                                'bg-gradient-to-t from-purple-500 to-purple-400'
                                        }`}
                                    style={{ height: `${progress}%` }}
                                >
                                    {/* Shimmer effect for active learning */}
                                    {progress < 100 && (
                                        <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white/20 to-transparent animate-pulse" />
                                    )}
                                </div>

                                {/* Completion sparkle */}
                                {progress === 100 && (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <Sparkles className="h-3 w-3 text-white animate-pulse" />
                                    </div>
                                )}
                            </div>

                            {/* Enhanced tooltip */}
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-black/95 text-white text-[10px] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 border border-emerald-400/30">
                                <div className="font-bold truncate max-w-[120px]">{material.filename}</div>
                                <div className="text-emerald-300">{progress}% learned</div>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default function BuddyPage() {
    const router = useRouter()
    const { user } = useAuth()
    const { stats, levelTitle } = useStats()
    const [isCustomizing, setIsCustomizing] = React.useState(false)

    // Recalculate level from total XP using new formula to ensure consistency
    // This handles cases where DB still has old level values
    const correctLevel = Math.min(1 + Math.floor(stats.total_xp / 100), 1000)

    // Match Backend Formula: Linear progression - 100 XP per level, capped at 1000
    // Level = 1 + (XP // 100), max 1000
    const currentLevelMinXP = (correctLevel - 1) * 100
    const nextLevelMinXP = correctLevel >= 1000 ? currentLevelMinXP : correctLevel * 100
    const xpProgress = Math.max(0, stats.total_xp - currentLevelMinXP) // Ensure never negative
    const xpRequiredForLevel = Math.max(1, nextLevelMinXP - currentLevelMinXP) // Ensure never zero

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-8">
            {/* Buddy Hero Section */}
            <div className="relative rounded-3xl bg-gradient-to-br from-primary via-purple-700 to-indigo-900 p-8 overflow-hidden border border-white/10 shadow-xl shadow-primary/20 animate-in fade-in duration-500">
                <div className="absolute top-0 right-0 p-32 bg-white/10 rounded-full blur-3xl -mr-16 -mt-16"></div>

                <div className="relative z-10 flex flex-col md:flex-row items-center gap-10">
                    {/* Avatar Placeholder */}
                    <div className="relative group cursor-pointer" onClick={() => setIsCustomizing(true)}>
                        <div className="w-48 h-48 bg-white/10 backdrop-blur-md rounded-full border-4 border-white/20 flex items-center justify-center shadow-2xl relative group-hover:scale-105 transition-transform duration-300">
                            <span className="text-8xl animate-in zoom-in duration-500">{AVATAR_ICONS[stats.buddyAvatar] || '🌱'}</span>
                            <div className="absolute bottom-2 right-2 bg-white text-primary p-2 rounded-full border border-primary/20 shadow-md">
                                <Edit2 className="h-4 w-4" />
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 text-center md:text-left space-y-4">
                        <div>
                            <h1 className="text-4xl font-black text-white mb-2 tracking-tight">{stats.buddyName}</h1>
                            <p className="text-purple-100 text-lg font-medium opacity-90">Your AI Learning Companion</p>

                            {/* Brain Growing Visualization */}
                            <BrainGrowingIndicator />
                        </div>

                        <div className="flex gap-4 justify-center md:justify-start pt-4">
                            <Button className="bg-white text-primary hover:bg-white/90 font-bold px-8 rounded-xl shadow-lg border-none" onClick={() => router.push("/")}>
                                <MessageSquare className="mr-2 h-4 w-4" /> Chat Now
                            </Button>
                            <Button variant="outline" className="border-white/40 text-white hover:bg-white/10 font-bold px-8 rounded-xl backdrop-blur-sm" onClick={() => setIsCustomizing(true)}>
                                Customize Appearance
                            </Button>
                        </div>
                    </div>

                    <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 min-w-[240px] shadow-2xl">
                        <h3 className="text-white font-black text-xs uppercase tracking-[0.2em] mb-4 border-b border-white/10 pb-3">Personality Traits</h3>
                        <div className="space-y-4">
                            <div className="flex items-center gap-3 text-white font-bold text-sm">
                                <div className="h-8 w-8 rounded-full bg-purple-400/20 flex items-center justify-center">
                                    <Brain className="h-4 w-4 text-purple-200" />
                                </div>
                                <span className="opacity-90">Curious</span>
                            </div>
                            <div className="flex items-center gap-3 text-white font-bold text-sm">
                                <div className="h-8 w-8 rounded-full bg-yellow-400/20 flex items-center justify-center">
                                    <Zap className="h-4 w-4 text-yellow-200" />
                                </div>
                                <span className="opacity-90">Eager</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* XP Level Display */}
            <div className="animate-in slide-in-from-bottom duration-700">
                <h2 className="text-xl font-black flex items-center gap-3 mb-8 text-foreground uppercase tracking-widest">
                    <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center">
                        <GraduationCap className="h-5 w-5 text-primary" />
                    </div>
                    XP Level
                </h2>
                <Card className="border-border bg-card/50 backdrop-blur-sm relative overflow-hidden rounded-3xl shadow-lg">
                    <CardContent className="p-8">
                        <div className="flex flex-col md:flex-row items-center gap-8">
                            <div className="flex-1 w-full">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <h3 className="text-3xl font-black text-foreground">Level {correctLevel}</h3>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-sm text-muted-foreground uppercase tracking-widest font-bold">Total XP</p>
                                        <p className="text-2xl font-black text-foreground">{stats.total_xp}</p>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm font-bold text-muted-foreground">
                                        <span>{correctLevel >= 1000 ? 'Max Level Reached!' : `Progress to Level ${correctLevel + 1}`}</span>
                                        <span className="tabular-nums">{correctLevel >= 1000 ? 'MAXED' : `${xpProgress} / ${xpRequiredForLevel} XP`}</span>
                                    </div>
                                    <Progress value={correctLevel >= 1000 ? 100 : (xpProgress / xpRequiredForLevel) * 100} className="h-4 bg-secondary" />
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <BuddyCustomizationModal
                isOpen={isCustomizing}
                onClose={() => setIsCustomizing(false)}
            />
        </div>
    )
}
