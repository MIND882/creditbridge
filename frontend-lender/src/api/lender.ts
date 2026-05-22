import client from './client'

export const getPool = (filters = {}) =>
  client.get('/v1/lenders/pool', { params: filters })

export const getSegments = () =>
  client.get('/v1/lenders/segments')

export const getBusinessDetail = (id: string) =>
  client.get(`/v1/lenders/business/${id}`)

export const getExplanation = (id: string) =>
  client.get(`/v1/lenders/explain/${id}`)

export const logRejection = (data: {
  business_id: string
  rejection_reason: string
  rejection_detail: string
}) => client.post('/v1/lenders/reject', data)

export const getPortfolio = () =>
  client.get('/v1/lenders/portfolio')