'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Mail, 
  Brain, 
  Search, 
  Bell, 
  BarChart3, 
  TrendingUp,
  Clock,
  Star,
  AlertTriangle,
  Users
} from 'lucide-react'
import { Email, EmailAnalytics } from '@/types/email'
import { User } from '@/types/user'
import { api } from '@/lib/api'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [analytics, setAnalytics] = useState<EmailAnalytics | null>(null)
  const [recentEmails, setRecentEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('authToken')
    if (!token) {
      router.push('/login')
      return
    }

    fetchDashboardData()
  }, [router])

  const fetchDashboardData = async () => {
    try {
      // Fetch analytics
      const analyticsData = await api.get<EmailAnalytics>('/api/emails/analytics/summary')
      setAnalytics(analyticsData)

      // Fetch recent emails
      const emailsData = await api.get<Email[]>('/api/emails?limit=5')
      setRecentEmails(emailsData)

      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      setLoading(false)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800'
      case 'important': return 'bg-orange-100 text-orange-800'
      case 'normal': return 'bg-blue-100 text-blue-800'
      case 'low': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'work': return <Briefcase className="h-4 w-4" />
      case 'personal': return <User className="h-4 w-4" />
      case 'financial': return <DollarSign className="h-4 w-4" />
      default: return <Mail className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Mail className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">NotiBuzz Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="outline" onClick={() => router.push('/inbox')}>
                <Mail className="h-4 w-4 mr-2" />
                Inbox
              </Button>
              <Button variant="outline" onClick={() => router.push('/search')}>
                <Search className="h-4 w-4 mr-2" />
                Search
              </Button>
              <Button onClick={() => {
                localStorage.removeItem('authToken')
                router.push('/login')
              }}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Stats Overview */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Emails</CardTitle>
                <Mail className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.total_emails}</div>
                <p className="text-xs text-muted-foreground">
                  All time emails
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Unread</CardTitle>
                <Mail className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.unread_count}</div>
                <p className="text-xs text-muted-foreground">
                  Need attention
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Urgent</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{analytics.urgent_count}</div>
                <p className="text-xs text-muted-foreground">
                  High priority
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Important</CardTitle>
                <Star className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">{analytics.important_count}</div>
                <p className="text-xs text-muted-foreground">
                  Priority items
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Emails */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Clock className="h-5 w-5 mr-2" />
                  Recent Emails
                </CardTitle>
                <CardDescription>
                  Latest emails from your inbox
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentEmails.map((email) => (
                    <div key={email.id} className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Mail className="h-5 w-5 text-blue-600" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {email.sender}
                          </p>
                          <div className="flex items-center space-x-2">
                            <Badge className={getPriorityColor(email.priority)}>
                              {email.priority}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              {new Date(email.timestamp).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-900 font-medium truncate">
                          {email.subject}
                        </p>
                        {email.summary && (
                          <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                            {email.summary}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                {recentEmails.length === 0 && (
                  <div className="text-center py-8">
                    <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No recent emails found</p>
                    <Button 
                      variant="outline" 
                      className="mt-4"
                      onClick={() => router.push('/inbox')}
                    >
                      View Inbox
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions & Insights */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="h-5 w-5 mr-2" />
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => router.push('/inbox')}
                >
                  <Mail className="h-4 w-4 mr-2" />
                  View Inbox
                </Button>
                <Button 
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => router.push('/search')}
                >
                  <Search className="h-4 w-4 mr-2" />
                  Search Emails
                </Button>
                <Button 
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => api.post('/api/gmail/sync')}
                >
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Sync Gmail
                </Button>
              </CardContent>
            </Card>

            {analytics && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BarChart3 className="h-5 w-5 mr-2" />
                    Email Categories
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(analytics.category_breakdown).map(([category, count]) => (
                      <div key={category} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                          <span className="text-sm capitalize">{category}</span>
                        </div>
                        <span className="text-sm font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

import { Briefcase, User, DollarSign } from 'lucide-react'
