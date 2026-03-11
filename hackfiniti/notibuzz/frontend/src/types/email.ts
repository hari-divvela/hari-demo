export type PriorityLevel = 'urgent' | 'important' | 'normal' | 'low'

export type EmailCategory = 'work' | 'personal' | 'financial' | 'marketing' | 'social' | 'newsletter' | 'other'

export interface EmailAttachment {
  filename: string
  size: number
  content_type: string
  attachment_id?: string
}

export interface Email {
  id: string
  thread_id: string
  subject: string
  sender: string
  sender_email: string
  recipients: string[]
  cc: string[]
  bcc: string[]
  body_text: string
  body_html?: string
  timestamp: string
  read: boolean
  starred: boolean
  important: boolean
  attachments: EmailAttachment[]
  labels: string[]
  
  // AI-generated fields
  summary?: string
  priority: PriorityLevel
  category: EmailCategory
  sentiment_score?: number
  embedding?: number[]
  
  // Processing metadata
  processed_at?: string
  last_updated: string
}

export interface EmailSearch {
  query: string
  limit: number
  offset: number
  filters?: Record<string, any>
}

export interface EmailSearchResult {
  emails: Email[]
  total_count: number
  query: string
  processing_time: number
}

export interface EmailAnalytics {
  total_emails: number
  unread_count: number
  urgent_count: number
  important_count: number
  category_breakdown: Record<string, number>
  daily_volume: Record<string, number>
  top_senders: Record<string, number>
}
