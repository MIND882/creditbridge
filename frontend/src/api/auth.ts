import client from './client'

export const register = (data: {
  pan: string
  gstin?: string
  business_name: string
  owner_name: string
  owner_phone: string
  owner_email?: string
  business_type?: string
  city?: string
  state?: string
  pan_verified?: boolean
  gstin_verified?: boolean
  kyc_score?: number
}) => client.post('/v1/auth/register', data)

export const login = (owner_phone: string) =>
  client.post('/v1/auth/login', { owner_phone })
