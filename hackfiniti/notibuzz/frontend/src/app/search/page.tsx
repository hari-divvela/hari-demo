'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Search, 
  Mail, 
  Clock, 
  Star, 
  AlertTriangle,
  Filter,
  Sparkles,
  TrendingUp
} from 'lucide-react'
import { Email, EmailSearchResult } from '@/types/email'
import { api } from '@/lib/api'

export default function SearchPage() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<EmailSearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    priority: '',
    category: '',
    dateRange: ''
  })

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('authToken')
    if (!token) {
      router.push('/login')
    }
  }, [router])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const searchRequest = {
        query: query.trim(),
        limit: 20,
        offset: 0,
        filters: Object.fromEntries(
          Object.entries(filters).filter(([_, value]) => value !== '')
        )
      }

      const results = await api.post<EmailSearchResult>('/api/search/semantic', searchRequest)
      setSearchResults(results)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
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

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'work': return 'bg-purple-100 text-purple-800'
      case 'personal': return 'bg-green-100 text-green-800'
      case 'financial': return 'bg-yellow-100 text-yellow-800'
      case 'marketing': return 'bg-pink-100 text-pink-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Mail className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">NotiBuzz Search</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="outline" onClick={() => router.push('/dashboard')}>
                Dashboard
              </Button>
              <Button variant="outline" onClick={() => router.push('/inbox')}>
                Inbox
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
        {/* Search Section */}
        <div className="max-w-4xl mx-auto mb-8">
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Sparkles className="h-5 w-5 mr-2 text-blue-600" />
                Semantic Email Search
              </CardTitle>
              <CardDescription>
                Search your emails using natural language. Try "emails about project deadline" or "find invoices from last month"
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSearch} className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search your emails..."
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                  />
                  <Button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2"
                  >
                    {loading ? 'Searching...' : 'Search'}
                  </Button>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap gap-4">
                  <select
                    value={filters.priority}
                    onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Priorities</option>
                    <option value="urgent">Urgent</option>
                    <option value="important">Important</option>
                    <option value="normal">Normal</option>
                    <option value="low">Low</option>
                  </select>

                  <select
                    value={filters.category}
                    onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Categories</option>
                    <option value="work">Work</option>
                    <option value="personal">Personal</option>
                    <option value="financial">Financial</option>
                    <option value="marketing">Marketing</option>
                    <option value="social">Social</option>
                    <option value="newsletter">Newsletter</option>
                  </select>

                  <select
                    value={filters.dateRange}
                    onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Any Time</option>
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                    <option value="year">This Year</option>
                  </select>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Search Results */}
        {searchResults && (
          <div className="max-w-4xl mx-auto">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                Found {searchResults.total_count} results
              </h2>
              {searchResults.processing_time && (
                <span className="text-sm text-gray-500">
                  in {searchResults.processing_time.toFixed(2)}s
                </span>
              )}
            </div>

            <div className="space-y-4">
              {searchResults.emails.map((email) => (
                <Card key={email.id} className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Mail className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{email.sender}</p>
                          <p className="text-sm text-gray-500">{email.sender_email}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={getPriorityColor(email.priority)}>
                          {email.priority}
                        </Badge>
                        <Badge className={getCategoryColor(email.category)}>
                          {email.category}
                        </Badge>
                        {email.similarity_score && (
                          <Badge variant="outline">
                            {Math.round(email.similarity_score * 100)}% match
                          </Badge>
                        )}
                      </div>
                    </div>

                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {email.subject}
                    </h3>

                    {email.summary && (
                      <p className="text-gray-600 mb-3 line-clamp-2">
                        {email.summary}
                      </p>
                    )}

                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <div className="flex items-center space-x-4">
                        <span className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {new Date(email.timestamp).toLocaleDateString()}
                        </span>
                        {email.starred && (
                          <span className="flex items-center">
                            <Star className="h-4 w-4 mr-1 text-yellow-500" />
                            Starred
                          </span>
                        )}
                        {email.priority === 'urgent' && (
                          <span className="flex items-center">
                            <AlertTriangle className="h-4 w-4 mr-1 text-red-500" />
                            Urgent
                          </span>
                        )}
                      </div>
                      <Button variant="ghost" size="sm">
                        View Email
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {searchResults.emails.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No results found
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Try adjusting your search terms or filters
                  </p>
                  <Button variant="outline" onClick={() => {
                    setQuery('')
                    setFilters({ priority: '', category: '', dateRange: '' })
                    setSearchResults(null)
                  }}>
                    Clear Search
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Search Tips */}
        {!searchResults && (
          <div className="max-w-4xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Search Tips
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-2">Natural Language Examples</h4>
                    <ul className="space-y-1 text-sm text-gray-600">
                      <li>• "emails about project deadline"</li>
                      <li>• "find invoices from last week"</li>
                      <li>• "meeting invitations with John"</li>
                      <li>• "urgent emails requiring action"</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Advanced Features</h4>
                    <ul className="space-y-1 text-sm text-gray-600">
                      <li>• Semantic search understands context</li>
                      <li>• Filter by priority and category</li>
                      <li>• Search within specific time ranges</li>
                      <li>• AI-powered relevance scoring</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}
