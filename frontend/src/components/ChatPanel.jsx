import { useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { addChatMessage, hydrateFromChat } from '../redux/interactionSlice'
import { sendChatMessage } from '../api/client'

export default function ChatPanel() {
  const dispatch = useDispatch()

  const interactionState = useSelector((s) => s.interaction)
  const messages = interactionState.chatMessages
  const selectedHcpId = interactionState.hcpId
  const hcpName = interactionState.hcpName

  // Temporary mapping (replace later with DB/API lookup)
  const doctorMap = {
    "Dr. Smith": 1,
    "Dr. Sharma": 2,
    "Dr. Rajesh Kumar": 3,
  }

  const hcpId = selectedHcpId ?? doctorMap[hcpName] ?? null

  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim()) return

    const userText = input

    dispatch(
      addChatMessage({
        role: "user",
        text: userText,
      })
    )

    setInput("")
    setLoading(true)

    try {
      const { response, form_update } = await sendChatMessage(userText, hcpId, {
        currentInteractionId: interactionState.currentInteractionId,
        currentForm: {
          hcpId: interactionState.hcpId,
          hcpName: interactionState.hcpName,
          interactionType: interactionState.interactionType,
          date: interactionState.date,
          time: interactionState.time,
          attendees: interactionState.attendees,
          topicsDiscussed: interactionState.topicsDiscussed,
          materialsShared: interactionState.materialsShared,
          samplesDistributed: interactionState.samplesDistributed,
          sentiment: interactionState.sentiment,
          outcomes: interactionState.outcomes,
          followupActions: interactionState.followupActions,
        },
      })

      if (form_update) {
        dispatch(hydrateFromChat(form_update))
      }

      dispatch(
        addChatMessage({
          role: "assistant",
          text: response,
        })
      )
    } catch (err) {
      console.error(err)

      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Sorry, something went wrong reaching the agent."

      dispatch(
        addChatMessage({
          role: "assistant",
          text: errorMessage,
        })
      )
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      className="panel chat-panel"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "700px",
      }}
    >
      <h3>AI Assistant</h3>

      <p style={{ fontSize: 12, color: "#666" }}>
        Log interaction via chat
      </p>

      <div
        className="chat-messages"
        style={{
          flex: 1,
          overflowY: "auto",
          marginBottom: "12px",
        }}
      >
        {messages.length === 0 && (
          <div style={{ fontSize: 13, color: "#888" }}>
            Log interaction details here
            <br />
            Example:
            <br />
            Met Dr. Rajesh Kumar today. Discussed NeuroCare Plus.
            Shared brochure. Positive response.
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`chat-bubble ${m.role}`}
          >
            {m.text}
          </div>
        ))}

        {loading && (
          <div className="chat-bubble assistant">
            Thinking...
          </div>
        )}
      </div>

      <div className="chat-input-row">
        <input
          type="text"
          placeholder="Describe interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />

        <button
          className="primary"
          onClick={handleSend}
          disabled={loading}
        >
          Log
        </button>
      </div>
    </div>
  )
}
