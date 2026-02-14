"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useAuth } from "@/context/auth-context"
import { useStats } from "@/context/stats-context"
import { X, Sparkles } from "lucide-react"

const AVATARS = [
    { id: 'seedling', label: 'Seedling', icon: '🌱' },
    { id: 'sprout', label: 'Sprout', icon: '🌿' },
    { id: 'brain', label: 'Brainy', icon: '🧠' },
    { id: 'robot', label: 'Droid', icon: '🤖' },
    { id: 'sparkles', label: 'Magic', icon: '✨' },
    { id: 'rocket', label: 'Explorer', icon: '🚀' },
    { id: 'star', label: 'Achiever', icon: '⭐' },
    { id: 'ghost', label: 'Playful', icon: '👻' },
]

interface BuddyCustomizationModalProps {
    isOpen: boolean
    onClose: () => void
}

export function BuddyCustomizationModal({ isOpen, onClose }: BuddyCustomizationModalProps) {
    const { user } = useAuth()
    const { stats, refreshStats } = useStats()
    const [name, setName] = useState(stats.buddyName)
    const [selectedAvatar, setSelectedAvatar] = useState(stats.buddyAvatar)
    const [isSaving, setIsSaving] = useState(false)

    const handleSave = async () => {
        if (!user?.email) return
        setIsSaving(true)
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/profile/${encodeURIComponent(user.email)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    buddy_name: name,
                    buddy_avatar: selectedAvatar
                })
            })
            if (res.ok) {
                await refreshStats()
                onClose()
            }
        } catch (e) {
            console.error("Failed to save buddy customization", e)
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[450px] bg-card border border-border shadow-2xl rounded-[32px] overflow-hidden z-[51]"
                    >
                        <div className="p-6 sm:p-8 space-y-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                                        Customize Buddy <Sparkles className="h-5 w-5 text-yellow-500" />
                                    </h2>
                                    <p className="text-sm text-muted-foreground mt-1">Make your learning buddy truly yours.</p>
                                </div>
                                <button onClick={onClose} className="p-2 hover:bg-accent rounded-full transition-colors">
                                    <X className="h-5 w-5" />
                                </button>
                            </div>

                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] uppercase font-black tracking-[0.2em] opacity-50 ml-1">Buddy Name</label>
                                    <Input
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        placeholder="Enter buddy name..."
                                        className="h-12 bg-secondary/30 border-border/50 rounded-2xl font-bold focus:ring-primary/20 transition-all"
                                    />
                                </div>

                                <div className="space-y-3">
                                    <label className="text-[10px] uppercase font-black tracking-[0.2em] opacity-50 ml-1">Icon / Avatar</label>
                                    <div className="grid grid-cols-4 gap-3">
                                        {AVATARS.map((avatar) => (
                                            <button
                                                key={avatar.id}
                                                onClick={() => setSelectedAvatar(avatar.id)}
                                                className={`h-20 rounded-2xl border-2 flex flex-col items-center justify-center gap-1 transition-all duration-300 ${selectedAvatar === avatar.id
                                                    ? "border-primary bg-primary/10 shadow-lg shadow-primary/5 ring-4 ring-primary/5 scale-105"
                                                    : "border-border bg-secondary/20 grayscale hover:grayscale-0 hover:border-primary/30"
                                                    }`}
                                            >
                                                <span className="text-3xl">{avatar.icon}</span>
                                                <span className={`text-[9px] uppercase font-black tracking-widest ${selectedAvatar === avatar.id ? "text-primary" : "text-muted-foreground opacity-60"}`}>
                                                    {avatar.label}
                                                </span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-3 pt-2">
                                <Button variant="ghost" onClick={onClose} className="flex-1 h-12 rounded-2xl font-black uppercase tracking-widest text-xs">
                                    Cancel
                                </Button>
                                <Button
                                    onClick={handleSave}
                                    disabled={isSaving}
                                    className="flex-1 h-12 rounded-2xl font-black uppercase tracking-widest text-xs bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20"
                                >
                                    {isSaving ? "Saving..." : "Save Changes"}
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    )
}
