"use client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import Link from "next/link"
import { useAuth } from "@/context/auth-context"
import { useState } from "react"

export default function LoginPage() {
    const { login } = useAuth()
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        const result = await login(email, password)
        if (!result.success) {
            alert(result.error || "Login failed! Please check your credentials.")
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
            <Card className="w-full max-w-md border-slate-800 bg-slate-900 text-slate-50">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
                        LearnLoop 2.0
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        Enter your email to sign in to your account
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Input
                                id="email"
                                placeholder="m@example.com"
                                type="email"
                                className="bg-slate-800 border-slate-700"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
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
                            />
                        </div>
                        <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700">Sign In</Button>
                    </form>
                </CardContent>
                <CardFooter className="flex justify-center text-sm text-slate-400">
                    Don't have an account?
                    <Link href="/signup" className="text-indigo-400 hover:underline ml-1">Sign up</Link>
                </CardFooter>
            </Card>
        </div>
    )
}
