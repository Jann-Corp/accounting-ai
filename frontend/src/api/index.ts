import axios from 'axios'
import type {
  ApiKeyResponse,
  ApiKeyCreate,
  LoginRequest,
  RegisterRequest,
  Token,
  User,
  Wallet,
  WalletCreate,
  TransferRequest,
  Category,
  CategoryCreate,
  CategoryType,
  Record,
  RecordCreate,
  RecordType,
  RecordStatus,
  MonthlyStats,
  CategoryBreakdownResponse,
  TrendResponse,
  AIRecognizeResponse,
} from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  register: (data: RegisterRequest) =>
    api.post<User>('/auth/register', data),

  login: (data: LoginRequest) =>
    api.post<Token>('/auth/login', data).then(res => {
      localStorage.setItem('token', res.data.access_token)
      return res
    }),

  getMe: () =>
    api.get<User>('/auth/me'),

  logout: () => {
    localStorage.removeItem('token')
  },
}

// Wallet API
export const walletApi = {
  list: () =>
    api.get<Wallet[]>('/wallets'),

  create: (data: WalletCreate) =>
    api.post<Wallet>('/wallets', data),

  update: (id: number, data: Partial<WalletCreate>) =>
    api.put<Wallet>(`/wallets/${id}`, data),

  delete: (id: number) =>
    api.delete(`/wallets/${id}`),

  transfer: (data: TransferRequest) =>
    api.post('/wallets/transfer', data),
}

// Category API
export const categoryApi = {
  list: (categoryType?: CategoryType) =>
    api.get<Category[]>('/categories', {
      params: categoryType ? { category_type: categoryType } : {},
    }),

  create: (data: CategoryCreate) =>
    api.post<Category>('/categories', data),

  update: (id: number, data: Partial<CategoryCreate>) =>
    api.put<Category>(`/categories/${id}`, data),

  delete: (id: number) =>
    api.delete(`/categories/${id}`),
}

// Record API
export const recordApi = {
  list: (params?: {
    start_date?: string
    end_date?: string
    wallet_id?: number
    category_id?: number
    record_type?: RecordType
    status?: RecordStatus
    limit?: number
    offset?: number
  }) =>
    api.get<Record[]>('/records', { params }),

  create: (data: RecordCreate) =>
    api.post<Record>('/records', data),

  get: (id: number) =>
    api.get<Record>(`/records/${id}`),

  update: (id: number, data: Partial<RecordCreate>) =>
    api.put<Record>(`/records/${id}`, data),

  delete: (id: number) =>
    api.delete(`/records/${id}`),

  pending: () =>
    api.get<Record[]>('/records/pending'),

  confirm: (id: number) =>
    api.post<Record>(`/records/${id}/confirm`),

  reject: (id: number) =>
    api.post(`/records/${id}/reject`),
}

// AI API
export const aiApi = {
  recognize: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<AIRecognizeResponse>('/ai/recognize', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// Stats API
export const statsApi = {
  monthly: (year?: number, month?: number) =>
    api.get<MonthlyStats>('/stats/monthly', { params: { year, month } }),

  categoryBreakdown: (year?: number, month?: number) =>
    api.get<CategoryBreakdownResponse>('/stats/category-breakdown', { params: { year, month } }),

  trend: (months?: number) =>
    api.get<TrendResponse>('/stats/trend', { params: { months } }),
}

// Export API
export const exportApi = {
  export: (format: 'csv' | 'json', params?: { start_date?: string; end_date?: string }) =>
    api.get('/records/export', {
      params: { format, ...params },
      responseType: 'blob',
    }),
}


// API Key API
export const apiKeyApi = {
  list: () =>
    api.get<ApiKeyResponse[]>('/api-keys'),

  create: (data: ApiKeyCreate) =>
    api.post<ApiKeyResponse>('/api-keys', data),

  update: (id: number, data: Partial<ApiKeyCreate & { is_active?: boolean }>) =>
    api.patch<ApiKeyResponse>(`/api-keys/${id}`, data),

  delete: (id: number) =>
    api.delete(`/api-keys/${id}`),
}


export default api
