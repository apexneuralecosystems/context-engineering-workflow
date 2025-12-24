import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003'

// Standard API Response Format
export interface APIResponse<T = any> {
  status_code: number
  status: boolean
  message: string
  path: string
  data: T
}

export interface QueryResponse {
  status: 'OK' | 'INSUFFICIENT_CONTEXT'
  source_used: 'MEMORY' | 'RAG' | 'WEB' | 'TOOL' | 'NONE'
  answer: string
  citations: Array<{
    label: string
    locator: string
    page_number?: number
    chunk_index?: number
    score?: number
    content?: string
  }>
  confidence: number
  missing: string[]
  final_response?: string
  context_sources?: {
    rag_result?: any
    memory_result?: any
    web_result?: any
    tool_result?: any
  }
  evaluation_result?: {
    relevant_sources?: string[]
    relevance_scores?: Record<string, number>
    reasoning?: string
  }
}

export interface DocumentUploadResponse {
  success: boolean
  message: string
  document_name?: string
}

export interface AssistantStatus {
  initialized: boolean
  document_processed: boolean
  current_document?: string
}

/**
 * Helper function to handle API responses and extract data
 */
function handleResponse<T>(response: APIResponse<T>): T {
  if (!response.status) {
    throw new Error(response.message || 'Request failed')
  }
  return response.data
}

/**
 * Initialize the research assistant
 */
export async function initializeAssistant(): Promise<AssistantStatus> {
  try {
    const response = await axios.post<APIResponse<AssistantStatus>>(
      `${API_URL}/api/initialize`,
      {},
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000,
      }
    )
    return handleResponse(response.data)
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      const apiResponse = error.response?.data as APIResponse
      if (apiResponse?.message) {
        throw new Error(apiResponse.message)
      }
      throw new Error(error.response?.data?.detail || error.message || 'Failed to initialize assistant')
    }
    throw new Error('An unexpected error occurred')
  }
}

/**
 * Upload and process a document
 */
export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post<APIResponse<DocumentUploadResponse>>(
      `${API_URL}/api/upload-document`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes for document processing
      }
    )
    return handleResponse(response.data)
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      const apiResponse = error.response?.data as APIResponse
      if (apiResponse?.message) {
        throw new Error(apiResponse.message)
      }
      throw new Error(error.response?.data?.detail || error.message || 'Failed to upload document')
    }
    throw new Error('An unexpected error occurred')
  }
}

/**
 * Search query endpoint
 */
export async function searchQuery(query: string, user_id?: string, thread_id?: string): Promise<QueryResponse> {
  try {
    const response = await axios.post<APIResponse<QueryResponse>>(
      `${API_URL}/api/query`,
      { 
        query,
        user_id: user_id || 'web_user',
        thread_id: thread_id || `web_session_${Date.now()}`
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 300000, // 5 minutes timeout for complex queries (RAG + Web + Memory + Synthesis)
      }
    )
    return handleResponse(response.data)
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      const apiResponse = error.response?.data as APIResponse
      if (apiResponse?.message) {
        throw new Error(apiResponse.message)
      }
      throw new Error(error.response?.data?.detail || error.message || 'Failed to process query')
    }
    throw new Error('An unexpected error occurred')
  }
}

/**
 * Get assistant status
 */
export async function getAssistantStatus(): Promise<AssistantStatus> {
  try {
    const response = await axios.get<APIResponse<AssistantStatus>>(
      `${API_URL}/api/status`,
      {
        timeout: 5000,
      }
    )
    return handleResponse(response.data)
  } catch (error: any) {
    // Return default status if API is not available
    return {
      initialized: false,
      document_processed: false,
    }
  }
}

/**
 * Health check endpoint
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await axios.get<APIResponse>(`${API_URL}/health`, {
      timeout: 5000,
    })
    return response.data.status === true
  } catch {
    return false
  }
}
