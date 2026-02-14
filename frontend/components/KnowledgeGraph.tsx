"use client"

import * as React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

import { useAuth } from "@/context/auth-context"

interface KnowledgeGraphProps {
    className?: string
}

export function KnowledgeGraph({ className }: KnowledgeGraphProps) {
    const { user } = useAuth()
    const [nodes, setNodes] = React.useState<any[]>([])
    const [stats, setStats] = React.useState<any>(null)

    React.useEffect(() => {
        const fetchGraph = async () => {
            if (!user?.email) return
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/graph/?username=${encodeURIComponent(user.email)}`)
                if (res.ok) {
                    const data = await res.json()
                    setNodes(data.nodes || [])
                    setStats(data.mastery_summary)
                }
            } catch (e) {
                console.error("Graph fetch error", e)
            }
        }
        fetchGraph()
    }, [user?.email])

    return (
        <Card className={cn("h-[300px] w-full overflow-hidden relative border-border shadow-sm group", className)}>
            <CardHeader className="absolute top-0 left-0 z-10 w-full pointer-events-none flex justify-between">
                <CardTitle className="text-lg text-foreground/80">Knowledge Map</CardTitle>
                {stats && (
                    <div className="text-xs text-muted-foreground pr-4">
                        Mastered: {stats.mastered} | Learning: {stats.learning}
                    </div>
                )}
            </CardHeader>

            <div className="relative w-full h-full flex items-center justify-center bg-background perspective-1000">
                <motion.svg
                    className="w-full h-full"
                    viewBox="0 0 200 200"
                    initial={{ rotateX: 0 }}
                    animate={{ rotateX: [0, 5, 0, -5, 0], rotateY: [0, 5, 0, -5, 0] }}
                    transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                >
                    <defs>
                        <radialGradient id="sphereGradient" cx="30%" cy="30%" r="70%">
                            <stop offset="0%" stopColor="#d8b4fe" /> {/* lighter purple */}
                            <stop offset="50%" stopColor="#9333ea" /> {/* purple-600 */}
                            <stop offset="100%" stopColor="#581c87" /> {/* purple-900 */}
                        </radialGradient>
                        <filter id="glow">
                            <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                        <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" floodOpacity="0.2" />
                        </filter>
                    </defs>

                    {/* Connecting Lines (Orbit) with 3D Depth - Improved visibility */}
                    <ellipse cx="100" cy="100" rx="70" ry="30" fill="none" stroke="currentColor" className="text-primary/40" strokeWidth="0.5" strokeDasharray="4 4" />
                    <ellipse cx="100" cy="100" rx="90" ry="40" fill="none" stroke="currentColor" className="text-primary/20" strokeWidth="0.5" />

                    {/* Render Learned Nodes with simulated Z-depth */}
                    {nodes.map((node, i) => {
                        const angle = (i / (nodes.length || 1)) * 2 * Math.PI + (Date.now() / 10000);
                        const radiusX = 70 + (i % 2) * 15;
                        const radiusY = 30 + (i % 2) * 10;
                        const cx = 100 + Math.cos(angle) * radiusX;
                        const cy = 100 + Math.sin(angle) * radiusY;

                        // Simulated Z-depth based on Y position (sin of angle)
                        const zScale = 0.7 + (Math.sin(angle) + 1) * 0.3; // 0.7 to 1.3
                        const opacity = 0.4 + (Math.sin(angle) + 1) * 0.3; // 0.4 to 1.0

                        return (
                            <motion.g
                                key={i}
                                className="cursor-pointer"
                                whileHover={{ scale: 1.2 }}
                                animate={{
                                    x: [0, Math.random() * 2, 0],
                                    y: [0, Math.random() * 2, 0]
                                }}
                                transition={{ duration: 3, repeat: Infinity }}
                            >
                                <circle
                                    cx={cx}
                                    cy={cy}
                                    r={(node.status === 'mastered' ? 5 : 3) * zScale}
                                    fill={node.color}
                                    style={{ opacity }}
                                    filter="url(#shadow)"
                                />
                                {nodes.length < 15 && opacity > 0.7 && (
                                    <text x={cx} y={cy + 10} fontSize="4" fill="currentColor" className="text-foreground font-medium" textAnchor="middle" style={{ opacity }}>
                                        {node.label}
                                    </text>
                                )}
                            </motion.g>
                        )
                    })}

                    {/* Central 3D Sphere (User/Core) */}
                    <motion.g
                        className="cursor-pointer"
                        whileHover={{ scale: 1.1 }}
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    >
                        <circle cx="100" cy="100" r="22" fill="url(#sphereGradient)" filter="url(#glow)" />
                        <text x="100" y="138" fontSize="6" textAnchor="middle" fill="currentColor" className="text-primary font-bold tracking-widest uppercase">
                            YOU
                        </text>
                    </motion.g>
                </motion.svg>
            </div>
        </Card>
    )
}
