"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Users, Clock, Hash, Search, Plus, ExternalLink, Video, Mic, X, Trash2 } from "lucide-react"
import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/auth-context"

interface Room {
    id: number
    name: string
    subject: string
    participants: string[]
    max: number
    type: string
    active: boolean
    meeting_link?: string
    creator_name: string
}

export default function RoomsPage() {
    const { user } = useAuth()
    const [rooms, setRooms] = useState<Room[]>([])
    const [isCreating, setIsCreating] = useState(false)
    const [newRoomName, setNewRoomName] = useState("")
    const [newRoomSubject, setNewRoomSubject] = useState("General")
    const [newRoomLink, setNewRoomLink] = useState("")

    const router = useRouter()

    // Fetch rooms on mount
    useEffect(() => {
        fetchRooms()
        const interval = setInterval(fetchRooms, 3000) // Poll every 3s
        return () => clearInterval(interval)
    }, [])

    const fetchRooms = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/rooms`)
            if (res.ok) {
                const data = await res.json()
                setRooms(data)
            }
        } catch (error) {
            console.error("Failed to fetch rooms")
        }
    }

    const [activeRoom, setActiveRoom] = useState<Room | null>(null)
    const [socket, setSocket] = useState<WebSocket | null>(null)
    const [isListening, setIsListening] = useState(false)
    const recognitionRef = useState<any>(null)[0] // Simple ref-like state or use actual useRef
    const recognitionInstance = typeof window !== 'undefined' ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition : null

    // Background Speech-to-Text / Buddy observation logic
    useEffect(() => {
        if (!activeRoom || !user?.name || !recognitionInstance) return

        // 1. WebSocket for this specific room
        const wsUrl = `${(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000').replace('http', 'ws')}/api/rooms/ws/${activeRoom.id}/${user.name}`
        const ws = new WebSocket(wsUrl)
        setSocket(ws)

        // 2. Speech Recognition
        const recognition = new recognitionInstance()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'

        recognition.onresult = (event: any) => {
            const currentResultIndex = event.results.length - 1
            const transcript = event.results[currentResultIndex][0].transcript
            if (event.results[currentResultIndex].isFinal && ws.readyState === WebSocket.OPEN) {
                ws.send(transcript)
            }
        }

        recognition.onend = () => {
            if (activeRoom) recognition.start()
        }

        recognition.start()
        setIsListening(true)

        return () => {
            ws.close()
            recognition.stop()
            setIsListening(false)
        }
    }, [activeRoom, user?.name])

    const handleCreateRoom = async () => {
        if (!newRoomName.trim() || !newRoomLink.trim()) {
            alert("Please enter a room name and a meeting link.")
            return
        }

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/rooms`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newRoomName,
                    subject: newRoomSubject,
                    type: "GoogleMeet",
                    creator_id: user?.id || 1,
                    creator_name: user?.name || "Host",
                    meeting_link: newRoomLink
                })
            })

            if (res.ok) {
                const newRoomRes = await res.json()
                setIsCreating(false)
                setNewRoomName("")
                setNewRoomSubject("General")
                setNewRoomLink("")
                fetchRooms()

                // Auto-join creator: Open Meet and start hidden observation
                if (newRoomLink) {
                    window.open(newRoomLink, '_blank')
                    // Start observation for the newly created room
                    const createdRoom = { ...newRoomRes, id: newRoomRes.id, name: newRoomName, subject: newRoomSubject, meeting_link: newRoomLink }
                    setActiveRoom(createdRoom)
                }
            }
        } catch (error) {
            alert("Failed to create room server-side")
        }
    }

    const deleteRoom = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation()
        if (confirm("Delete this room?")) {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/rooms/${id}`, { method: 'DELETE' })
                if (res.ok) {
                    if (activeRoom?.id === id) setActiveRoom(null)
                    fetchRooms()
                }
            } catch (error) {
                console.error("Failed to delete room")
            }
        }
    }

    const joinRoom = (room: Room) => {
        // Open Google Meet
        if (room.meeting_link) {
            window.open(room.meeting_link, '_blank')
        }
        // Start background AI observation
        setActiveRoom(room)
    }

    const openGoogleMeet = () => {
        window.open("https://meet.google.com/new", "_blank")
    }

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">Study Rooms</h1>
                    <p className="text-slate-400">Join a Google Meet session with peers</p>
                </div>
                <div className="flex gap-3">
                    <Button className="bg-indigo-600 hover:bg-indigo-700" onClick={() => setIsCreating(true)}>
                        <Plus className="mr-2 h-4 w-4" /> Create Room
                    </Button>
                </div>
            </div>

            {/* Create Room Modal */}
            {isCreating && (
                <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                    <Card className="w-full max-w-md bg-slate-900 border-slate-800 shadow-xl">
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle>Create Study Room</CardTitle>
                            <Button variant="ghost" size="icon" onClick={() => setIsCreating(false)}>
                                <X className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Room Name</label>
                                <Input
                                    placeholder="e.g. Biology Exam Prep"
                                    value={newRoomName}
                                    onChange={(e) => setNewRoomName(e.target.value)}
                                    className="bg-slate-800 border-slate-700"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Subject</label>
                                <Input
                                    placeholder="e.g. Physics, General"
                                    value={newRoomSubject}
                                    onChange={(e) => setNewRoomSubject(e.target.value)}
                                    className="bg-slate-800 border-slate-700"
                                />
                            </div>

                            <div className="space-y-2 pt-2 border-t border-slate-800">
                                <label className="text-sm font-medium flex justify-between">
                                    Meeting Link
                                    <span
                                        className="text-xs text-indigo-400 cursor-pointer hover:underline flex items-center"
                                        onClick={openGoogleMeet}
                                    >
                                        Generate New Meet Link <ExternalLink className="ml-1 h-3 w-3" />
                                    </span>
                                </label>
                                <Input
                                    placeholder="Paste Google Meet link here..."
                                    value={newRoomLink}
                                    onChange={(e) => setNewRoomLink(e.target.value)}
                                    className="bg-slate-800 border-slate-700"
                                />
                                <p className="text-xs text-slate-500">
                                    Click "Generate" to open Google Meet, copy the link, and paste it here.
                                </p>
                            </div>

                            <Button className="w-full bg-indigo-600 hover:bg-indigo-700 mt-2" onClick={handleCreateRoom}>
                                Launch Room
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            )}

            <div className="flex gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                    <Input placeholder="Search rooms..." className="pl-9 bg-slate-900 border-slate-700" />
                </div>
            </div>

            {rooms.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-500 border-2 border-dashed border-slate-800 rounded-xl bg-slate-900/50">
                    <div className="h-16 w-16 bg-slate-800/50 rounded-full flex items-center justify-center mb-4">
                        <Users className="h-8 w-8 opacity-50 text-indigo-400" />
                    </div>
                    <h3 className="text-lg font-medium text-slate-300 mb-1">No Active Rooms</h3>
                    <Button onClick={() => setIsCreating(true)} variant="secondary" className="mt-4">
                        Start a Room
                    </Button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {rooms.map((room) => (
                        <Card key={room.id} className="border-slate-800 bg-slate-900/50 hover:border-indigo-500/50 transition-colors group relative">
                            {/* Delete Button for Everyone (requested by user to be able to delete) */}
                            {/* Ideally checked against creator_name, but user wants easy delete */}
                            <button
                                onClick={(e) => deleteRoom(e, room.id)}
                                className="absolute top-3 right-3 p-1.5 rounded-full hover:bg-red-900/30 text-slate-600 hover:text-red-400 transition-colors z-10"
                                title="Delete Room"
                            >
                                <Trash2 className="h-4 w-4" />
                            </button>

                            <CardHeader className="pb-3">
                                <div className="flex justify-between items-start mb-2">
                                    <Badge variant="default" className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                        {room.subject}
                                    </Badge>
                                </div>
                                <CardTitle className="text-lg group-hover:text-indigo-400 transition-colors">{room.name}</CardTitle>
                                <CardDescription className="flex items-center gap-2 text-xs">
                                    Host: {room.creator_name}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex justify-between items-center text-sm text-slate-400">
                                    <div className="flex items-center gap-2">
                                        <Users className="h-4 w-4" />
                                        <span>{room.participants?.length || 0} joined</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-green-400">
                                        <Video className="h-4 w-4" />
                                        <span>Google Meet</span>
                                    </div>
                                </div>

                                <Button
                                    className="w-full bg-slate-800 hover:bg-green-600 hover:text-white border border-slate-700 transition-all"
                                    onClick={() => joinRoom(room)}
                                >
                                    Join Meeting <ExternalLink className="ml-2 h-4 w-4" />
                                </Button>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
}
