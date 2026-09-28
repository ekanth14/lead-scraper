import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_URL,
})

export const scrapeLeads = async ({ source, niche, city, brand, apiKey }) => {
  const { data } = await api.post(`/scrape/${source}`, { niche, city, api_key: apiKey, brand })
  return data
}

export const fetchLeads = async ({ brand, source, limit = 50, offset = 0 }) => {
  const { data } = await api.get('/leads', {
    params: { brand, source: source === 'all' ? undefined : source, limit, offset },
  })
  return data
}

export const fetchStats = async (brand) => {
  const { data } = await api.get('/leads/stats', { params: { brand } })
  return data
}

export const generateOutreach = async ({ lead, brand }) => {
  const { data } = await api.post('/outreach', { lead, brand, lead_id: lead.id })
  return data
}

export const exportLeads = async ({ brand, source }) => {
  const response = await api.get('/leads/export', {
    params: { brand, source: source === 'all' ? undefined : source },
    responseType: 'blob',
  })
  return response.data
}

export const deleteLead = async (id) => {
  const { data } = await api.delete(`/leads/${id}`)
  return data
}
