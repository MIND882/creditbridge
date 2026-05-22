import client from './client'

export const initiateConsent = (business_id: string, phone: string) =>
  client.post('/v1/consent/initiate', { business_id, phone })

export const getConsentStatus = (business_id: string) =>
  client.get(`/v1/consent/status/${business_id}`)