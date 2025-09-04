interface UploadResponse {
  success: boolean
  session_id: string
  chunks_processed: number
  domains: string[]
  message?: string
}

interface KnowledgeStatus {
  has_knowledge: boolean
  chunk_count: number
  domains: string[]
  session_id: string
}

interface ChatResponse {
  success: boolean
  response?: string
  sources?: Array<{
    source: string
    relevance_score: number
    content_preview: string
  }>
  metadata?: {
    chunks_retrieved: number
    processing_time_ms: number
    model_used: string
  }
  error?: string
  message?: string
}

interface KnowledgeChunk {
  id: string
  content: string
  metadata: {
    source: string
    topic?: string
    date?: string
    entities?: string[]
    category?: string
    tags?: string[]
  }
}

interface ComputeJobMetaData {
  [key: string]: any
}

interface ChatbotUseCaseData {
  id?: number
  job: ComputeJobMetaData
  result: Array<{
    knowledgeBase?: {
      chunks: KnowledgeChunk[]
      searchIndex?: Record<string, string[]>
    }
    domainInfo?: {
      domain: string
      entities: string[]
      timeRange?: string
      description?: string
    }
  }>
}

class ChatbotApiService {
  private baseUrl: string
  private sessionId: string

  constructor() {
    // 安全地获取环境变量
    this.baseUrl = this.getBaseUrlFromEnv()
    this.sessionId = this.generateSessionId()
  }

  private getBaseUrlFromEnv(): string {
    // 在浏览器环境中
    if (typeof window !== 'undefined') {
      return (window as any).__NEXT_PUBLIC_API_URL__ || 'http://localhost:8001'
    }
    
    // 在Node.js环境中
    try {
      // @ts-ignore
      return process?.env?.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
    } catch {
      return 'http://localhost:8001'
    }
  }

  async uploadKnowledge(
    chatbotData: ChatbotUseCaseData[]
  ): Promise<UploadResponse> {
    try {
      const allChunks = this.extractKnowledgeChunks(chatbotData)
      const domains = this.extractDomains(chatbotData)

      const response = await this.makeRequest(
        `${this.baseUrl}/api/v1/session/knowledge/upload`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Session-ID': this.sessionId
          },
          body: JSON.stringify({
            session_id: this.sessionId,
            knowledge_chunks: allChunks,
            domains: domains
          })
        }
      )

      return response
    } catch (error) {
      console.error('❌ Knowledge upload failed:', error)
      throw error
    }
  }

  async chat(message: string, config: any = {}): Promise<ChatResponse> {
    try {
      const requestBody = {
        session_id: this.sessionId,
        message: message,
        config: {
          max_tokens: config.maxTokens || 500,
          temperature: config.temperature || 0.7,
          model: config.model || undefined
        }
      }

      const response = await this.makeRequest(`${this.baseUrl}/api/v1/session/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': this.sessionId,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          Pragma: 'no-cache',
          Expires: '0'
        },
        body: JSON.stringify(requestBody)
      })

      return response
    } catch (error) {
      console.error('❌ Chat request failed:', error)
      throw error
    }
  }

  async getKnowledgeStatus(): Promise<KnowledgeStatus> {
    try {
      const response = await this.makeRequest(
        `${this.baseUrl}/api/v1/session/knowledge/status`,
        {
          headers: { 'X-Session-ID': this.sessionId }
        }
      )

      return response
    } catch (error) {
      console.error('❌ Knowledge status check failed:', error)
      throw error
    }
  }

  async healthCheck(): Promise<any> {
    try {
      const response = await this.makeRequest(`${this.baseUrl}/api/health`)
      return response
    } catch (error) {
      console.error('❌ Health check failed:', error)
      throw error
    }
  }

  private async makeRequest(url: string, options: RequestInit = {}): Promise<any> {
    // 检查fetch是否可用
    if (typeof fetch === 'undefined') {
      throw new Error('fetch is not available. Please ensure you are running in a browser environment or install node-fetch for Node.js.')
    }

    const response = await fetch(url, options)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ HTTP Error Response:', errorText)
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }

    return await response.json()
  }

  private extractKnowledgeChunks(
    chatbotData: ChatbotUseCaseData[]
  ): KnowledgeChunk[] {
    const chunks: KnowledgeChunk[] = []
    chatbotData.forEach((data) => {
      data.result.forEach((result) => {
        if (result.knowledgeBase?.chunks) {
          chunks.push(...result.knowledgeBase.chunks)
        }
      })
    })
    return chunks
  }

  private extractDomains(chatbotData: ChatbotUseCaseData[]): string[] {
    const domains = new Set<string>()
    chatbotData.forEach((data) => {
      data.result.forEach((result) => {
        if (result.domainInfo?.domain) {
          domains.add(result.domainInfo.domain)
        }
      })
    })
    return Array.from(domains)
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
  }

  getBaseUrl(): string {
    return this.baseUrl
  }

  getSessionId(): string {
    return this.sessionId
  }
}

export const chatbotApi = new ChatbotApiService()
export type {
  UploadResponse,
  KnowledgeStatus,
  ChatResponse,
  KnowledgeChunk,
  ChatbotUseCaseData
} 