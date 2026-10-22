import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  currentInteractionId: null,
  hcpId: null,
  hcpName: '',
  interactionType: 'Meeting',
  date: '',
  time: '',
  attendees: '',
  topicsDiscussed: '',
  materialsShared: '',
  samplesDistributed: '',
  sentiment: 'Neutral',
  outcomes: '',
  followupActions: '',
  chatMessages: [], // { role: 'user' | 'assistant', text: string }
  followupSuggestions: '',
}

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    setField(state, action) {
      const { field, value } = action.payload
      state[field] = value
    },
    setInteractionId(state, action) {
      state.currentInteractionId = action.payload
    },
    addChatMessage(state, action) {
      state.chatMessages.push(action.payload)
    },
    setFollowupSuggestions(state, action) {
      state.followupSuggestions = action.payload
    },
    // Called when the agent logs/edits data via chat, so the form reflects it
    hydrateFromChat(state, action) {
      Object.assign(state, action.payload)
    },
    resetForm() {
      return initialState
    },
  },
})

export const {
  setField,
  setInteractionId,
  addChatMessage,
  setFollowupSuggestions,
  hydrateFromChat,
  resetForm,
} = interactionSlice.actions

export default interactionSlice.reducer
