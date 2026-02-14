"use client"

import { useRef, useState, useEffect } from "react"
import { KnowledgeGraph } from "@/components/KnowledgeGraph"
import { Button } from "@/components/ui/button"
import { Maximize2, Minimize2 } from "lucide-react"

export default function GraphPage() {
    const containerRef = useRef<HTMLDivElement>(null)
    const [isFullscreen, setIsFullscreen] = useState(false)

    const toggleFullscreen = () => {
        if (!document.fullscreenElement) {
            containerRef.current?.requestFullscreen().then(() => {
                setIsFullscreen(true)
            }).catch(err => {
                console.error(`Error attempting to enable fullscreen: ${err.message}`)
            })
        } else {
            document.exitFullscreen()
            setIsFullscreen(false)
        }
    }

    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement)
        }

        document.addEventListener('fullscreenchange', handleFullscreenChange)
        return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }, [])

    return (
        <div className="p-6 h-[calc(100vh-4rem)] flex flex-col gap-6">
            <div className="flex justify-between items-center shrink-0">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">Knowledge Graph</h1>
                    <p className="text-slate-400">Interactive 3D visualization of your learning journey.</p>
                </div>
                <Button variant="outline" className="border-slate-700 hover:bg-slate-800" onClick={toggleFullscreen}>
                    {isFullscreen ? <Minimize2 className="mr-2 h-4 w-4" /> : <Maximize2 className="mr-2 h-4 w-4" />}
                    {isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                </Button>
            </div>

            <div
                ref={containerRef}
                className="flex-1 w-full min-h-0 bg-slate-900 overflow-hidden relative rounded-xl border border-slate-800 shadow-2xl"
            >
                <KnowledgeGraph className="w-full h-full border-0" />
            </div>
        </div>
    );
}
