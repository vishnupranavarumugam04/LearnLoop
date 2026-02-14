"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, XCircle, AlertCircle, Loader2, Database, Zap, RefreshCw } from "lucide-react"
import { useState, useEffect } from "react"

interface HealthStatus {
    status: string
    gemini_configured: boolean
    gemini_working: boolean
    database_connected: boolean
    timestamp: string
    message: string
}

export default function APICheckPage() {
    const [health, setHealth] = useState<HealthStatus | null>(null)
    const [loading, setLoading] = useState(false)
    const [testKey, setTestKey] = useState("")
    const [testResult, setTestResult] = useState<any>(null)

    const checkHealth = async () => {
        setLoading(true)
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/health`.replace('/api/api/', '/api/'))
            const data = await res.json()
            setHealth(data)
        } catch (error) {
            setHealth({
                status: "error",
                gemini_configured: false,
                gemini_working: false,
                database_connected: false,
                timestamp: new Date().toISOString(),
                message: "Cannot connect to backend server"
            })
        }
        setLoading(false)
    }

    const testApiKey = async () => {
        if (!testKey.trim()) {
            alert("Please enter an API key")
            return
        }

        setLoading(true)
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/health/test-key`.replace('/api/api/', '/api/'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: testKey })
            })
            const data = await res.json()
            setTestResult(data)
        } catch (error) {
            setTestResult({
                status: "error",
                message: "Failed to test API key"
            })
        }
        setLoading(false)
    }

    useEffect(() => {
        checkHealth()
    }, [])

    const StatusIcon = ({ working }: { working: boolean }) => {
        if (working) return <CheckCircle2 className="h-5 w-5 text-green-500" />
        return <XCircle className="h-5 w-5 text-red-500" />
    }

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-6">
            <div>
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
                    API Health Check
                </h1>
                <p className="text-slate-400">Monitor backend services and test Gemini API</p>
            </div>

            {/* Overall Status */}
            <Card className="border-slate-800 bg-slate-900/50">
                <CardHeader>
                    <div className="flex justify-between items-center">
                        <CardTitle className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-yellow-500" />
                            System Status
                        </CardTitle>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={checkHealth}
                            disabled={loading}
                        >
                            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                            <span className="ml-2">Refresh</span>
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {health ? (
                        <>
                            <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <StatusIcon working={health.status === "healthy"} />
                                    <div>
                                        <div className="font-medium">Overall Status</div>
                                        <div className="text-sm text-slate-400">{health.message}</div>
                                    </div>
                                </div>
                                <Badge variant={health.status === "healthy" ? "default" : "destructive"}>
                                    {health.status.toUpperCase()}
                                </Badge>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700">
                                    <div className="flex items-center gap-2 mb-2">
                                        <StatusIcon working={health.gemini_configured} />
                                        <span className="font-medium">API Key</span>
                                    </div>
                                    <div className="text-sm text-slate-400">
                                        {health.gemini_configured ? "Configured" : "Missing"}
                                    </div>
                                </div>

                                <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700">
                                    <div className="flex items-center gap-2 mb-2">
                                        <StatusIcon working={health.gemini_working} />
                                        <span className="font-medium">Gemini API</span>
                                    </div>
                                    <div className="text-sm text-slate-400">
                                        {health.gemini_working ? "Working" : "Not responding"}
                                    </div>
                                </div>

                                <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700">
                                    <div className="flex items-center gap-2 mb-2">
                                        <StatusIcon working={health.database_connected} />
                                        <span className="font-medium">Database</span>
                                    </div>
                                    <div className="text-sm text-slate-400">
                                        {health.database_connected ? "Connected" : "Disconnected"}
                                    </div>
                                </div>
                            </div>

                            <div className="text-xs text-slate-500">
                                Last checked: {new Date(health.timestamp).toLocaleString()}
                            </div>
                        </>
                    ) : (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* API Key Tester */}
            <Card className="border-slate-800 bg-slate-900/50">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-blue-500" />
                        Test Gemini API Key
                    </CardTitle>
                    <CardDescription>
                        Test a new API key before updating your configuration
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex gap-2">
                        <Input
                            type="password"
                            placeholder="Enter Gemini API key..."
                            value={testKey}
                            onChange={(e) => setTestKey(e.target.value)}
                            className="bg-slate-800 border-slate-700"
                        />
                        <Button
                            onClick={testApiKey}
                            disabled={loading || !testKey.trim()}
                            className="bg-indigo-600 hover:bg-indigo-700"
                        >
                            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                            Test Key
                        </Button>
                    </div>

                    {testResult && (
                        <div className={`p-4 rounded-lg border ${testResult.status === "success"
                            ? "bg-green-500/10 border-green-500/30"
                            : "bg-red-500/10 border-red-500/30"
                            }`}>
                            <div className="flex items-center gap-2 mb-2">
                                {testResult.status === "success" ? (
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                ) : (
                                    <XCircle className="h-5 w-5 text-red-500" />
                                )}
                                <span className="font-medium">{testResult.message}</span>
                            </div>
                            {testResult.response && (
                                <div className="text-sm text-slate-400 mt-2">
                                    Response: {testResult.response}
                                </div>
                            )}
                        </div>
                    )}

                    <div className="text-xs text-slate-500 space-y-1">
                        <p>💡 Get your free API key at: <a href="https://aistudio.google.com/app/apikey" target="_blank" className="text-indigo-400 hover:underline">Google AI Studio</a></p>
                        <p>🔒 Your API key is tested securely and not stored</p>
                    </div>
                </CardContent>
            </Card>

            {/* Quick Fixes */}
            <Card className="border-slate-800 bg-slate-900/50">
                <CardHeader>
                    <CardTitle>Common Issues & Fixes</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div className="p-3 bg-slate-800/30 rounded border border-slate-700">
                        <div className="font-medium mb-1">❌ Gemini API not working</div>
                        <div className="text-sm text-slate-400">
                            1. Check your API key in <code className="bg-slate-700 px-1 rounded">backend/.env</code><br />
                            2. Verify key at Google AI Studio<br />
                            3. Restart the backend server
                        </div>
                    </div>

                    <div className="p-3 bg-slate-800/30 rounded border border-slate-700">
                        <div className="font-medium mb-1">❌ Database not connected</div>
                        <div className="text-sm text-slate-400">
                            1. Check if <code className="bg-slate-700 px-1 rounded">learnloop.db</code> exists in backend folder<br />
                            2. Restart the backend server to initialize database
                        </div>
                    </div>

                    <div className="p-3 bg-slate-800/30 rounded border border-slate-700">
                        <div className="font-medium mb-1">❌ Cannot connect to backend</div>
                        <div className="text-sm text-slate-400">
                            1. Ensure backend is running on port 8000<br />
                            2. Run <code className="bg-slate-700 px-1 rounded">python start_project.py</code> from project root
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
