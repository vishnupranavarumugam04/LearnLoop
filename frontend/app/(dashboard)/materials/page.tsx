"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FileText, Youtube, Upload, Link as LinkIcon, Loader2, Trash2, Search, File, ExternalLink, X, BookOpen, History } from "lucide-react"
import { useState, useRef, useEffect } from "react"
import { useAuth } from "@/context/auth-context"
import { ScrollArea } from "@/components/ui/scroll-area"

interface Material {
    id: number
    filename: string
    file_type: string
    uploaded_at: string
    summary: string
    full_text?: string
    learning_stage?: string
    xp_earned_total?: number
}

export default function MaterialsPage() {
    const { user } = useAuth()
    const [materials, setMaterials] = useState<Material[]>([])
    const [isUploading, setIsUploading] = useState(false)
    const [activeTab, setActiveTab] = useState("upload")
    const [urlInput, setUrlInput] = useState("")
    const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null)
    const [isViewLoading, setIsViewLoading] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        fetchMaterials()
    }, [user])

    const fetchMaterials = async () => {
        if (!user) return
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/material/?user_id=${encodeURIComponent(user.email)}`)
            if (res.ok) {
                const data = await res.json()
                setMaterials(data)
            }
        } catch (e) {
            console.error("Failed to fetch materials", e)
        }
    }

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file || !user) return

        setIsUploading(true)
        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/material/upload?user_id=${encodeURIComponent(user.email)}`, {
                method: 'POST',
                body: formData
            })

            if (res.ok) {
                const data = await res.json()
                fetchMaterials()
                alert("Material uploaded and analyzed! You can now chat with Buddy about it.")
            } else {
                const errorData = await res.json().catch(() => ({ detail: "Unknown error" }))
                alert(`Upload failed: ${errorData.detail || res.statusText}`)
            }
        } catch (e) {
            console.error(e)
            alert("Failed to upload material. Please check your connection and the server status.")
        } finally {
            setIsUploading(false)
        }
    }

    const handleUrlUpload = () => {
        alert("YouTube analysis coming soon!")
    }

    const handleDelete = async (id: number, e: React.MouseEvent) => {
        e.stopPropagation()
        if (!confirm("Are you sure you want to delete this material? This will also remove your learning progress for it.")) return

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/material/${id}`, {
                method: 'DELETE'
            })
            if (res.ok) {
                setMaterials(materials.filter(m => m.id !== id))
            } else {
                alert("Failed to delete material")
            }
        } catch (e) {
            console.error("Delete error", e)
            alert("An error occurred during deletion")
        }
    }

    const handleOpen = async (item: Material) => {
        setIsViewLoading(true)
        setSelectedMaterial(item) // Set basic info first for the modal skeleton/header

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/material/${item.id}`)
            if (res.ok) {
                const data = await res.json()
                setSelectedMaterial(data)
            } else {
                console.warn("Failed to fetch material details. Status:", res.status)
            }
        } catch (e) {
            console.error("Failed to fetch material details", e)
            // Error is handled gracefully - user still sees basic info and header
        } finally {
            setIsViewLoading(false)
        }
    }

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <div className="animate-in slide-in-from-left duration-500">
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600">Study Materials</h1>
                    <p className="text-muted-foreground">Manage your documents and learning resources</p>
                </div>
                <Button className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20" onClick={() => fileInputRef.current?.click()}>
                    <Upload className="mr-2 h-4 w-4" /> Upload New
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Upload Area */}
                <div className="lg:col-span-1 space-y-6">
                    <Card className="border-border bg-card/50 backdrop-blur-sm shadow-sm">
                        <CardHeader>
                            <CardTitle className="text-foreground">Add Content</CardTitle>
                            <CardDescription className="text-muted-foreground">PDF, PPT, DOCX, TXT</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex gap-2 p-1 bg-secondary rounded-lg">
                                <button
                                    onClick={() => setActiveTab("upload")}
                                    className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${activeTab === 'upload' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                                >
                                    Upload File
                                </button>
                                <button
                                    onClick={() => setActiveTab("link")}
                                    className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${activeTab === 'link' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                                >
                                    YouTube / URL
                                </button>
                            </div>

                            {activeTab === 'upload' ? (
                                <div
                                    className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-primary/50 hover:bg-primary/5 transition-all cursor-pointer group"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    <div className="bg-primary/10 h-10 w-10 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                                        <Upload className="h-5 w-5 text-primary" />
                                    </div>
                                    <p className="text-sm font-semibold text-foreground">Click to upload files</p>
                                    <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, TXT (Max 50MB)</p>
                                    <input
                                        type="file"
                                        className="hidden"
                                        ref={fileInputRef}
                                        onChange={handleFileUpload}
                                    />
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Video or Article URL</label>
                                        <div className="flex gap-2">
                                            <Input
                                                placeholder="https://youtube.com/..."
                                                className="bg-background border-border"
                                                value={urlInput}
                                                onChange={(e) => setUrlInput(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <Button className="w-full bg-secondary text-secondary-foreground hover:bg-secondary/80" onClick={handleUrlUpload} disabled={isUploading}>
                                        {isUploading ? <Loader2 className="animate-spin h-4 w-4" /> : "Process Link"}
                                    </Button>
                                    <p className="text-[10px] text-center text-muted-foreground">YouTube analysis is powered by Buddy AI</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Right: Library */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex gap-2 mb-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                            <Input placeholder="Search materials..." className="pl-9 bg-card border-border shadow-sm" />
                        </div>
                        <Button variant="outline" className="border-border bg-background hover:bg-secondary">Filters</Button>
                    </div>

                    {materials.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground border-2 border-dashed border-border rounded-2xl bg-secondary/20">
                            <div className="bg-background p-4 rounded-full mb-4 shadow-inner">
                                <File className="h-8 w-8 opacity-30" />
                            </div>
                            <p className="font-medium">No materials yet.</p>
                            <p className="text-xs">Upload your study content to get started.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {materials.map((item) => (
                                <Card
                                    key={item.id}
                                    className="hover:border-primary/50 hover:shadow-md transition-all cursor-pointer group bg-card border-border relative overflow-hidden active:scale-[0.98]"
                                    onClick={() => handleOpen(item)}
                                >
                                    <div className="absolute top-0 left-0 w-1 h-full bg-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                                    <CardContent className="p-4 flex gap-4">
                                        <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0 transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                                            <FileText className="h-6 w-6" />
                                        </div>
                                        <div className="flex-1 overflow-hidden pr-8">
                                            <h3 className="font-semibold text-foreground line-clamp-1 truncate group-hover:text-primary transition-colors">
                                                {item.filename}
                                            </h3>
                                            <p className="text-xs text-muted-foreground mt-1 font-medium bg-secondary w-fit px-1.5 py-0.5 rounded uppercase tracking-tighter">
                                                {item.file_type}
                                            </p>
                                            <p className="text-[10px] text-muted-foreground mt-1">
                                                Added {new Date(item.uploaded_at).toLocaleDateString()}
                                            </p>
                                        </div>

                                        {/* Actions */}
                                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-full"
                                                onClick={(e) => handleDelete(item.id, e)}
                                                title="Delete"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* View Modal */}
            {selectedMaterial && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md animate-in fade-in duration-300">
                    <Card className="w-full max-w-5xl max-h-[90vh] flex flex-col bg-card border-border shadow-2xl overflow-hidden ring-1 ring-primary/10 rounded-3xl animate-in zoom-in-95 duration-200">
                        <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4 pt-6 px-8 bg-gradient-to-b from-secondary/50 to-transparent">
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-2xl bg-primary flex items-center justify-center text-primary-foreground shadow-lg shadow-primary/20 shrink-0">
                                    <FileText className="h-6 w-6" />
                                </div>
                                <div className="overflow-hidden">
                                    <CardTitle className="text-2xl text-foreground font-bold truncate leading-tight">{selectedMaterial.filename}</CardTitle>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className="text-muted-foreground uppercase text-[10px] tracking-widest font-black bg-secondary px-2 py-0.5 rounded">
                                            {selectedMaterial.file_type}
                                        </span>
                                        <span className="text-[10px] text-primary font-bold uppercase tracking-wider">
                                            Uploaded {new Date(selectedMaterial.uploaded_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-10 w-10 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-full transition-all"
                                onClick={() => setSelectedMaterial(null)}
                            >
                                <X className="h-6 w-6" />
                            </Button>
                        </CardHeader>

                        <div className="flex-1 overflow-hidden flex flex-col">

                            <div className="flex-1 p-0 flex flex-col bg-background">
                                <div className="px-8 py-5 border-b border-border flex justify-between items-center bg-background/50 backdrop-blur">
                                    <div className="flex items-center gap-4">
                                        <h4 className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">Source Intelligence</h4>
                                        <div className="flex items-center gap-2">
                                            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                                            <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">Analyzed</span>
                                        </div>
                                    </div>
                                    <div className="bg-secondary px-3 py-1 rounded-full text-[10px] text-primary font-black mono shadow-sm">
                                        {selectedMaterial.full_text?.length || 0} WORDS
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-scroll p-8 scrollbar-thin scrollbar-thumb-primary/60 scrollbar-track-secondary/30 hover:scrollbar-thumb-primary transition-all" style={{ maxHeight: 'calc(90vh - 250px)' }}>
                                    {isViewLoading ? (
                                        <div className="flex flex-col items-center justify-center h-full gap-4 py-20 opacity-50">
                                            <Loader2 className="h-10 w-10 text-primary animate-spin" />
                                            <p className="text-muted-foreground text-sm font-bold tracking-widest animate-pulse">EXTRACTING KNOWLEDGE...</p>
                                        </div>
                                    ) : (
                                        <div className="prose prose-slate max-w-none">
                                            <p className="text-foreground/80 text-sm leading-8 whitespace-pre-wrap font-sans first-letter:text-4xl first-letter:font-bold first-letter:text-primary first-letter:mr-3 first-letter:float-left">
                                                {selectedMaterial.full_text || "Document content could not be displayed."}
                                            </p>
                                        </div>
                                    )}

                                    {/* Evolution Path for this Material */}
                                    {!isViewLoading && (
                                        <div className="mt-12 pt-8 border-t border-border">
                                            <h3 className="text-sm font-black text-muted-foreground uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                                                <History className="h-4 w-4" />
                                                Evolution Path for this Material
                                            </h3>
                                            <div className="grid grid-cols-5 gap-4">
                                                {[
                                                    { stage: 'uploaded', name: 'Uploaded', icon: '📄', description: 'Material added' },
                                                    { stage: 'buddy_taught', name: 'Buddy Taught', icon: '🤖', description: 'Buddy explained' },
                                                    { stage: 'user_taught', name: 'You Taught', icon: '🎓', description: 'You explained back' },
                                                    { stage: 'mastered', name: 'Mastered', icon: '🏆', description: 'Fully learned' },
                                                    { stage: 'expert', name: 'Expert', icon: '⭐', description: 'Teaching others' },
                                                ].map((evolutionStage, idx) => {
                                                    const currentStage = selectedMaterial.learning_stage || 'uploaded'
                                                    const stageOrder = ['uploaded', 'buddy_taught', 'user_taught', 'mastered', 'expert']
                                                    const currentIdx = stageOrder.indexOf(currentStage)
                                                    const thisIdx = stageOrder.indexOf(evolutionStage.stage)

                                                    const isCompleted = thisIdx < currentIdx
                                                    const isCurrent = thisIdx === currentIdx
                                                    const isLocked = thisIdx > currentIdx

                                                    return (
                                                        <div
                                                            key={evolutionStage.stage}
                                                            className={`relative flex flex-col items-center text-center p-4 rounded-2xl border-2 transition-all duration-300 ${isCurrent
                                                                ? 'bg-primary/10 border-primary shadow-lg shadow-primary/20'
                                                                : isCompleted
                                                                    ? 'bg-emerald-500/10 border-emerald-500/50'
                                                                    : 'bg-secondary/30 border-border opacity-50 grayscale'
                                                                }`}
                                                        >
                                                            {isCurrent && (
                                                                <div className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-[9px] uppercase font-black px-2 py-0.5 rounded-full shadow-md">
                                                                    Current
                                                                </div>
                                                            )}
                                                            {isCompleted && (
                                                                <div className="absolute -top-2 -right-2 bg-emerald-500 text-white text-[9px] uppercase font-black px-2 py-0.5 rounded-full shadow-md">
                                                                    ✓
                                                                </div>
                                                            )}
                                                            <div className="text-3xl mb-2">{evolutionStage.icon}</div>
                                                            <div className={`font-bold text-xs uppercase tracking-wider mb-1 ${isCurrent ? 'text-primary' : isCompleted ? 'text-emerald-600' : 'text-muted-foreground'}`}>
                                                                {evolutionStage.name}
                                                            </div>
                                                            <div className="text-[10px] text-muted-foreground">
                                                                {evolutionStage.description}
                                                            </div>
                                                        </div>
                                                    )
                                                })}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-border bg-secondary/30 flex justify-end gap-3 px-8">
                            <Button variant="outline" className="border-border bg-background hover:bg-secondary text-foreground font-bold px-6 rounded-xl" onClick={() => setSelectedMaterial(null)}>
                                Close
                            </Button>
                            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold px-8 rounded-xl shadow-lg shadow-primary/20 transition-all hover:scale-105" onClick={() => {
                                setSelectedMaterial(null);
                                window.location.href = `/chat?material=${encodeURIComponent(selectedMaterial.filename)}`;
                            }}>
                                Study with Buddy
                            </Button>
                        </div>
                    </Card>
                </div>
            )}
        </div>
    )
}
