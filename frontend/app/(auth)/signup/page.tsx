"use client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import Link from "next/link"
import { useAuth } from "@/context/auth-context"
import { useState } from "react"

export default function SignupPage() {
    const { signup } = useAuth()
    const [firstName, setFirstName] = useState("")
    const [lastName, setLastName] = useState("")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [isSubmitting, setIsSubmitting] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (password !== confirmPassword) {
            alert("Passwords do not match!")
            return
        }
        setIsSubmitting(true)
        const fullName = `${firstName} ${lastName}`.trim()
        const success = await signup(email, password, fullName)
        if (!success) {
            alert("Signup failed! Please try again.")
            setIsSubmitting(false)
        }
        // If success, redirect happens in signup -> login, so we don't need to unset submitting
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
            <Card className="w-full max-w-md border-slate-800 bg-slate-900 text-slate-50">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
                        Create an Account
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        Join LearnLoop to start teaching your AI Buddy
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Input
                                    id="first-name"
                                    placeholder="First Name"
                                    className="bg-slate-800 border-slate-700"
                                    value={firstName}
                                    onChange={(e) => setFirstName(e.target.value)}
                                    required
                                    disabled={isSubmitting}
                                />
                            </div>
                            <div className="space-y-2">
                                <Input
                                    id="last-name"
                                    placeholder="Last Name"
                                    className="bg-slate-800 border-slate-700"
                                    value={lastName}
                                    onChange={(e) => setLastName(e.target.value)}
                                    required
                                    disabled={isSubmitting}
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Input
                                id="email"
                                placeholder="Email"
                                type="email"
                                className="bg-slate-800 border-slate-700"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isSubmitting}
                            />
                        </div>
                        <div className="space-y-2">
                            <Input
                                id="password"
                                placeholder="Password"
                                type="password"
                                className="bg-slate-800 border-slate-700"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                disabled={isSubmitting}
                            />
                        </div>
                        <div className="space-y-2">
                            <Input
                                id="confirm-password"
                                placeholder="Confirm Password"
                                type="password"
                                className="bg-slate-800 border-slate-700"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                                disabled={isSubmitting}
                            />
                        </div>

                        <Button type="submit" disabled={isSubmitting} className="w-full bg-indigo-600 hover:bg-indigo-700 bg-gradient-to-r from-indigo-600 to-purple-600">
                            {isSubmitting ? "Creating Account..." : "Sign Up"}
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex justify-center text-sm text-slate-400">
                    Already have an account?
                    <Link href="/login" className="text-indigo-400 hover:underline ml-1">Sign in</Link>
                </CardFooter>
            </Card>
        </div>
    )
}
