"use client"

import React, { Component, useState, useEffect } from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

// Props for the class component error boundary
interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  onReset?: () => void
}

// State for the error boundary
interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

// Class component for catching React errors
class ErrorBoundaryClass extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { 
      hasError: false,
      error: null
    }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render shows the fallback UI
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Log error only in development
    if (process.env.NODE_ENV === 'development') {
      console.error("Error caught by boundary:", error, info)
    }
  }

  resetErrorBoundary = () => {
    // Reset the error state
    this.setState({ hasError: false, error: null })
    
    // Call onReset callback if provided
    if (this.props.onReset) {
      this.props.onReset()
    }
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI or the provided fallback
      return this.props.fallback || (
        <Alert variant="destructive" className="my-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Something went wrong</AlertTitle>
          <AlertDescription>
            <p className="mb-4">We encountered an error while rendering this content.</p>
            <p className="mb-4 text-sm text-muted-foreground">
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={this.resetErrorBoundary}
              className="flex items-center"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )
    }

    return this.props.children
  }
}

// Functional wrapper component for better hooks integration
export function ErrorBoundary({ 
  children, 
  fallback,
  onReset 
}: ErrorBoundaryProps) {
  // Use for global error handling if needed
  const [globalError, setGlobalError] = useState(false)

  useEffect(() => {
    const handleGlobalError = () => {
      setGlobalError(true)
    }

    window.addEventListener("unhandledrejection", handleGlobalError)
    
    return () => {
      window.removeEventListener("unhandledrejection", handleGlobalError)
    }
  }, [])

  // Reset handler for global errors
  const handleReset = () => {
    setGlobalError(false)
    if (onReset) onReset()
  }

  // Show global error UI if needed
  if (globalError) {
    return (
      <Alert variant="destructive" className="my-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Something went wrong</AlertTitle>
        <AlertDescription>
          <p className="mb-4">We encountered an unexpected error.</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              handleReset()
              window.location.reload()
            }}
            className="flex items-center"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  // Use the class component for React errors
  return (
    <ErrorBoundaryClass fallback={fallback} onReset={onReset}>
      {children}
    </ErrorBoundaryClass>
  )
}