import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' }
})

export const setApiKey = (key: string) => {
  client.defaults.headers['x-api-key'] = key
  localStorage.setItem('lender_api_key', key)
}

export const getApiKey = () => localStorage.getItem('lender_api_key')

// Added: sign out function
export const removeApiKey = () => {
  delete client.defaults.headers['x-api-key']
  localStorage.removeItem('lender_api_key')
}

// Auto-load from storage on init
const saved = getApiKey()
if (saved) client.defaults.headers['x-api-key'] = saved

export default client