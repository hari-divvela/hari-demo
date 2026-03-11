export interface User {
  id: string
  email: string
  display_name?: string
  photo_url?: string
  email_verified: boolean
  
  // Gmail integration
  gmail_connected: boolean
  gmail_access_token?: string
  gmail_refresh_token?: string
  gmail_token_expires_at?: string
  
  // Preferences
  notification_preferences: Record<string, boolean>
  
  // Settings
  sync_frequency_minutes: number
  auto_categorize: boolean
  auto_summarize: boolean
  
  // Metadata
  created_at: string
  last_login?: string
  last_sync?: string
}

export interface UserCreate {
  email: string
  display_name?: string
  photo_url?: string
}

export interface UserUpdate {
  display_name?: string
  photo_url?: string
  notification_preferences?: Record<string, boolean>
  sync_frequency_minutes?: number
  auto_categorize?: boolean
  auto_summarize?: boolean
}

export interface UserPreferences {
  notification_preferences: Record<string, boolean>
  sync_frequency_minutes: number
  auto_categorize: boolean
  auto_summarize: boolean
}
