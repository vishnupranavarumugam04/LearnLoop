"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Moon, Bell, Loader2 } from "lucide-react"
import { useAuth } from "@/context/auth-context"
import { useTheme } from "@/context/theme-context"
import { useNotifications } from "@/context/notification-context"
import { useState, useEffect } from "react"

export default function SettingsPage() {
    const { user } = useAuth()
    const { theme, setTheme, setHighContrast } = useTheme()
    const { addNotification } = useNotifications()
    const [settings, setSettings] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    // Fetch Settings
    useEffect(() => {
        if (!user) return
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/profile/${encodeURIComponent(user.name)}`)
            .then(res => res.json())
            .then(data => {
                setSettings(data.settings)
                setLoading(false)
            })
            .catch(err => setLoading(false))
    }, [user])

    const updateSetting = async (key: string, value: boolean) => {
        // Optimistic update for local state
        const newSettings = { ...settings, [key]: value }
        setSettings(newSettings)

        // Special handler for Dark Mode and High Contrast to apply immediately
        if (key === 'dark_mode') {
            setTheme(value ? 'dark' : 'light')
        } else if (key === 'high_contrast') {
            setHighContrast(value)
        } else if (key === 'notifications_study' && value === true) {
            addNotification({
                title: "Study Reminders Enabled 📚",
                message: "You will now receive daily nudges to help you stay on track!",
                type: 'success'
            })
        }

        if (!user) return

        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/profile/${encodeURIComponent(user.name)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    settings: { [key]: value }
                })
            })
        } catch (e) {
            console.error("Failed to save setting")
        }
    }

    if (!user) return <div className="p-8 text-center text-slate-400">Please log in.</div>
    if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin h-8 w-8 text-indigo-500" /></div>

    return (
        <div className="p-6 max-w-3xl mx-auto space-y-6">
            <h1 className="text-3xl font-bold">App Settings</h1>

            <div className="space-y-6">
                <Card className="bg-card border-border">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Moon className="h-5 w-5 text-indigo-400" /> Appearance
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="font-medium">Dark Mode</div>
                                <div className="text-sm text-slate-400">Switch between dark and light themes</div>
                            </div>
                            <Switch
                                checked={settings?.dark_mode ?? true}
                                onCheckedChange={(val) => updateSetting('dark_mode', val)}
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="font-medium">High Contrast</div>
                                <div className="text-sm text-slate-400">Increase visual accessibility</div>
                            </div>
                            <Switch
                                checked={settings?.high_contrast ?? false}
                                onCheckedChange={(val) => updateSetting('high_contrast', val)}
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-card border-border">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Bell className="h-5 w-5 text-indigo-400" /> Notifications
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="font-medium">Study Reminders</div>
                                <div className="text-sm text-slate-400">Daily nudges to keep your streak</div>
                            </div>
                            <Switch
                                checked={settings?.notifications_study ?? true}
                                onCheckedChange={(val) => updateSetting('notifications_study', val)}
                            />
                        </div>
                    </CardContent>
                </Card>

            </div>
        </div>
    )
}
