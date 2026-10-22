import { useSelector } from 'react-redux'

export default function FollowUpSuggestions() {
  const suggestions = useSelector((s) => s.interaction.followupSuggestions)

  if (!suggestions) return null

  const lines = suggestions
    .split('\n')
    .map((l) => l.replace(/^-\s*/, '').trim())
    .filter(Boolean)

  return (
    <div className="followups">
      <strong>AI Suggested Follow-ups:</strong>
      <ul>
        {lines.map((line, i) => (
          <li key={i}>{line}</li>
        ))}
      </ul>
    </div>
  )
}
