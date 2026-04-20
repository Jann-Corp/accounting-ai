// User types
export interface User {
  id: string
  username: string
  email: string
  created_at: string
}

// Auth types
export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface Token {
  access_token: string
}

// Wallet types
export enum WalletType {
  CASH = 'cash',
  BANK_CARD = 'bank_card',
  E_WALLET = 'e_wallet',
  OTHER = 'other'
}

export interface Wallet {
  id: number
  user_id: string
  name: string
  wallet_type: WalletType
  balance: number
  currency: string
  created_at: string
  updated_at?: string
}

export interface WalletCreate {
  name: string
  wallet_type: WalletType
  balance?: number
  currency?: string
}

export interface TransferRequest {
  from_wallet_id: number
  to_wallet_id: number
  amount: number
  note?: string
}

// Category types
export enum CategoryType {
  EXPENSE = 'expense',
  INCOME = 'income'
}

export interface Category {
  id: number
  user_id: string
  name: string
  category_type: CategoryType
  icon: string
  is_default: boolean
  created_at: string
}

export interface CategoryCreate {
  name: string
  category_type: CategoryType
  icon: string
}

// Record types
export enum RecordType {
  EXPENSE = 'expense',
  INCOME = 'income'
}

export enum RecordStatus {
  CONFIRMED = 'confirmed',
  PENDING = 'pending',
  REJECTED = 'rejected'
}

export interface Record {
  id: number
  user_id: string
  wallet_id: number
  category_id: number | null
  amount: number
  record_type: RecordType
  note: string
  date: string
  original_image_url: string | null
  ai_confidence: number | null
  status: RecordStatus
  created_at: string
  updated_at: string
  wallet_name: string | null
  category_name: string | null
  category_icon: string | null
}

export interface RecordCreate {
  wallet_id: number
  category_id: number | null
  amount: number
  record_type: RecordType
  note?: string
  date: string
}

// AI types
export interface AIRecognizeRecord {
  amount: number | null
  merchant_name: string | null
  date: string | null
  category_guess: string | null
  category_id: number | null
  confidence: number
  record_type: 'expense' | 'income'
}

export interface AIRecognizeResponse {
  amount: number | null
  merchant_name: string | null
  date: string | null
  category_guess: string | null
  category_id: number | null
  confidence: number
  original_image_url: string | null
  raw_response?: any
  records: AIRecognizeRecord[]
}

// Stats types
export interface MonthlyStats {
  year: number
  month: number
  total_expense: number
  total_income: number
  balance: number
  record_count: number
}

export interface CategoryBreakdown {
  category_id: number
  category_name: string
  category_icon: string
  total_amount: number
  percentage: number
  record_count: number
}

export interface TrendPoint {
  year: number
  month: number
  total_expense: number
  total_income: number
}

export interface CategoryBreakdownResponse {
  year: number
  month: number
  breakdown: CategoryBreakdown[]
}

export interface TrendResponse {
  trend: TrendPoint[]
}

// API Key types
export interface ApiKeyResponse {
  id: number
  name: string
  key_prefix: string
  key_full: string | null   // Only returned ONCE at creation time
  is_active: boolean
  last_used_at: string | null
  expires_at: string | null
  created_at: string
}

export interface ApiKeyCreate {
  name: string
  expires_at?: string | null
}
