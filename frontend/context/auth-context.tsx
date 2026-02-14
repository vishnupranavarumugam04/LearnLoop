"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"

// --- Configuration ---
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

// --- Types ---
interface User {
    id: number
    name: string
    email: string
    level: number
    role: string
    token?: string
}

interface AuthContextType {
    user: User | null
    login: (email: string, password: string, name?: string) => Promise<{ success: boolean; error?: string }>
    signup: (email: string, password: string, name: string) => Promise<boolean>
    logout: () => void
    isLoading: boolean
    error: string | null
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    login: async () => ({ success: false }),
    signup: async () => false,
    logout: () => { },
    isLoading: true,
    error: null
})

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const router = useRouter()

    useEffect(() => {
        // Check local storage on mount
        const storedUser = localStorage.getItem("learnloop_user")
        if (storedUser) {
            setUser(JSON.parse(storedUser))
        }
        setIsLoading(false)
    }, [])

    const login = async (email: string, password: string, name?: string) => {
        setIsLoading(true)
        setError(null)
        try {
            // FastAPI OAuth2PasswordRequestForm expects form data, not JSON
            const formData = new FormData()
            formData.append('username', email) // Using email as username
            formData.append('password', password)

            const res = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                let errorMessage = "Login failed"
                try {
                    const errorData = await res.json()
                    errorMessage = errorData.detail || errorMessage
                } catch (e) { }
                throw new Error(errorMessage)
            }

            const data = await res.json()
            // data = { access_token, token_type }

            // Store token
            localStorage.setItem('token', data.access_token)

            // Simplification: In a real app we would decode the token or call /me
            // For MVP, we construct the user object from input + token
            // Ideally we should call GET /users/me here

            const loggedInUser: User = {
                id: 1, // Mock ID or extract from token if possible without library
                name: name || email.split('@')[0],
                email: email,
                level: 1,
                role: "Scholar",
                token: data.access_token
            }

            // Try to fetch real profile name
            try {
                const profileRes = await fetch(`${API_BASE_URL}/profile/${encodeURIComponent(email)}`)
                if (profileRes.ok) {
                    const profile = await profileRes.json()
                    loggedInUser.name = profile.user_name || loggedInUser.name
                    loggedInUser.level = profile.level || 1
                }
            } catch (e) {
                console.warn("Could not fetch profile", e)
            }

            setUser(loggedInUser)
            localStorage.setItem("learnloop_user", JSON.stringify(loggedInUser))
            router.push("/")
            return { success: true }

        } catch (err: any) {
            const msg = err.message || "Login failed"
            setError(msg)
            return { success: false, error: msg }
        } finally {
            setIsLoading(false)
        }
    }

    const signup = async (email: string, password: string, name: string) => {
        setIsLoading(true)
        setError(null)
        try {
            const res = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: email,
                    password: password,
                    full_name: name
                }),
            })

            if (!res.ok) {
                let errorMessage = "Signup failed"
                try {
                    const errorData = await res.json()
                    errorMessage = errorData.detail || errorMessage
                } catch (e) { }
                throw new Error(errorMessage)
            }

            // After successful signup, auto-login
            await login(email, password, name)
            return true

        } catch (err: any) {
            setError(err.message)
            return false
        } finally {
            setIsLoading(false)
        }
    }

    const logout = () => {
        setUser(null)
        localStorage.removeItem("learnloop_user")
        localStorage.removeItem("token")
        router.push("/login")
    }

    return (
        <AuthContext.Provider value={{ user, login, signup, logout, isLoading, error }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => useContext(AuthContext)
