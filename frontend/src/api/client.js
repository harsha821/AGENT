import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export const createInteraction = (payload) =>
  client.post('/interactions', payload).then((r) => r.data)

export const updateInteraction = (id, payload) =>
  client.put(`/interactions/${id}`, payload).then((r) => r.data)

export const getInteraction = (id) =>
  client.get(`/interactions/${id}`).then((r) => r.data)

export const sendChatMessage = (message, hcp_id, context = {}) =>
  client.post('/agent/chat', {
    message,
    hcp_id,
    current_interaction_id: context.currentInteractionId ?? null,
    current_form: context.currentForm ?? {},
  }).then((r) => r.data)

export default client

