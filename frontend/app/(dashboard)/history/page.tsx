"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MessageSquare, Calendar, Trash2, Plus } from "lucide-react"
import { useRouter } from "next/navigation"

import { useAuth } from "@/context/auth-context"

interface Session {
    id: number
    title: string
    created_at: string
    updated_at: string
}

export default function HistoryPage() {
    const router = useRouter()
    const { user } = useAuth()
    const [sessions, setSessions] = React.useState<Session[]>([])
    const [isLoading, setIsLoading] = React.useState(true)

    React.useEffect(() => {
        if (user?.email) {
            fetchSessions()
        }
    }, [user])

    const fetchSessions = async () => {
        if (!user?.email) return
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/buddy/sessions?username=${encodeURIComponent(user.email)}`)
            if (res.ok) {
                const data = await res.json()
                setSessions(data.sessions || [])
            }
        } catch (error) {
            console.error(error)
        } finally {
            setIsLoading(false)
        }
    }

    const createSession = async () => {
        if (!user?.email) return
        try {
            const title = `Chat ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/buddy/sessions`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, user_id: user.email })
            })
            if (res.ok) {
                const data = await res.json()
                // Redirect to dashboard with session
                router.push(`/?session=${data.session_id}`)
            }
        } catch (error) {
            console.error(error)
        }
    }

    const deleteSession = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation() // Prevent card click
        if (!confirm("Delete this chat?")) return

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/buddy/sessions/${id}`, {
                method: "DELETE"
            })
            if (res.ok) {
                setSessions(prev => prev.filter(s => s.id !== id))
            }
        } catch (error) {
            console.error(error)
        }
    }

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-8">
            <div className="flex justify-between items-center bg-card p-6 rounded-2xl border border-border shadow-sm">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600">
                        Chat History
                    </h1>
                    <p className="text-muted-foreground mt-1">Manage your learning conversations with Buddy</p>
                </div>
                <Button onClick={createSession} className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2 rounded-xl h-11 px-6 shadow-md transition-all hover:scale-105">
                    <Plus size={18} /> New Chat
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sessions.map(session => (
                    <Card
                        key={session.id}
                        className="cursor-pointer hover:border-primary transition-all group rounded-2xl border-border bg-card shadow-sm hover:shadow-md"
                        onClick={() => router.push(`/?session=${session.id}`)}
                    >
                        <CardHeader className="pb-2">
                            <div className="flex justify-between items-start">
                                <CardTitle className="text-lg font-semibold text-foreground truncate pr-2 group-hover:text-primary transition-colors">{session.title}</CardTitle>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                    onClick={(e) => deleteSession(e, session.id)}
                                >
                                    <Trash2 size={16} />
                                </Button>
                            </div>
                            <CardDescription className="flex items-center gap-1 text-xs">
                                <Calendar size={12} />
                                {new Date(session.updated_at).toLocaleDateString()}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <div className="p-1.5 bg-primary/10 rounded-lg text-primary">
                                    <MessageSquare size={14} />
                                </div>
                                <span className="font-medium">Continue conversation</span>
                            </div>
                        </CardContent>
                    </Card>
                ))}

                {sessions.length === 0 && !isLoading && (
                    <div className="col-span-full py-12 text-center text-slate-500 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-dashed">
                        <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-20" />
                        <p>No chat history yet.</p>
                        <Button variant="link" onClick={createSession} className="text-indigo-500">Start new chat</Button>
                    </div>
                )}
            </div>
        </div>
    )
}
