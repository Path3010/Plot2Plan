import { useState, useCallback, useEffect } from 'react'
import ChatInterface from '../components/ChatInterface'
import FormInterface from '../components/FormInterface'
import PlanPreview from '../components/PlanPreview'
import Viewer3D from '../components/Viewer3D'
import ExportPanel from '../components/ExportPanel'
import axios from 'axios'

const API = '/api'

export default function Workspace() {
    const [activeTab, setActiveTab] = useState('form')
    const [previewMode, setPreviewMode] = useState('2d')
    const [projectId, setProjectId] = useState(null)
    const [plan, setPlan] = useState(null)
    const [boundary, setBoundary] = useState(null)
    const [loading, setLoading] = useState(false)
    const [toast, setToast] = useState(null)

    useEffect(() => {
        const sessionId = localStorage.getItem('session_id') || crypto.randomUUID()
        localStorage.setItem('session_id', sessionId)

        axios.post(`${API}/project`, { session_id: sessionId })
            .then(res => setProjectId(res.data.project_id))
            .catch(() => showToast('Failed to create project', 'error'))
    }, [])

    const showToast = useCallback((msg, type = 'success') => {
        setToast({ msg, type })
        setTimeout(() => setToast(null), 3000)
    }, [])

    const handleBoundaryUpload = useCallback(async (file, scale = 1.0) => {
        if (!projectId) return
        const formData = new FormData()
        formData.append('file', file)
        formData.append('project_id', projectId)
        formData.append('scale', scale)

        try {
            const res = await axios.post(`${API}/upload-boundary`, formData)
            setBoundary(res.data.polygon)
            showToast(`Boundary extracted: ${res.data.num_vertices} vertices`)
            return res.data
        } catch (err) {
            showToast(err.response?.data?.detail || 'Upload failed', 'error')
            return null
        }
    }, [projectId, showToast])

    const handleGenerate = useCallback(async (rooms, totalArea) => {
        if (!projectId) return
        setLoading(true)

        try {
            const res = await axios.post(`${API}/generate-floorplan`, {
                project_id: projectId,
                rooms,
                total_area: totalArea,
                boundary_polygon: boundary,
            })
            setPlan(res.data.plan)
            showToast('Floor plan generated!')
        } catch (err) {
            showToast(err.response?.data?.detail || 'Generation failed', 'error')
        } finally {
            setLoading(false)
        }
    }, [projectId, boundary, showToast])

    const handleGenerate3D = useCallback(async () => {
        if (!projectId) return
        setLoading(true)

        try {
            await axios.post(`${API}/generate-3d/${projectId}`)
            setPreviewMode('3d')
            showToast('3D model generated!')
        } catch (err) {
            showToast(err.response?.data?.detail || '3D generation failed', 'error')
        } finally {
            setLoading(false)
        }
    }, [projectId, showToast])

    const handleNewProject = useCallback(() => {
        const sessionId = localStorage.getItem('session_id') || crypto.randomUUID()
        axios.post(`${API}/project`, { session_id: sessionId })
            .then(res => {
                setProjectId(res.data.project_id)
                setPlan(null)
                setBoundary(null)
                setPreviewMode('2d')
                showToast('New project created')
            })
    }, [showToast])

    return (
        <div className="workspace">
            <div className="sidebar">
                <div className="sidebar-header">
                    <div className="logo">NakshaNirman</div>
                    <button className="btn btn-secondary btn-sm" onClick={handleNewProject}>
                        New
                    </button>
                </div>

                <div className="tab-switcher">
                    <button
                        className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                        onClick={() => setActiveTab('chat')}
                    >
                        Chat
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'form' ? 'active' : ''}`}
                        onClick={() => setActiveTab('form')}
                    >
                        Form
                    </button>
                </div>

                <div className="sidebar-content">
                    {activeTab === 'chat' ? (
                        <ChatInterface
                            projectId={projectId}
                            onGenerate={handleGenerate}
                            onBoundaryUpload={handleBoundaryUpload}
                        />
                    ) : (
                        <FormInterface
                            onGenerate={handleGenerate}
                            onBoundaryUpload={handleBoundaryUpload}
                            boundary={boundary}
                        />
                    )}
                </div>
            </div>

            <div className="preview-panel">
                <div className="preview-header">
                    <div className="preview-tabs">
                        <button
                            className={`preview-tab ${previewMode === '2d' ? 'active' : ''}`}
                            onClick={() => setPreviewMode('2d')}
                        >
                            2D Plan
                        </button>
                        <button
                            className={`preview-tab ${previewMode === '3d' ? 'active' : ''}`}
                            onClick={() => {
                                if (plan) handleGenerate3D()
                                setPreviewMode('3d')
                            }}
                        >
                            3D View
                        </button>
                    </div>
                    <div className="preview-actions">
                        {plan && (
                            <>
                                <a
                                    className="btn btn-secondary btn-sm"
                                    href={`${API}/download-dxf/${projectId}`}
                                    download
                                >
                                    Download DXF
                                </a>
                                <button className="btn btn-primary btn-sm" onClick={handleGenerate3D}>
                                    Make 3D
                                </button>
                            </>
                        )}
                    </div>
                </div>

                <div className="preview-content">
                    {loading && (
                        <div className="loading-overlay">
                            <div className="spinner" />
                            <div className="loading-text">Generating...</div>
                        </div>
                    )}

                    {previewMode === '2d' ? (
                        plan ? <PlanPreview plan={plan} /> : (
                            <div className="preview-empty">
                                <div className="preview-empty-icon">
                                    <svg width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" />
                                    </svg>
                                </div>
                                <h3>No Floor Plan Yet</h3>
                                <p>Use the chat or form to configure and generate your plan.</p>
                            </div>
                        )
                    ) : (
                        plan ? <Viewer3D projectId={projectId} /> : (
                            <div className="preview-empty">
                                <div className="preview-empty-icon">
                                    <svg width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                                    </svg>
                                </div>
                                <h3>No 3D Model Yet</h3>
                                <p>Generate a floor plan first, then click "Make 3D".</p>
                            </div>
                        )
                    )}
                </div>

                {plan && <ExportPanel projectId={projectId} onGenerate3D={handleGenerate3D} />}
            </div>

            {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
        </div>
    )
}
