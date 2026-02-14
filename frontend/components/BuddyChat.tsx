"use client"

import * as React from "react"
import { Send, User, Bot, Sparkles, Plus, Mic } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
    role: "user" | "model"
    content: string
}

import { useAuth } from "@/context/auth-context"
import { useStats } from "@/context/stats-context"
import { useSearchParams } from "next/navigation"

// ... imports

interface BuddyChatProps {
    onXPUpdate?: () => void
}

export function BuddyChat({ onXPUpdate }: BuddyChatProps = {}) {
    const { user } = useAuth()
    const { stats, refreshStats } = useStats()
    const searchParams = useSearchParams()
    const urlSessionId = searchParams.get('session')
    const materialContext = searchParams.get('material')

    const [messages, setMessages] = React.useState<Message[]>([])
    const [input, setInput] = React.useState("")
    const [isLoading, setIsLoading] = React.useState(false)
    const [currentSessionId, setCurrentSessionId] = React.useState<string | null>(urlSessionId)
    const [isRecording, setIsRecording] = React.useState(false)
    const messagesEndRef = React.useRef<HTMLDivElement>(null)
    const recognitionRef = React.useRef<any>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    React.useEffect(() => {
        scrollToBottom()
    }, [messages, isLoading])

    // Update session ID if URL changes
    React.useEffect(() => {
        if (urlSessionId) setCurrentSessionId(urlSessionId)
    }, [urlSessionId])

    // Initialize speech recognition
    React.useEffect(() => {
        if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
            const recognition = new SpeechRecognition()

            recognition.continuous = false
            recognition.interimResults = false
            recognition.lang = 'en-US'

            recognition.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript
                setInput(transcript)
                setIsRecording(false)
            }

            recognition.onerror = (event: any) => {
                console.error('Speech recognition error:', event.error)
                setIsRecording(false)
            }

            recognition.onend = () => {
                setIsRecording(false)
            }

            recognitionRef.current = recognition
        }
    }, [])

    // Load history on mount or session change
    React.useEffect(() => {
        const fetchHistory = async () => {
            if (!user?.email) return

            // If no session ID, it's a fresh chat.
            if (!currentSessionId) {
                if (user?.name) {
                    const firstName = user.name.split(' ')[0]
                    const welcomeMsg = materialContext
                        ? `Hi ${firstName}! I'm ready to study "${materialContext}" with you. Shall I start by teaching you a key concept, or do you want to try explaining it to me?`
                        : `Hi ${firstName}! I'm Buddy. I'm excited to learn with you today. What topic should we explore?`

                    setMessages([
                        { role: "model", content: welcomeMsg }
                    ])
                } else {
                    setMessages([])
                }
                return
            }

            // Optimization: If we just created a session in this component, don't re-fetch immediately 
            if (activeSessionIdRef.current === currentSessionId && messages.length > 0) return;

            const sessionIdParam = `&session_id=${currentSessionId}`

            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/buddy/history?username=${encodeURIComponent(user.email)}${sessionIdParam}`)
                if (response.ok) {
                    const data = await response.json()
                    if (data.history && data.history.length > 0) {
                        setMessages(data.history)
                    } else {
                        setMessages([])
                    }
                }
            } catch (error) {
                console.error("Failed to load history", error)
            }
        }

        fetchHistory()
    }, [user, currentSessionId, materialContext])

    const activeSessionIdRef = React.useRef<string | null>(urlSessionId)

    const handleVoiceInput = () => {
        if (!recognitionRef.current) {
            alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.')
            return
        }

        if (isRecording) {
            try {
                recognitionRef.current.stop()
            } catch (e) {
                console.error('Error stopping recognition:', e)
            }
            setIsRecording(false)
        } else {
            setInput('') // Clear input before recording
            setIsRecording(true)
            try {
                recognitionRef.current.start()
            } catch (e) {
                console.error('Error starting recognition:', e)
                setIsRecording(false)
            }
        }
    }

    const handleNewChat = () => {
        setCurrentSessionId(null)
        activeSessionIdRef.current = null
        if (user?.name) {
            setMessages([{ role: "model", content: `Ready for a new topic, ${user.name.split(' ')[0]}!` }])
        } else {
            setMessages([])
        }
        window.history.pushState({}, '', window.location.pathname)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || !user?.email) return

        const userMessage: Message = { role: "user", content: input }

        // Use a functional update to ensure we have the most recent messages even if the effect didn't run yet
        setMessages((prev) => [...prev, userMessage])
        const currentMessages = [...messages, userMessage]
        const currentInput = input
        setInput("")
        setIsLoading(true)

        let activeSessionId = currentSessionId

        if (!activeSessionId) {
            try {
                const title = materialContext ? `Study: ${materialContext}` : `Chat: ${currentInput.substring(0, 20)}...`
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/buddy/sessions`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title, user_id: user.email })
                })
                if (res.ok) {
                    const data = await res.json()
                    if (data.session_id) {
                        activeSessionId = data.session_id
                        activeSessionIdRef.current = String(data.session_id)
                        setCurrentSessionId(String(data.session_id))
                        const newUrl = `${window.location.pathname}?session=${data.session_id}${materialContext ? `&material=${encodeURIComponent(materialContext)}` : ''}`
                        window.history.pushState({}, '', newUrl)
                    }
                }
            } catch (e) {
                console.error("Failed to auto-create session", e)
            }
        }

        try {
            // Create session context identifier for rate limiting
            const sessionContext = activeSessionId ? `${activeSessionId}${materialContext ? `-material-${materialContext}` : ''}` : 'new'

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/buddy/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Session-Context": sessionContext
                },
                body: JSON.stringify({
                    messages: currentMessages,
                    user_id: user?.email,
                    session_id: activeSessionId ? parseInt(String(activeSessionId)) : null,
                    context: materialContext
                }),
            })

            if (!response.ok) {
                // Handle rate limiting gracefully
                if (response.status === 429) {
                    const errorData = await response.json().catch(() => ({}))
                    const waitTime = errorData.retry_after || 60
                    setMessages((prev) => [...prev, {
                        role: "model",
                        content: `Hey! I need a short breather 😊 I've been chatting a lot! Let's continue in about ${waitTime} seconds. Take a moment to review what we've discussed!`
                    }])
                    setIsLoading(false)
                    return
                }
                throw new Error("Failed to fetch")
            }

            const data = await response.json()
            if (onXPUpdate) onXPUpdate()
            refreshStats()
            setMessages((prev) => [...prev, data])
        } catch (error) {
            setMessages((prev) => [...prev, { role: "model", content: "Oops, I'm having trouble thinking right now. Can we try again?" }])
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Card className="h-[600px] flex flex-col w-full shadow-lg border border-border bg-card overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-primary/90 to-purple-500 text-primary-foreground flex flex-row items-center justify-between border-b">
                <div>
                    <div className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-yellow-300" />
                        <CardTitle className="text-lg">{stats.buddyName} (Level {stats.level}) {currentSessionId ? `- Session #${currentSessionId}` : ""}</CardTitle>
                    </div>
                    <CardDescription className="text-primary-foreground/80">AI Learning Companion</CardDescription>
                </div>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleNewChat}
                    className="text-primary-foreground hover:bg-white/10 border border-primary-foreground/20 rounded-lg flex items-center gap-2"
                >
                    <Plus className="h-4 w-4" />
                    New Chat
                </Button>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-4 overflow-hidden bg-background">
                <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
                    {messages.map((message, i) => (
                        <div
                            key={i}
                            className={`flex items-start gap-3 ${message.role === "user" ? "flex-row-reverse" : "flex-row"
                                }`}
                        >
                            <div
                                className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${message.role === "user"
                                    ? "bg-indigo-600 text-white"
                                    : "bg-emerald-500 text-white"
                                    }`}
                            >
                                {message.role === "user" ? <User size={16} /> : <Bot size={16} />}
                            </div>
                            <div
                                className={`rounded-2xl px-4 py-3 max-w-[80%] text-sm shadow-sm ${message.role === "user"
                                    ? "bg-primary text-primary-foreground rounded-br-none"
                                    : "bg-secondary text-secondary-foreground border border-border rounded-bl-none"
                                    }`}
                            >
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        // Headings
                                        h1: ({ node, ...props }) => <h1 className="text-lg font-bold mt-2 mb-1" {...props} />,
                                        h2: ({ node, ...props }) => <h2 className="text-base font-bold mt-2 mb-1" {...props} />,
                                        h3: ({ node, ...props }) => <h3 className="text-sm font-bold mt-1 mb-1" {...props} />,
                                        // Paragraphs with proper spacing
                                        p: ({ node, ...props }) => <p className="mb-2 last:mb-0 leading-relaxed" {...props} />,
                                        // Lists
                                        ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
                                        ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
                                        li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
                                        // Code blocks
                                        code: ({ node, inline, ...props }: any) =>
                                            inline
                                                ? <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono" {...props} />
                                                : <code className="block bg-muted p-2 rounded my-2 overflow-x-auto text-xs font-mono" {...props} />,
                                        pre: ({ node, ...props }) => <pre className="bg-muted p-2 rounded my-2 overflow-x-auto" {...props} />,
                                        // Links
                                        a: ({ node, ...props }) => <a className="text-blue-500 hover:underline font-medium" {...props} />,
                                        // Blockquotes
                                        blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-muted pl-3 italic my-2" {...props} />,
                                        // Strong and emphasis
                                        strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
                                        em: ({ node, ...props }) => <em className="italic" {...props} />,
                                        // Tables
                                        table: ({ node, ...props }) => <table className="border-collapse border border-border my-2 w-full" {...props} />,
                                        thead: ({ node, ...props }) => <thead className="bg-muted" {...props} />,
                                        th: ({ node, ...props }) => <th className="border border-border px-2 py-1 text-left font-semibold" {...props} />,
                                        td: ({ node, ...props }) => <td className="border border-border px-2 py-1" {...props} />,
                                        // Horizontal rule
                                        hr: ({ node, ...props }) => <hr className="my-3 border-border" {...props} />,
                                    }}
                                >
                                    {message.content}
                                </ReactMarkdown>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-start gap-3">
                            <div className="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0">
                                <Bot size={16} />
                            </div>
                            <div className="bg-secondary text-secondary-foreground border border-border rounded-2xl rounded-bl-none px-4 py-2 text-sm shadow-sm">
                                <span className="animate-pulse">Thinking...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
                <form onSubmit={handleSubmit} className="flex gap-2">
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={isRecording ? "Listening..." : "Teach me something, or ask me a question..."}
                        disabled={isLoading || isRecording}
                        className="rounded-full shadow-sm border-border focus-visible:ring-primary"
                    />
                    <Button
                        type="button"
                        size="icon"
                        variant={isRecording ? "destructive" : "outline"}
                        onClick={handleVoiceInput}
                        disabled={isLoading}
                        className={`rounded-full ${isRecording ? 'animate-pulse bg-red-500 hover:bg-red-600' : ''}`}
                        title={isRecording ? "Stop recording" : "Voice input"}
                    >
                        <Mic size={18} className={isRecording ? 'text-white' : ''} />
                    </Button>
                    <Button type="submit" size="icon" disabled={isLoading || !input.trim()} className="rounded-full bg-primary hover:bg-primary/90">
                        <Send size={18} />
                    </Button>
                </form>
            </CardContent>
        </Card>
    )
}
