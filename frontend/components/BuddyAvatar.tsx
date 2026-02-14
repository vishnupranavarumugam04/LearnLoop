"use client"

import * as React from "react"
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/auth-context"
import { useStats } from "@/context/stats-context"
import "../styles/buddy-avatar.css"

type EmotionState = "idle" | "listening" | "thinking" | "speaking" | "happy" | "confused"

interface BuddyAvatarProps {
    autoListen?: boolean
    showTranscript?: boolean
    onMessage?: (message: string) => void
}

export function BuddyAvatar({ autoListen = false, showTranscript = true }: BuddyAvatarProps) {
    const { user } = useAuth()
    const { stats, refreshStats } = useStats()
    const [emotion, setEmotion] = React.useState<EmotionState>("idle")
    const [isListening, setIsListening] = React.useState(false)
    const [audioEnabled, setAudioEnabled] = React.useState(true)
    const [transcript, setTranscript] = React.useState("")
    const [lastResponse, setLastResponse] = React.useState("")
    const [sessionId, setSessionId] = React.useState<string | null>(null)

    const recognitionRef = React.useRef<any>(null)
    const synthRef = React.useRef<SpeechSynthesis | null>(null)
    const isProcessingRef = React.useRef(false)
    const autoListenEnabledRef = React.useRef(autoListen)
    const isStartingRef = React.useRef(false) // Track if recognition is starting/active

    // Initialize speech synthesis
    React.useEffect(() => {
        if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
            synthRef.current = window.speechSynthesis
        }
    }, [])

    // Initialize speech recognition
    React.useEffect(() => {
        if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
            const recognition = new SpeechRecognition()

            recognition.continuous = false
            recognition.interimResults = false
            recognition.lang = 'en-US'

            recognition.onstart = () => {
                isStartingRef.current = true
                setEmotion("listening")
                setIsListening(true)
            }

            recognition.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript
                setTranscript(transcript)
                setIsListening(false)
                isStartingRef.current = false
                handleUserSpeech(transcript)
            }

            recognition.onerror = (event: any) => {
                // Silently handle common, non-critical errors
                const silentErrors = ['network', 'no-speech', 'aborted']
                if (!silentErrors.includes(event.error)) {
                    console.error('Speech recognition error:', event.error)
                }

                setIsListening(false)
                isStartingRef.current = false
                setEmotion("idle")

                // Only auto-restart for transient errors (network, no-speech)
                // Don't restart for permission errors or other persistent issues
                const transientErrors = ['network', 'no-speech']
                if (transientErrors.includes(event.error) && autoListenEnabledRef.current && !isProcessingRef.current) {
                    const retryDelay = event.error === 'network' ? 500 : 2000
                    setTimeout(() => {
                        if (autoListenEnabledRef.current && !isProcessingRef.current) {
                            startListening()
                        }
                    }, retryDelay)
                }
            }

            recognition.onend = () => {
                setIsListening(false)
                isStartingRef.current = false

                // Auto-restart listening if enabled and not processing
                if (autoListenEnabledRef.current && !isProcessingRef.current) {
                    setTimeout(() => {
                        if (autoListenEnabledRef.current && !isProcessingRef.current) {
                            startListening()
                        }
                    }, 500)
                }
            }

            recognitionRef.current = recognition
        }

        return () => {
            if (recognitionRef.current) {
                try {
                    recognitionRef.current.stop()
                } catch (e) {
                    // Ignore
                }
            }
        }
    }, [])

    // Auto-start listening on mount if enabled
    React.useEffect(() => {
        if (autoListen && recognitionRef.current) {
            setTimeout(() => startListening(), 1000)
        }
    }, [autoListen])

    const startListening = () => {
        if (!recognitionRef.current) {
            alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.')
            return
        }

        // Don't start if already listening, starting, or processing
        if (isStartingRef.current || isProcessingRef.current) return

        try {
            isStartingRef.current = true
            recognitionRef.current.start()
        } catch (e) {
            console.error('Error starting recognition:', e)
            isStartingRef.current = false
        }
    }

    const stopListening = () => {
        if (recognitionRef.current) {
            try {
                recognitionRef.current.stop()
            } catch (e) {
                console.error('Error stopping recognition:', e)
            }
        }
        setIsListening(false)
        isStartingRef.current = false
        setEmotion("idle")
    }

    const toggleListening = () => {
        autoListenEnabledRef.current = !autoListenEnabledRef.current

        if (autoListenEnabledRef.current) {
            startListening()
        } else {
            stopListening()
        }
    }

    const speak = (text: string) => {
        if (!synthRef.current || !audioEnabled) {
            // If audio is disabled, just mark as done and resume listening
            isProcessingRef.current = false
            setEmotion("idle")
            if (autoListenEnabledRef.current) {
                setTimeout(() => {
                    if (autoListenEnabledRef.current) {
                        startListening()
                    }
                }, 500)
            }
            return
        }

        // Cancel any ongoing speech
        synthRef.current.cancel()

        // Ensure voices are loaded (browser needs time to load voices)
        const voices = synthRef.current.getVoices()
        if (voices.length === 0) {
            // Voices not loaded yet, try again after a short delay
            setTimeout(() => speak(text), 100)
            return
        }

        const utterance = new SpeechSynthesisUtterance(text)
        utterance.rate = 1.0
        utterance.pitch = 1.1
        utterance.volume = 1.0


        // Select a female voice
        if (voices.length > 0) {
            // Try to find a female voice
            const femaleVoice = voices.find(voice =>
                voice.name.toLowerCase().includes('female') ||
                voice.name.toLowerCase().includes('zira') ||
                voice.name.toLowerCase().includes('susan') ||
                voice.name.toLowerCase().includes('samantha') ||
                voice.name.toLowerCase().includes('google uk english female') ||
                voice.name.toLowerCase().includes('google us english female')
            )

            utterance.voice = femaleVoice || voices[0]
        }

        utterance.onstart = () => {
            setEmotion("speaking")
        }

        utterance.onend = () => {
            setEmotion("idle")
            isProcessingRef.current = false

            // Resume listening if auto-listen is enabled
            if (autoListenEnabledRef.current) {
                setTimeout(() => {
                    if (autoListenEnabledRef.current) {
                        startListening()
                    }
                }, 500)
            }
        }

        utterance.onerror = (event) => {
            // Silently handle error - just resume normal operation
            setEmotion("idle")
            isProcessingRef.current = false

            // Resume listening even if speech failed
            if (autoListenEnabledRef.current) {
                setTimeout(() => {
                    if (autoListenEnabledRef.current) {
                        startListening()
                    }
                }, 500)
            }
        }

        synthRef.current.speak(utterance)
    }

    const handleUserSpeech = async (userText: string) => {
        if (!user?.email || isProcessingRef.current) return

        isProcessingRef.current = true
        setEmotion("thinking")

        // Stop listening while processing
        if (recognitionRef.current && isListening) {
            try {
                recognitionRef.current.stop()
            } catch (e) {
                // Ignore
            }
        }

        try {
            // Create session if needed
            let activeSessionId = sessionId
            if (!activeSessionId) {
                try {
                    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/buddy/sessions`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            title: `Voice Chat: ${userText.substring(0, 20)}...`,
                            user_id: user.email
                        })
                    })
                    if (res.ok) {
                        const data = await res.json()
                        if (data.session_id) {
                            activeSessionId = String(data.session_id)
                            setSessionId(activeSessionId)
                        }
                    }
                } catch (e) {
                    console.error("Failed to create session", e)
                }
            }

            // Get response from buddy
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/buddy/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Session-Context": activeSessionId ? `${activeSessionId}-voice` : 'voice-new'
                },
                body: JSON.stringify({
                    messages: [
                        { role: "system", content: "You are a helpful learning buddy. Keep all responses to TWO SHORT SENTENCES maximum (under 40 words total). Be concise, friendly, and encouraging." },
                        { role: "user", content: userText }
                    ],
                    user_id: user.email,
                    session_id: activeSessionId ? parseInt(activeSessionId) : null,
                    context: null
                }),
            })

            if (!response.ok) {
                if (response.status === 429) {
                    const errorData = await response.json().catch(() => ({}))
                    const waitTime = errorData.retry_after || 60
                    const message = `I need a short breather! Let's continue in about ${waitTime} seconds.`
                    setLastResponse(message)
                    speak(message)
                    setEmotion("confused")
                    isProcessingRef.current = false
                    return
                }
                throw new Error("Failed to fetch")
            }

            const data = await response.json()
            const responseText = data.content || "I'm not sure how to respond to that."

            setLastResponse(responseText)
            refreshStats()

            // Speak the response
            speak(responseText)
            setEmotion("happy")

            // After a brief moment, transition to speaking
            setTimeout(() => {
                if (!synthRef.current?.speaking) {
                    setEmotion("idle")
                }
            }, 1000)

        } catch (error) {
            console.error('Error processing speech:', error)
            const errorMessage = "Oops, I'm having trouble thinking right now. Can you try again?"
            setLastResponse(errorMessage)
            speak(errorMessage)
            setEmotion("confused")
            isProcessingRef.current = false

            // Resume listening after error
            if (autoListenEnabledRef.current) {
                setTimeout(() => {
                    if (autoListenEnabledRef.current) {
                        startListening()
                    }
                }, 2000)
            }
        }
    }

    const getEyeStyle = () => {
        switch (emotion) {
            case "listening":
                return "listening"
            case "thinking":
                return "thinking"
            case "speaking":
                return "speaking"
            case "happy":
                return "happy"
            case "confused":
                return "confused"
            default:
                return "idle"
        }
    }

    return (
        <div className="flex flex-col items-center justify-center h-full space-y-6 p-8">
            {/* Buddy Avatar */}
            <div className="relative">
                {/* Particle Effects */}
                <div className="buddy-particles">
                    {[...Array(20)].map((_, i) => (
                        <div key={i} className="particle" style={{
                            animationDelay: `${i * 0.2}s`,
                            left: `${Math.random() * 100}%`,
                            animationDuration: `${2 + Math.random() * 3}s`
                        }} />
                    ))}
                </div>

                {/* Main Avatar Circle */}
                <div className={`buddy-avatar ${emotion}`}>
                    {/* Gradient Overlay */}
                    <div className="buddy-gradient" />

                    {/* Eyes Container */}
                    <div className="buddy-eyes">
                        <div className={`buddy-eye left ${getEyeStyle()}`} />
                        <div className={`buddy-eye right ${getEyeStyle()}`} />
                    </div>

                    {/* Listening Indicator */}
                    {isListening && (
                        <div className="listening-pulse" />
                    )}
                </div>
            </div>

            {/* Status Text */}
            <div className="text-center space-y-2">
                <h3 className="text-2xl font-bold text-foreground">
                    {stats.buddyName || "Buddy"}
                </h3>
                <p className="text-sm text-muted-foreground font-medium">
                    {isListening ? "🎤 Listening..." :
                        emotion === "thinking" ? "🤔 Thinking..." :
                            emotion === "speaking" ? "💬 Speaking..." :
                                autoListenEnabledRef.current ? "👂 Ready to listen" : "😊 Press mic to talk"}
                </p>
            </div>

            {/* Transcript Display - Hidden for cleaner voice-only interface */}

            {/* Controls - Hidden, auto-listen always on */}
            <div className="hidden">
                <Button
                    size="lg"
                    variant={autoListenEnabledRef.current ? "default" : "outline"}
                    onClick={toggleListening}
                    className={`rounded-full ${autoListenEnabledRef.current && isListening ? 'animate-pulse' : ''}`}
                >
                    {autoListenEnabledRef.current ? (
                        <>
                            <Mic className="h-5 w-5 mr-2" />
                            Stop Listening
                        </>
                    ) : (
                        <>
                            <MicOff className="h-5 w-5 mr-2" />
                            Start Listening
                        </>
                    )}
                </Button>

                <Button
                    size="lg"
                    variant="outline"
                    onClick={() => setAudioEnabled(!audioEnabled)}
                    className="rounded-full"
                >
                    {audioEnabled ? (
                        <Volume2 className="h-5 w-5" />
                    ) : (
                        <VolumeX className="h-5 w-5" />
                    )}
                </Button>
            </div>

            {/* Helper Text */}
            <p className="text-xs text-muted-foreground text-center max-w-md">
                {stats.buddyName} is listening and ready to help you learn!
            </p>
        </div>
    )
}
