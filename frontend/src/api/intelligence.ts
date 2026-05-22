import client from './client'

export const fetchData = (business_id: string) =>
  client.post('/v1/data/fetch', { business_id })

export const computeScore = (business_id: string) =>
  client.post('/v1/intelligence/score', { business_id })

export const getScore = (business_id: string) =>
  client.get(`/v1/intelligence/score/${business_id}`)
export const acceptOffer = (data: {
  business_id: string
  lender_name: string
  amount: number
  rate: number
}) => client.post('/v1/loans/accept', data)