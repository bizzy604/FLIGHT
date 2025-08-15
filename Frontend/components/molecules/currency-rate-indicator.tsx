/**
 * Currency Rate Indicator Component
 * Shows exchange rate freshness and allows manual refresh
 */

"use client"

import React, { useState, useEffect } from "react"
import { RefreshCw, Clock, AlertTriangle, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { getExchangeRateInfo, refreshExchangeRate } from "@/utils/exchange-rate-manager"

interface CurrencyRateIndicatorProps {
  fromCurrency: string
  toCurrency: string
  onRateRefresh?: (newRate: number | null) => void
  className?: string
}

export function CurrencyRateIndicator({ 
  fromCurrency, 
  toCurrency, 
  onRateRefresh,
  className 
}: CurrencyRateIndicatorProps) {
  const [rateInfo, setRateInfo] = useState(getExchangeRateInfo(fromCurrency, toCurrency))
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Update rate info periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setRateInfo(getExchangeRateInfo(fromCurrency, toCurrency))
    }, 60000) // Check every minute

    return () => clearInterval(interval)
  }, [fromCurrency, toCurrency])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      const newRate = await refreshExchangeRate(fromCurrency, toCurrency)
      setRateInfo(getExchangeRateInfo(fromCurrency, toCurrency))
      onRateRefresh?.(newRate)
    } catch (error) {
      console.error('Failed to refresh exchange rate:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const getStatusInfo = () => {
    if (!rateInfo.hasRate) {
      return {
        icon: <AlertTriangle className="h-3 w-3" />,
        color: "destructive" as const,
        text: "No rate",
        tooltip: "Exchange rate not available"
      }
    }

    if (rateInfo.ageMinutes < 15) {
      return {
        icon: <CheckCircle className="h-3 w-3" />,
        color: "default" as const,
        text: `${rateInfo.ageMinutes}m ago`,
        tooltip: `Rate updated ${rateInfo.ageMinutes} minutes ago`
      }
    }

    if (rateInfo.ageMinutes < 60) {
      return {
        icon: <Clock className="h-3 w-3" />,
        color: "secondary" as const,
        text: `${rateInfo.ageMinutes}m ago`,
        tooltip: `Rate is ${rateInfo.ageMinutes} minutes old`
      }
    }

    const hours = Math.floor(rateInfo.ageMinutes / 60)
    return {
      icon: <AlertTriangle className="h-3 w-3" />,
      color: "destructive" as const,
      text: `${hours}h ago`,
      tooltip: `Rate is ${hours} hours old - may be inaccurate`
    }
  }

  const statusInfo = getStatusInfo()

  // Don't show indicator if currencies are the same
  if (fromCurrency === toCurrency) return null

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant={statusInfo.color} className="flex items-center gap-1 text-xs">
              {statusInfo.icon}
              {statusInfo.text}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div className="text-xs">
              <div>{statusInfo.tooltip}</div>
              {rateInfo.lastUpdated && (
                <div className="text-gray-400 mt-1">
                  Last updated: {rateInfo.lastUpdated.toLocaleTimeString()}
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <Button
        variant="ghost"
        size="sm"
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="h-6 w-6 p-0"
      >
        <RefreshCw className={`h-3 w-3 ${isRefreshing ? 'animate-spin' : ''}`} />
      </Button>
    </div>
  )
}

/**
 * Currency Conversion Notice Component
 */
interface CurrencyConversionNoticeProps {
  originalCurrency: string
  displayCurrency: string
  rateAge?: number
  className?: string
}

export function CurrencyConversionNotice({ 
  originalCurrency, 
  displayCurrency,
  rateAge,
  className 
}: CurrencyConversionNoticeProps) {
  if (originalCurrency === displayCurrency) return null

  const getWarningLevel = () => {
    if (!rateAge) return "info"
    if (rateAge < 30) return "info"
    if (rateAge < 60) return "warning"
    return "error"
  }

  const warningLevel = getWarningLevel()
  const bgColor = {
    info: "bg-blue-50 border-blue-200 text-blue-800",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-800", 
    error: "bg-red-50 border-red-200 text-red-800"
  }[warningLevel]

  return (
    <div className={`rounded-lg border p-3 text-sm ${bgColor} ${className}`}>
      <div className="flex items-start gap-2">
        {warningLevel === "error" && <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />}
        <div>
          <div className="font-medium">Currency Conversion Notice</div>
          <div className="mt-1">
            Prices shown in {displayCurrency} are converted from {originalCurrency} for your convenience. 
            Final charges will be processed in {originalCurrency}.
          </div>
          {rateAge && rateAge > 30 && (
            <div className="mt-2 text-xs opacity-80">
              Exchange rates are {rateAge} minutes old and may not reflect current market rates.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}