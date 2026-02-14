"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { User, Mail, Shield, Zap, Trophy, Medal, Flame, Calendar, PenTool, Loader2, X, AlertTriangle } from "lucide-react"
import { useAuth } from "@/context/auth-context"
import { useStats } from "@/context/stats-context"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

interface UserProfile {
    user_name: string
    level: number
    total_xp: number
    streak_days: number
    global_rank_percent: number
    role: string
    bio: string
    university: string
    subjects: { [key: string]: number }
    badges: string[]
    created_at?: string
}

export default function ProfilePage() {
    const { user, logout } = useAuth()
    const { stats: globalStats } = useStats()
    const router = useRouter()
    const [profile, setProfile] = useState<UserProfile | null>(null)
    const [loading, setLoading] = useState(true)

    // UI State
    const [isEditing, setIsEditing] = useState(false)
    const [editBio, setEditBio] = useState("")
    const [editUniversity, setEditUniversity] = useState("")
    const [isDeleting, setIsDeleting] = useState(false)

    // Password Change State
    const [isChangingPassword, setIsChangingPassword] = useState(false)
    const [oldPassword, setOldPassword] = useState("")
    const [newPassword, setNewPassword] = useState("")

    useEffect(() => {
        if (user) {
            fetchProfiles()
        }
    }, [user])

    const fetchProfiles = () => {
        if (!user) return
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/profile/${encodeURIComponent(user.email)}`)
            .then(res => res.json())
            .then(data => {
                setProfile(data)
                setEditBio(data.bio)
                setEditUniversity(data.university)
                setLoading(false)
            })
            .catch(err => {
                console.error(err)
                setLoading(false)
            })
    }

    const handleChangePassword = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/change-password`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    username: user?.email,
                    old_password: oldPassword,
                    new_password: newPassword
                })
            })
            if (res.ok) {
                alert("Password changed successfully!")
                setIsChangingPassword(false)
                setOldPassword("")
                setNewPassword("")
            } else {
                alert("Failed to change password.")
            }
        } catch (e) {
            console.error(e)
            alert("Error changing password")
        }
    }

    const handleSaveProfile = async () => {
        if (!user) return
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/profile/${user.email}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bio: editBio,
                    university: editUniversity
                })
            })
            if (res.ok) {
                const updated = await res.json()
                setProfile(updated)
                setIsEditing(false)
            }
        } catch (e) {
            alert("Failed to update profile")
        }
    }

    const handleShare = () => {
        navigator.clipboard.writeText(window.location.href)
        alert("Profile link copied to clipboard!")
    }

    const handleDeleteAccount = async () => {
        if (!user) return
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/users/me?username=${user.email}`, {
                method: "DELETE"
            })

            if (res.ok) {
                alert("Account deleted securely.")
                logout()
                router.push('/')
            } else {
                alert("Failed to delete account")
            }
        } catch (e) {
            console.error(e)
            alert("Error deleting account")
        }
    }

    if (!user) return <div className="p-8 text-center text-muted-foreground">Please log in to view profile.</div>
    if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin h-8 w-8 text-indigo-500" /></div>
    if (!profile) return <div className="p-8 text-center text-muted-foreground">Error loading profile.</div>

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-8 relative">

            {/* Edit Modal */}
            {isEditing && (
                <div className="fixed inset-0 bg-background/80 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                    <Card className="w-full max-w-md bg-card border-border shadow-xl">
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle>Edit Profile</CardTitle>
                            <Button variant="ghost" size="icon" onClick={() => setIsEditing(false)}>
                                <X className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">University / School</label>
                                <Input
                                    value={editUniversity}
                                    onChange={(e) => setEditUniversity(e.target.value)}
                                    className="bg-background border-input"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Bio</label>
                                <Input
                                    value={editBio}
                                    onChange={(e) => setEditBio(e.target.value)}
                                    className="bg-background border-input"
                                />
                            </div>
                            <Button className="w-full bg-indigo-600 hover:bg-indigo-700 mt-2" onClick={handleSaveProfile}>
                                Save Changes
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Change Password Modal */}
            {isChangingPassword && (
                <div className="fixed inset-0 bg-background/80 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                    <Card className="w-full max-w-md bg-card border-border shadow-xl">
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle>Change Password</CardTitle>
                            <Button variant="ghost" size="icon" onClick={() => setIsChangingPassword(false)}>
                                <X className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Current Password</label>
                                <Input
                                    type="password"
                                    value={oldPassword}
                                    onChange={(e) => setOldPassword(e.target.value)}
                                    className="bg-background border-input"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">New Password</label>
                                <Input
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="bg-background border-input"
                                />
                            </div>
                            <Button className="w-full bg-indigo-600 hover:bg-indigo-700 mt-2" onClick={handleChangePassword}>
                                Update Password
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {isDeleting && (
                <div className="fixed inset-0 bg-background/80 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                    <Card className="w-full max-w-md bg-card border-red-500/50 shadow-xl">
                        <CardHeader>
                            <CardTitle className="text-red-500 flex items-center gap-2">
                                <AlertTriangle className="h-5 w-5" /> Delete Account?
                            </CardTitle>
                            <CardDescription>
                                This action cannot be undone. All your progress will be lost.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4 pt-4">
                            <div className="flex gap-3">
                                <Button variant="outline" className="flex-1" onClick={() => setIsDeleting(false)}>Cancel</Button>
                                <Button variant="destructive" className="flex-1" onClick={handleDeleteAccount}>Delete Permanently</Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Header Profile Card */}
            <Card className="bg-gradient-to-r from-card to-secondary border-border">
                <CardContent className="p-8 flex flex-col md:flex-row gap-8 items-center md:items-start">
                    <div className="relative">
                        <div className="w-32 h-32 rounded-full bg-indigo-500 flex items-center justify-center text-4xl font-bold text-white border-4 border-background shadow-xl uppercase">
                            {user.name.charAt(0)}
                        </div>
                        <div className="absolute bottom-0 right-0 bg-yellow-500 text-slate-900 text-xs font-bold px-2 py-1 rounded-full border border-background">
                            LVL {globalStats.level}
                        </div>
                    </div>

                    <div className="flex-1 space-y-4 text-center md:text-left">
                        <div>
                            <h1 className="text-3xl font-bold text-primary">{user.name}</h1>
                            <p className="text-muted-foreground">{profile.role} • Joined {profile.created_at ? new Date(profile.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : 'Recently'}</p>
                        </div>

                        <div className="flex flex-wrap gap-4 justify-center md:justify-start">
                            <div className="bg-background/50 px-4 py-2 rounded-lg border border-border flex items-center gap-2">
                                <Flame className="text-orange-500 h-5 w-5" />
                                <div>
                                    <div className="text-lg font-bold">{globalStats.streak_days}</div>
                                    <div className="text-xs text-muted-foreground">Day Streak</div>
                                </div>
                            </div>
                            <div className="bg-background/50 px-4 py-2 rounded-lg border border-border flex items-center gap-2">
                                <Zap className="text-yellow-400 h-5 w-5" />
                                <div>
                                    <div className="text-lg font-bold">{globalStats.total_xp}</div>
                                    <div className="text-xs text-muted-foreground">Total XP</div>
                                </div>
                            </div>
                            <div className="bg-background/50 px-4 py-2 rounded-lg border border-border flex items-center gap-2">
                                <Trophy className="text-purple-400 h-5 w-5" />
                                <div>
                                    <div className="text-lg font-bold">Top {profile.global_rank_percent}%</div>
                                    <div className="text-xs text-muted-foreground">Global Rank</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col gap-2">
                        <Button variant="outline" className="border-border hover:bg-secondary" onClick={() => setIsEditing(true)}>Edit Profile</Button>
                        <Button variant="ghost" className="text-muted-foreground hover:text-primary" onClick={handleShare}>Share Profile</Button>
                    </div>
                </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left: Stats & Details */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Account Details */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <User className="h-5 w-5 text-indigo-400" />
                                Personal Information
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm text-muted-foreground">Full Name</label>
                                    <Input value={user.name} className="bg-background border-input" readOnly />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm text-muted-foreground">Email</label>
                                    <Input value={user.email} className="bg-background border-input" readOnly />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm text-muted-foreground">University</label>
                                    <Input value={profile.university} className="bg-background border-input" readOnly />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm text-muted-foreground">Bio</label>
                                    <Input value={profile.bio} className="bg-background border-input" readOnly />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Subject Progress */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Medal className="h-5 w-5 text-emerald-400" />
                                Subject Mastery
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            {Object.entries(profile.subjects).length === 0 ? (
                                <div className="text-center py-6 text-muted-foreground">
                                    <p>No subjects started yet.</p>
                                    <p className="text-xs mt-1">Chat with your Buddy to gain experience!</p>
                                </div>
                            ) : (
                                Object.entries(profile.subjects).map(([subject, level]) => (
                                    <div key={subject} className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span className="font-medium">{subject}</span>
                                            <span className="text-emerald-400">Level {level}</span>
                                        </div>
                                        <Progress value={Math.min(level * 10, 100)} className="h-2 bg-secondary" />
                                    </div>
                                ))
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Right: Achievements & Settings */}
                <div className="space-y-8">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Trophy className="h-5 w-5 text-yellow-400" />
                                Recent Badges
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="grid grid-cols-3 gap-2">
                            {profile.badges.map((badge, idx) => (
                                <div key={idx} className="bg-secondary p-2 rounded-lg border border-border flex flex-col items-center gap-1 text-center">
                                    <div className="h-8 w-8 rounded-full bg-yellow-500/20 text-yellow-500 flex items-center justify-center">🔥</div>
                                    <span className="text-[10px] font-bold">{badge}</span>
                                </div>
                            ))}
                            {profile.badges.length === 0 && <div className="text-xs text-muted-foreground col-span-3 text-center">No badges yet</div>}
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Shield className="h-5 w-5 text-red-400" />
                                Account Security
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            <Button variant="outline" className="w-full justify-between border-border hover:bg-secondary" onClick={() => setIsChangingPassword(true)}>
                                Change Password
                                <PenTool className="h-4 w-4" />
                            </Button>
                            <Button variant="outline" className="w-full justify-between border-border hover:bg-secondary" onClick={() => alert("Privacy settings helper unavailable in demo.")}>
                                Privacy Settings
                                <Shield className="h-4 w-4" />
                            </Button>
                            <Button variant="link" className="text-red-400 hover:text-red-300 p-0 h-auto" onClick={() => setIsDeleting(true)}>
                                Delete Account
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
