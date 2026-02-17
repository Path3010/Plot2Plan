import { useState, useRef, useEffect, useCallback } from 'react'

export default function ChatInterface({ projectId, onGenerate, onBoundaryUpload }) {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: "Welcome! I'll help you design your floor plan. What's the total area of your plot (in sq ft)?" }
    ])
    const [input, setInput] = useState('')
    const [isTyping, setIsTyping] = useState(false)
    const [ws, setWs] = useState(null)
    const [wsReady, setWsReady] = useState(false)
    const [extractedData, setExtractedData] = useState({ rooms: [], total_area: null })
    const messagesEndRef = useRef(null)
    const fileInputRef = useRef(null)

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, isTyping])

    // WebSocket connection - only connect when user switches to chat tab
    useEffect(() => {
        let socket = null
        let reconnectTimeout = null

        const connect = () => {
            try {
                const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
                const wsUrl = `${proto}//${window.location.host}/api/chat`
                socket = new WebSocket(wsUrl)

                socket.onopen = () => {
                    setWs(socket)
                    setWsReady(true)
                }

                socket.onmessage = (event) => {
                    const data = JSON.parse(event.data)
                    setIsTyping(false)

                    setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])

                    if (data.extracted_data) {
                        setExtractedData(prev => {
                            const updated = { ...prev }
                            if (data.extracted_data.total_area) updated.total_area = data.extracted_data.total_area
                            if (data.extracted_data.rooms) {
                                updated.rooms = [...(updated.rooms || []), ...data.extracted_data.rooms]
                            }
                            return updated
                        })
                    }

                    if (data.should_generate && extractedData.total_area) {
                        onGenerate(extractedData.rooms, extractedData.total_area)
                    }
                }

                socket.onerror = () => {
                    setWsReady(false)
                }

                socket.onclose = () => {
                    setWs(null)
                    setWsReady(false)
                    // Retry after 5 seconds
                    reconnectTimeout = setTimeout(connect, 5000)
                }
            } catch {
                setWsReady(false)
            }
        }

        connect()

        return () => {
            if (reconnectTimeout) clearTimeout(reconnectTimeout)
            if (socket) socket.close()
        }
    }, [])

    const sendMessage = useCallback(() => {
        if (!input.trim()) return

        const userMsg = { role: 'user', content: input.trim() }
        setMessages(prev => [...prev, userMsg])
        setIsTyping(true)

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                message: input.trim(),
                project_id: projectId,
            }))
        } else {
            setTimeout(() => {
                setIsTyping(false)
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: "I'm not connected right now. Please use the Form tab to configure your floor plan.",
                }])
            }, 1000)
        }

        setInput('')
    }, [input, ws, projectId])

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    const handleFileUpload = async (e) => {
        const file = e.target.files?.[0]
        if (!file) return

        setMessages(prev => [...prev, {
            role: 'user', content: `Uploaded: ${file.name}`
        }])

        setIsTyping(true)
        const result = await onBoundaryUpload(file)
        setIsTyping(false)

        if (result) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `I've extracted the boundary from your upload. It has ${result.num_vertices} vertices and an area of ${result.area.toFixed(0)} sq units. Now, tell me what rooms you'd like!`,
            }])
        }
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {!wsReady && (
                <div style={{
                    padding: '0.5rem 0.8rem',
                    background: 'var(--warning-bg)',
                    border: '1px solid #fde68a',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.78rem',
                    color: '#92400e',
                    marginBottom: '0.5rem',
                }}>
                    Chat is connecting... You can use the Form tab in the meantime.
                </div>
            )}
            <div className="chat-messages" style={{ flex: 1 }}>
                {messages.map((msg, i) => (
                    <div key={i} className={`chat-bubble ${msg.role}`}>
                        {msg.content}
                    </div>
                ))}
                {isTyping && (
                    <div className="typing-indicator">
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area" style={{ position: 'sticky', bottom: 0 }}>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".png,.jpg,.jpeg,.dxf"
                    style={{ display: 'none' }}
                />
                <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => fileInputRef.current?.click()}
                    title="Upload boundary"
                >
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                </button>
                <input
                    className="chat-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Describe your dream home..."
                />
                <button className="btn btn-primary btn-sm" onClick={sendMessage}>
                    Send
                </button>
            </div>
        </div>
    )
}
