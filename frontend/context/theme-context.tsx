"use client"

import { createContext, useContext, useEffect, useState, ReactNode } from "react"
import { useAuth } from "./auth-context"

type Theme = "dark" | "light"

interface ThemeContextType {
    theme: Theme
    highContrast: boolean
    setTheme: (theme: Theme) => void
    setHighContrast: (enabled: boolean) => void
    toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType>({
    theme: "light",
    highContrast: false,
    setTheme: () => { },
    setHighContrast: () => { },
    toggleTheme: () => { },
})

export function ThemeProvider({ children }: { children: ReactNode }) {
    const { user } = useAuth()
    const [theme, setThemeState] = useState<Theme>("light")
    const [highContrast, setHighContrastState] = useState<boolean>(false)

    // Apply theme and high contrast to DOM
    useEffect(() => {
        const root = window.document.documentElement
        root.classList.remove("light", "dark")
        root.classList.add(theme)

        if (highContrast) {
            root.classList.add("high-contrast")
        } else {
            root.classList.remove("high-contrast")
        }
    }, [theme, highContrast])

    // Sync with User Settings from Backend
    useEffect(() => {
        if (user) {
            fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/profile/${encodeURIComponent(user.name)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.settings) {
                        if (data.settings.dark_mode !== undefined) {
                            setThemeState(data.settings.dark_mode ? "dark" : "light")
                        }
                        if (data.settings.high_contrast !== undefined) {
                            setHighContrastState(data.settings.high_contrast)
                        }
                    }
                })
                .catch(console.error)
        }
    }, [user])

    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme)
    }

    const setHighContrast = (enabled: boolean) => {
        setHighContrastState(enabled)
    }

    const toggleTheme = () => {
        setThemeState(prev => prev === "dark" ? "light" : "dark")
    }

    return (
        <ThemeContext.Provider value={{ theme, highContrast, setTheme, setHighContrast, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    )
}

export const useTheme = () => useContext(ThemeContext)
