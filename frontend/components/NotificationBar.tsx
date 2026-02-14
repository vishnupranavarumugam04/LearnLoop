"use client"

import React, { useState, useEffect } from "react"
import { Bell, X, Info } from "lucide-react"
import { io, Socket } from "socket.io-client"
import { useAuth } from "@/context/auth-context"
import { useNotifications } from "@/context/notification-context"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"

export function NotificationBar() {
    const { user } = useAuth()
    const {
        notifications,
        unreadCount,
        showPopup,
        addNotification,
        removeNotification,
        clearNotifications,
        clearUnread,
        dismissPopup
    } = useNotifications()
    const [socket, setSocket] = useState<Socket | null>(null)
    const [showList, setShowList] = useState(false)

    useEffect(() => {
        if (!user) return

        const newSocket = io(process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000', {
            transports: ['websocket', 'polling'],
            autoConnect: true,
            reconnection: true,
        })

        setSocket(newSocket)

        newSocket.on('connect', () => {
            newSocket.emit('user_connected', {
                user_id: user.id,
                username: user.name
            })
        })

        // Listen for generic notifications
        newSocket.on('new_notification', (data: any) => {
            addNotification({
                title: data.title || "New Notification",
                message: data.message || "You have a new alert.",
                type: data.type || 'info'
            })
        })

        // Listen for Battle Challenges
        newSocket.on('battle_challenge', (data: any) => {
            addNotification({
                title: "Battle Challenge! ⚔️",
                message: `${data.sender_name} has challenged you to a battle!`,
                type: 'warning'
            })
        })

        return () => {
            newSocket.disconnect()
        }
    }, [user, addNotification])


    return (
        <header className="fixed top-0 right-0 left-0 lg:left-64 h-16 bg-background/80 backdrop-blur-md border-b border-border z-40 flex items-center justify-between px-6">
            <div className="flex items-center gap-4">
                {/* Space for page-specific title if needed */}
                <h2 className="text-sm font-medium text-muted-foreground hidden md:block">
                    Learning Journey
                </h2>
            </div>

            <div className="flex items-center gap-4">
                {/* Notification Icon */}
                <div
                    className="relative cursor-pointer hover:bg-accent p-2 rounded-full transition-colors"
                    onClick={() => {
                        setShowList(!showList)
                        clearUnread()
                    }}
                >
                    <Bell className="h-5 w-5 text-foreground" />
                    {unreadCount > 0 && (
                        <span className="absolute top-1 right-1 h-4 w-4 bg-primary text-[10px] font-bold text-primary-foreground flex items-center justify-center rounded-full border-2 border-background">
                            {unreadCount}
                        </span>
                    )}
                </div>

                {/* Notification List Panel */}
                <AnimatePresence>
                    {showList && (
                        <>
                            <div className="fixed inset-0 z-40" onClick={() => setShowList(false)} />
                            <motion.div
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                className="absolute top-16 right-0 w-80 md:w-96 bg-card border border-border shadow-2xl rounded-2xl overflow-hidden z-50 flex flex-col max-h-[80vh]"
                            >
                                <div className="p-4 border-b border-border flex items-center justify-between bg-muted/30">
                                    <h3 className="font-bold text-sm">Notifications</h3>
                                    {notifications.length > 0 && (
                                        <button
                                            onClick={clearNotifications}
                                            className="text-[10px] uppercase tracking-wider font-bold text-primary hover:text-primary/80 transition-colors"
                                        >
                                            Clear All
                                        </button>
                                    )}
                                </div>
                                <div className="overflow-y-auto flex-1">
                                    {notifications.length === 0 ? (
                                        <div className="p-8 text-center text-muted-foreground">
                                            <Bell className="h-8 w-8 mx-auto mb-2 opacity-20" />
                                            <p className="text-xs">No notifications yet</p>
                                        </div>
                                    ) : (
                                        <div className="divide-y divide-border">
                                            {notifications.map((n) => (
                                                <div key={n.id} className="p-4 hover:bg-accent/50 transition-colors group relative">
                                                    <div className="flex gap-3">
                                                        <div className={cn(
                                                            "h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0",
                                                            n.type === 'success' ? "bg-green-500/10 text-green-500" :
                                                                n.type === 'warning' ? "bg-yellow-500/10 text-yellow-500" : "bg-indigo-500/10 text-indigo-500"
                                                        )}>
                                                            <Info className="h-4 w-4" />
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center justify-between gap-2">
                                                                <p className="text-sm font-semibold truncate">{n.title}</p>
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation()
                                                                        removeNotification(n.id)
                                                                    }}
                                                                    className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                                                                >
                                                                    <X className="h-3 w-3" />
                                                                </button>
                                                            </div>
                                                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{n.message}</p>
                                                            <p className="text-[10px] text-muted-foreground/60 mt-1">
                                                                {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>

                {/* User Profile Info (Minimal) */}
                <div className="flex items-center gap-3 pl-4 border-l border-border">
                    <div className="text-right hidden sm:block">
                        <div className="text-sm font-semibold">{user?.name}</div>
                        <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Active Now</div>
                    </div>
                    <div className="h-8 w-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-xs">
                        {user?.name?.charAt(0) || 'U'}
                    </div>
                </div>
            </div>

            {/* Notification Popup (Toast) */}
            <AnimatePresence>
                {showPopup && (
                    <motion.div
                        initial={{ opacity: 0, y: -50, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="fixed top-20 right-6 z-50 w-80 shadow-2xl rounded-xl border border-border bg-card overflow-hidden"
                    >
                        <div className={cn(
                            "h-1 w-full",
                            showPopup.type === 'success' ? "bg-green-500" :
                                showPopup.type === 'warning' ? "bg-yellow-500" : "bg-indigo-500"
                        )} />
                        <div className="p-4 flex gap-3">
                            <div className={cn(
                                "flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center",
                                showPopup.type === 'success' ? "bg-green-500/10 text-green-500" :
                                    showPopup.type === 'warning' ? "bg-yellow-500/10 text-yellow-500" : "bg-indigo-500/10 text-indigo-500"
                            )}>
                                <Info className="h-5 w-5" />
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center justify-between">
                                    <h3 className="font-bold text-sm">{showPopup.title}</h3>
                                    <button onClick={() => removeNotification(showPopup.id)} className="text-muted-foreground hover:text-foreground">
                                        <X className="h-4 w-4" />
                                    </button>
                                </div>
                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                    {showPopup.message}
                                </p>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </header>
    )
}
