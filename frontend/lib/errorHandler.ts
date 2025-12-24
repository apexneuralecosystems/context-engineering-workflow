/**
 * Sanitizes error messages to prevent exposing internal server details
 * and provides user-friendly error messages
 */

interface SanitizedError {
  message: string
  isUserFriendly: boolean
}

/**
 * Sanitizes error messages for display to users
 */
export function sanitizeError(error: any): string {
  if (!error) {
    return 'An unexpected error occurred. Please try again.'
  }

  // If it's already a string, check if it's user-friendly
  if (typeof error === 'string') {
    return sanitizeErrorMessage(error)
  }

  // Handle Axios errors
  if (error.response) {
    const status = error.response.status
    const data = error.response.data

    // Check for API response format
    if (data?.message) {
      return sanitizeErrorMessage(data.message)
    }

    if (data?.detail) {
      return sanitizeErrorMessage(data.detail)
    }

    // Handle HTTP status codes
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input and try again.'
      case 401:
        return 'Authentication failed. Please check your API keys.'
      case 403:
        return 'Access denied. You do not have permission to perform this action.'
      case 404:
        return 'The requested resource was not found.'
      case 408:
        return 'Request timeout. Please try again.'
      case 413:
        return 'File too large. Please upload a smaller file.'
      case 429:
        return 'Too many requests. Please wait a moment and try again.'
      case 500:
        return 'Internal server error. Please try again later.'
      case 502:
        return 'Service temporarily unavailable. Please try again later.'
      case 503:
        return 'Service unavailable. Please try again later.'
      default:
        return 'An error occurred. Please try again.'
    }
  }

  // Handle network errors
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return 'Request timed out. Please try again.'
  }

  if (error.message?.includes('Network Error') || error.code === 'ERR_NETWORK') {
    return 'Network error. Please check your connection and try again.'
  }

  // Handle error objects with message property
  if (error.message) {
    return sanitizeErrorMessage(error.message)
  }

  return 'An unexpected error occurred. Please try again.'
}

/**
 * Sanitizes error message strings to remove internal details
 */
function sanitizeErrorMessage(message: string): string {
  if (!message) {
    return 'An error occurred. Please try again.'
  }

  const msg = message.toLowerCase()

  // Remove stack traces and technical details
  if (msg.includes('traceback') || msg.includes('stack trace') || msg.includes('at ')) {
    return 'An internal error occurred. Please try again.'
  }

  // Sanitize common internal error patterns
  const internalPatterns = [
    /internal server error/i,
    /database error/i,
    /connection.*refused/i,
    /sql.*error/i,
    /exception.*occurred/i,
    /traceback/i,
    /file.*not found/i,
    /module.*not found/i,
    /import.*error/i,
  ]

  for (const pattern of internalPatterns) {
    if (pattern.test(message)) {
      return 'An internal error occurred. Please try again later.'
    }
  }

  // Sanitize API key errors (don't expose key details)
  if (msg.includes('api key') || msg.includes('api_key') || msg.includes('authentication')) {
    if (msg.includes('invalid') || msg.includes('missing') || msg.includes('required')) {
      return 'API authentication failed. Please check your configuration.'
    }
    return 'Authentication error. Please check your API keys.'
  }

  // Sanitize file path errors
  if (msg.includes('c:\\') || msg.includes('/home/') || msg.includes('/var/') || msg.includes('\\')) {
    return 'File processing error. Please try again.'
  }

  // Keep user-friendly messages
  const userFriendlyPatterns = [
    /please.*upload/i,
    /file.*too large/i,
    /invalid.*file/i,
    /document.*not.*processed/i,
    /please.*initialize/i,
    /not.*found/i,
  ]

  for (const pattern of userFriendlyPatterns) {
    if (pattern.test(message)) {
      return message // Keep user-friendly messages as-is
    }
  }

  // If message looks technical, sanitize it
  if (message.length > 200 || message.includes('Error:') || message.includes('Exception:')) {
    return 'An error occurred. Please try again.'
  }

  // Return the message if it seems safe
  return message
}

/**
 * Gets a user-friendly error message based on error type
 */
export function getUserFriendlyError(error: any, context?: 'initialize' | 'upload' | 'query' | 'status'): string {
  const sanitized = sanitizeError(error)

  // Add context-specific messages if needed
  if (sanitized === 'An unexpected error occurred. Please try again.' && context) {
    switch (context) {
      case 'initialize':
        return 'Failed to initialize the assistant. Please check your configuration and try again.'
      case 'upload':
        return 'Failed to upload document. Please ensure the file is a valid PDF and try again.'
      case 'query':
        return 'Failed to process your query. Please try again or rephrase your question.'
      case 'status':
        return 'Unable to check assistant status. The service may be unavailable.'
      default:
        return sanitized
    }
  }

  return sanitized
}

