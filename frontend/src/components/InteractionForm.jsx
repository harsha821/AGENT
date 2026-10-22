import { useSelector, useDispatch } from 'react-redux'
import { setField, setInteractionId } from '../redux/interactionSlice'
import { createInteraction, updateInteraction } from '../api/client'
import FollowUpSuggestions from './FollowUpSuggestions'

export default function InteractionForm() {
  const dispatch = useDispatch()
  const state = useSelector((s) => s.interaction)

  const handleChange = (field) => (e) => {
    dispatch(setField({ field, value: e.target.value }))
  }

  const handleSave = async () => {
    const doctorMap = {
  "Dr. Smith": 1,
  "Dr. Sharma": 2,
  }

  const payload = {
    hcp_id: doctorMap[state.hcpName] ?? null,
    interaction_type: state.interactionType,
    interaction_date: state.date && state.time
      ? `${state.date}T${state.time}`
      : null,
    attendees: state.attendees,
    topics_discussed: state.topicsDiscussed,
    materials_shared: state.materialsShared,
    samples_distributed: state.samplesDistributed,
    sentiment: state.sentiment,
    outcomes: state.outcomes,
    followup_actions: state.followupActions,
  }

    if (state.currentInteractionId) {
      await updateInteraction(state.currentInteractionId, payload)
    } else {
      const created = await createInteraction(payload)
      dispatch(setInteractionId(created.id))
    }
  }

  return (
    <div className="panel form-panel">
      <h2>Log HCP Interaction</h2>

      <div className="field">
        <label>HCP Name</label>
        <input
          type="text"
          placeholder="Search or select HCP..."
          value={state.hcpName}
          onChange={handleChange('hcpName')}
        />
      </div>

      <div className="field">
        <label>Interaction Type</label>
        <select value={state.interactionType} onChange={handleChange('interactionType')}>
          <option>Meeting</option>
          <option>Call</option>
          <option>Email</option>
          <option>Conference</option>
        </select>
      </div>

      <div className="field">
        <label>Date</label>
        <input type="date" value={state.date} onChange={handleChange('date')} />
      </div>

      <div className="field">
        <label>Time</label>
        <input type="time" value={state.time} onChange={handleChange('time')} />
      </div>

      <div className="field">
        <label>Attendees</label>
        <input
          type="text"
          placeholder="Enter names or search..."
          value={state.attendees}
          onChange={handleChange('attendees')}
        />
      </div>

      <div className="field">
        <label>Topics Discussed</label>
        <textarea
          rows={3}
          placeholder="Enter key discussion points..."
          value={state.topicsDiscussed}
          onChange={handleChange('topicsDiscussed')}
        />
      </div>

      <div className="field">
        <label>Materials Shared</label>
        <input
          type="text"
          placeholder="No materials added"
          value={state.materialsShared}
          onChange={handleChange('materialsShared')}
        />
      </div>

      <div className="field">
        <label>Samples Distributed</label>
        <input
          type="text"
          placeholder="No samples added"
          value={state.samplesDistributed}
          onChange={handleChange('samplesDistributed')}
        />
      </div>

      <div className="field">
        <label>Observed / Inferred HCP Sentiment</label>
        <div className="sentiment-row">
          {['Positive', 'Neutral', 'Negative'].map((s) => (
            <label key={s}>
              <input
                type="radio"
                name="sentiment"
                checked={state.sentiment === s}
                onChange={() => dispatch(setField({ field: 'sentiment', value: s }))}
              />{' '}
              {s}
            </label>
          ))}
        </div>
      </div>

      <div className="field">
        <label>Outcomes</label>
        <textarea
          rows={2}
          placeholder="Key outcomes or agreements..."
          value={state.outcomes}
          onChange={handleChange('outcomes')}
        />
      </div>

      <div className="field">
        <label>Follow-up Actions</label>
        <textarea
          rows={2}
          placeholder="Enter next steps or tasks..."
          value={state.followupActions}
          onChange={handleChange('followupActions')}
        />
      </div>

      <FollowUpSuggestions />

      <button className="primary" onClick={handleSave}>
        {state.currentInteractionId ? 'Update Interaction' : 'Log Interaction'}
      </button>
    </div>
  )
}
