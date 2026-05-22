import { create } from 'zustand'

interface ScoreData {
  score: number
  grade: string
  cash_flow_score: number
  payment_discipline_score: number
  gst_compliance_score: number
  revenue_growth_score: number
  business_vintage_score: number
  recommended_limit: number
  flags: string[]
  positive_factors: string[]
  improvement_areas: string[]
  confidence: number
}

interface BusinessState {
  scoreData: ScoreData | null
  setScoreData: (data: ScoreData) => void
}

export const useBusinessStore = create<BusinessState>((set) => ({
  scoreData: null,
  setScoreData: (data) => set({ scoreData: data })
}))