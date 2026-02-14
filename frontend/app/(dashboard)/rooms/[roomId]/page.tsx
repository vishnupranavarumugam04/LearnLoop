"use client"

import { useState, useEffect, useRef } from "react"
import { useParams, useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { MessageSquare, Share2, Ear, Waves, Mic, MicOff, Info } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/context/auth-context"

/**
 * AI Buddy Observation Room
 * Features:
 * 1. Speech-to-Text (Buddy Ears): Listens to user microphone and sends transcripts to Buddy.
 * 2. Interaction Chat: Text-based communication with the Buddy.
 * 3. Live Transcript Feed: Shows what the Buddy is hearing in real-time.
 */
export default function RoomSessionPage() {
    const params = useParams()
    const searchParams = useSearchParams()
    const router = useRouter()
    const { user } = useAuth()

    const roomId = params.roomId

    const [messages, setMessages] = useState<any[]>([])
    const [inputText, setInputText] = useState("")
    const [socket, setSocket] = useState<WebSocket | null>(null)
    const [buddyStatus, setBuddyStatus] = useState("Observing...")
    const [isListening, setIsListening] = useState(false)
    const [transcriptFeed, setTranscriptFeed] = useState<string[]>([])

    const recognitionRef = useRef<any>(null)

    // WebSocket Connection
    useEffect(() => {
        if (!roomId || !user?.name) return

        const wsUrl = `${(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000').replace('http', 'ws')}/api/rooms/ws/${roomId}/${user.name}`
        const ws = new WebSocket(wsUrl)

        ws.onopen = () => console.log("Connected to room chat")
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data)
            setMessages(prev => [...prev, data])
            if (data.is_ai) {
                setBuddyStatus("Buddy Replying...")
                setTimeout(() => setBuddyStatus("Observing..."), 2000)
            }
        }

        setSocket(ws)
        return () => ws.close()
    }, [roomId, user?.name])

    // Speech-to-Text Logic (Buddy Ears)
    useEffect(() => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
        if (!SpeechRecognition) {
            console.error("Speech recognition not supported in this browser.")
            return
        }

        const recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'

        recognition.onresult = (event: any) => {
            // Get the current transcript chunk
            const currentResultIndex = event.results.length - 1
            const transcript = event.results[currentResultIndex][0].transcript

            if (event.results[currentResultIndex].isFinal) {
                setTranscriptFeed(prev => [transcript, ...prev].slice(0, 10))

                // Send transcribed speech via WebSocket for AI processing
                if (socket && transcript.trim().length > 5) {
                    socket.send(transcript)
                }
            }
        }

        recognition.onend = () => {
            // Keep listening if enabled
            if (isListening) {
                try {
                    recognition.start()
                } catch (e) {
                    console.error("Failed to restart recognition:", e)
                }
            }
        }

        recognitionRef.current = recognition

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop()
            }
        }
    }, [socket, isListening])

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop()
            setIsListening(false)
        } else {
            try {
                recognitionRef.current?.start()
                setIsListening(true)
            } catch (e) {
                console.error("Speech recognition error:", e)
                alert("Please ensure microphone permissions are granted.")
            }
        }
    }

    const sendMessage = () => {
        if (!socket || !inputText.trim()) return
        socket.send(inputText)
        setInputText("")
    }

    const handleLeave = () => {
        if (confirm("Stop session?")) router.push('/rooms')
    }

    return (
        <div className="h-[calc(100vh-4rem)] flex flex-col bg-slate-950 p-4 gap-4 overflow-hidden">
            {/* Header */}
            <div className="flex justify-between items-center shrink-0 bg-slate-900 p-4 rounded-xl border border-slate-800 shadow-lg">
                <div className="flex items-center gap-4">
                    <div className="h-10 w-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                        <Ear className="text-white h-6 w-6" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold flex items-center gap-2 text-slate-100">
                            Study Session #{roomId}
                        </h1>
                        <p className="text-xs text-slate-400 font-medium">AI Buddy is optimized for your Google Meet session</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1 flex items-center gap-2">
                        <span className={cn("w-2 h-2 rounded-full", isListening ? "bg-green-500 animate-pulse" : "bg-slate-600")}></span>
                        <span className="text-xs font-bold text-indigo-400">Buddy: {buddyStatus}</span>
                    </div>
                    <Button variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800 text-slate-300" onClick={() => {
                        navigator.clipboard.writeText(roomId as string)
                        alert("Room Code copied!")
                    }}>
                        <Share2 className="h-4 w-4 mr-2 text-indigo-400" /> Share ID
                    </Button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex gap-4 min-h-0">
                {/* Observation Stage */}
                <div className="flex-1 flex flex-col gap-4">
                    <div className="flex-1 bg-slate-900 rounded-2xl border border-slate-800 p-8 shadow-inner flex flex-col items-center justify-center relative overflow-hidden">
                        {/* Background Visual Effects */}
                        <div className="absolute inset-0 opacity-10 pointer-events-none overflow-hidden">
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500 rounded-full blur-[120px] animate-pulse-slow"></div>
                        </div>

                        {/* Status Section */}
                        <div className="text-center z-10 space-y-8">
                            <div className={cn(
                                "h-40 w-40 rounded-full flex items-center justify-center transition-all duration-700",
                                isListening
                                    ? "bg-indigo-600 shadow-[0_0_80px_rgba(79,70,229,0.6)] scale-110"
                                    : "bg-slate-800 grayscale shadow-none hover:grayscale-0 hover:bg-slate-700"
                            )}>
                                {isListening ? (
                                    <div className="flex space-x-2 items-end h-12">
                                        {[1.2, 2.5, 4, 2.8, 1.5, 3.2, 1.8].map((n, i) => (
                                            <div
                                                key={i}
                                                className="w-2 bg-white rounded-full animate-bounce"
                                                style={{ height: `${n * 25}%`, animationDelay: `${i * 0.1}s` }}
                                            ></div>
                                        ))}
                                    </div>
                                ) : (
                                    <Ear className="h-16 w-16 text-slate-400" />
                                )}
                            </div>

                            <div className="space-y-3">
                                <h2 className="text-3xl font-extrabold tracking-tight text-white">
                                    {isListening ? "Buddy Ears: Active" : "Buddy Ears: Offline"}
                                </h2>
                                <p className="text-slate-400 max-w-sm mx-auto text-sm leading-relaxed font-medium">
                                    Buddy listens to your descriptions while you talk in Google Meet and uses them to grow its knowledge graph.
                                </p>
                            </div>

                            <Button
                                size="lg"
                                className={cn(
                                    "px-12 rounded-full font-bold transition-all h-16 text-xl",
                                    isListening
                                        ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 border-red-500/20 border"
                                        : "bg-indigo-600 hover:bg-indigo-700 shadow-xl shadow-indigo-600/30 text-white"
                                )}
                                onClick={toggleListening}
                            >
                                {isListening ? (
                                    <><MicOff className="mr-3 h-6 w-6" /> Stop Listening</>
                                ) : (
                                    <><Mic className="mr-3 h-6 w-6" /> Turn on Buddy Ears</>
                                )}
                            </Button>
                        </div>

                        {/* Leave/Stop Helper */}
                        <div className="absolute bottom-8 right-8">
                            <Button variant="ghost" className="text-slate-500 hover:text-red-400 font-medium" onClick={handleLeave}>
                                End Study Session
                            </Button>
                        </div>
                    </div>

                    {/* Live Transcript Stream */}
                    <div className="h-44 bg-slate-900 rounded-2xl border border-slate-800 p-5 shadow-inner overflow-hidden flex flex-col">
                        <div className="flex items-center gap-2 mb-3 px-1 shrink-0">
                            <Waves className="h-4 w-4 text-indigo-400" />
                            <span className="text-[11px] font-extrabold uppercase tracking-widest text-slate-500">Live Transcript Analysis</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-2.5 px-1 scrollbar-hide">
                            {transcriptFeed.length === 0 ? (
                                <div className="text-slate-600 text-sm flex items-center gap-3 italic py-6 group">
                                    <Info className="h-5 w-5 opacity-30 group-hover:opacity-60 transition-opacity" />
                                    <span>Start speaking... the Buddy is ready to hear your descriptions.</span>
                                </div>
                            ) : (
                                transcriptFeed.map((text, i) => (
                                    <div key={i} className="text-slate-200 text-sm opacity-90 border-l-3 border-indigo-500/40 pl-4 py-2 bg-slate-800/30 rounded-r-xl font-medium animate-in fade-in slide-in-from-left-2 duration-300">
                                        {text}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Sidebar (Room Chat) */}
                <div className="w-80 bg-slate-900 rounded-2xl border border-slate-800 flex flex-col shadow-2xl">
                    <div className="p-5 border-b border-slate-800 font-bold flex items-center justify-between bg-slate-900/50">
                        <div className="flex items-center gap-2 text-slate-200">
                            <MessageSquare className="h-4 w-4 text-indigo-400" /> Direct Interaction
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-5 space-y-5">
                        {messages.length === 0 && (
                            <div className="text-center text-slate-600 text-xs py-12 italic font-medium">
                                Address "Buddy" in chat for direct assistance.
                            </div>
                        )}
                        {messages.map((msg, i) => (
                            <div key={i} className={cn(
                                "flex flex-col gap-1.5",
                                msg.is_ai ? "items-start" : "items-end"
                            )}>
                                <span className="text-[10px] text-slate-500 uppercase tracking-widest px-2 font-bold">
                                    {msg.user_name}
                                </span>
                                <div className={cn(
                                    "max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-md font-medium",
                                    msg.is_ai
                                        ? "bg-indigo-600 text-white rounded-tl-none border border-indigo-400/40"
                                        : "bg-slate-800 text-slate-200 rounded-tr-none border border-slate-700"
                                )}>
                                    {msg.content}
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="p-5 border-t border-slate-800 bg-slate-900/50">
                        <div className="flex gap-2">
                            <input
                                className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-xs focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-slate-200 placeholder:text-slate-600 font-medium"
                                placeholder="Message Buddy..."
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                            />
                            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 rounded-xl px-5 font-bold" onClick={sendMessage}>
                                Send
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
