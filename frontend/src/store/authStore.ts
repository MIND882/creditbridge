import { create } from 'zustand'

interface AuthState {
  token: string | null
  business_id: string | null
  phone: string | null
  setAuth: (token: string, business_id: string, phone: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('access_token'),
  business_id: localStorage.getItem('business_id'),
  phone: localStorage.getItem('phone'),
  setAuth: (token, business_id, phone) => {
    localStorage.setItem('access_token', token)
    localStorage.setItem('business_id', business_id)
    localStorage.setItem('phone', phone)
    set({ token, business_id, phone })
  },
  logout: () => {
    localStorage.clear()
    set({ token: null, business_id: null, phone: null })
  }
}))