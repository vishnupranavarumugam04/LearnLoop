"use client"

import React, { createContext, useContext, useState, ReactNode, useCallback } from "react"

export interface Notification {
    id: string
    title: string
    message: string
    type: 'info' | 'success' | 'warning'
    timestamp: number
}

interface NotificationContextType {
    notifications: Notification[]
    unreadCount: number
    showPopup: Notification | null
    addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void
    removeNotification: (id: string) => void
    clearNotifications: () => void
    clearUnread: () => void
    dismissPopup: () => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function NotificationProvider({ children }: { children: ReactNode }) {
    const [notifications, setNotifications] = useState<Notification[]>([])
    const [unreadCount, setUnreadCount] = useState(0)
    const [showPopup, setShowPopup] = useState<Notification | null>(null)

    const addNotification = useCallback((data: Omit<Notification, 'id' | 'timestamp'>) => {
        const newNotification: Notification = {
            ...data,
            id: Math.random().toString(36).substr(2, 9),
            timestamp: Date.now()
        }

        setNotifications(prev => [newNotification, ...prev])
        setUnreadCount(prev => prev + 1)
        setShowPopup(newNotification)

        // Auto-hide popup after 5 seconds
        setTimeout(() => {
            setShowPopup(current => current?.id === newNotification.id ? null : current)
        }, 5000)
    }, [])

    const removeNotification = useCallback((id: string) => {
        setNotifications(prev => prev.filter(n => n.id !== id))
        if (showPopup?.id === id) setShowPopup(null)
    }, [showPopup])

    const clearNotifications = useCallback(() => {
        setNotifications([])
        setUnreadCount(0)
        setShowPopup(null)
    }, [])

    const clearUnread = useCallback(() => {
        setUnreadCount(0)
    }, [])

    const dismissPopup = useCallback(() => {
        setShowPopup(null)
    }, [])

    return (
        <NotificationContext.Provider value={{
            notifications,
            unreadCount,
            showPopup,
            addNotification,
            removeNotification,
            clearNotifications,
            clearUnread,
            dismissPopup
        }}>
            {children}
        </NotificationContext.Provider>
    )
}

export const useNotifications = () => {
    const context = useContext(NotificationContext)
    if (!context) {
        throw new Error("useNotifications must be used within a NotificationProvider")
    }
    return context
}
