"use client"

import { LoadingSpinner } from "../loading-spinner"
import { cn } from "@/utils/cn"

interface FullscreenLoadingOverlayProps {
  /** Whether the overlay should be visible */
  isVisible: boolean
  /** Custom message to display */
  message?: string
  /** Custom className for styling */
  className?: string
  /** Whether to show a backdrop blur effect */
  backdropBlur?: boolean
}

export function FullscreenLoadingOverlay({
  isVisible,
  message = "Searching for flights...",
  className,
  backdropBlur = true
}: FullscreenLoadingOverlayProps) {
  if (!isVisible) return null

  return (
    <div
      className={cn(
        "fixed inset-0 z-[9999] flex items-center justify-center transition-all duration-300 ease-in-out",
        backdropBlur ? "backdrop-blur-sm" : "",
        "bg-background/80 dark:bg-background/90",
        className
      )}
    >
      <div className="flex flex-col items-center space-y-6 p-8 rounded-2xl bg-card/90 dark:bg-card/90 border border-border/50 shadow-2xl animate-in fade-in-0 zoom-in-95 duration-300">
        {/* Large Loading Spinner */}
        <div className="relative">
          <LoadingSpinner className="h-16 w-16 text-primary animate-spin" />
          {/* Outer ring animation */}
          <div className="absolute inset-0 rounded-full border-4 border-primary/20 animate-pulse" />
        </div>
        
        {/* Loading Message */}
        <div className="text-center space-y-2">
          <h3 className="text-xl font-semibold text-foreground">
            {message}
          </h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Please wait while we search for the best flight options...
          </p>
        </div>
        
        {/* Animated dots */}
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]" />
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]" />
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
        </div>
        
        {/* Progress bar */}
        <div className="w-48 h-1 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full animate-pulse" style={{ animationDuration: '2s' }} />
        </div>
      </div>
    </div>
  )
}
