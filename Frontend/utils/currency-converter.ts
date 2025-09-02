/**
 * Currency Conversion and Display System
 * Handles both display currency and actual pricing currency
 */

// Exchange rates (should be fetched from API in production)
interface ExchangeRates {
  [key: string]: {
    [key: string]: number
  }
}

// Mock exchange rates - in production, fetch from API like exchangerate-api.io
const MOCK_EXCHANGE_RATES: ExchangeRates = {
  'KES': {
    'USD': 0.0077,  // 1 KES = 0.0077 USD
    'EUR': 0.0070,  // 1 KES = 0.0070 EUR
    'GBP': 0.0061,  // 1 KES = 0.0061 GBP
    'KES': 1.0
  },
  'USD': {
    'KES': 129.87, // 1 USD = 129.87 KES
    'EUR': 0.91,   // 1 USD = 0.91 EUR
    'GBP': 0.79,   // 1 USD = 0.79 GBP
    'USD': 1.0
  },
  'EUR': {
    'USD': 1.10,   // 1 EUR = 1.10 USD
    'KES': 142.86, // 1 EUR = 142.86 KES
    'GBP': 0.87,   // 1 EUR = 0.87 GBP
    'EUR': 1.0
  },
  'INR': {
    'USD': 0.012,  // 1 INR = 0.012 USD
    'EUR': 0.011,  // 1 INR = 0.011 EUR
    'KES': 1.56,   // 1 INR = 1.56 KES
    'INR': 1.0
  }
}

/**
 * Get user's preferred currency based on location/settings
 */
export function getUserPreferredCurrency(): string {
  // Method 1: Check user settings/preferences (if stored)
  const storedCurrency = localStorage.getItem('preferred_currency')
  if (storedCurrency) {
    return storedCurrency
  }

  // Method 2: Detect from browser locale
  try {
    const userLocale = navigator.language || 'en-US'
    const currencyMap: { [key: string]: string } = {
      'en-US': 'USD',
      'en-GB': 'GBP', 
      'en-CA': 'CAD',
      'en-AU': 'AUD',
      'de-DE': 'EUR',
      'fr-FR': 'EUR',
      'es-ES': 'EUR',
      'it-IT': 'EUR',
      'nl-NL': 'EUR',
      'en-KE': 'KES',
      'sw-KE': 'KES',
      'en-NG': 'NGN',
      'ar-AE': 'AED',
      'zh-CN': 'CNY',
      'ja-JP': 'JPY',
      'ko-KR': 'KRW',
      'hi-IN': 'INR',
      'en-IN': 'INR'
    }
    
    return currencyMap[userLocale] || currencyMap[userLocale.split('-')[0]] || 'USD'
  } catch {
    return 'USD' // Safe fallback
  }
}

/**
 * Convert amount from one currency to another
 */
export function convertCurrency(
  amount: number,
  fromCurrency: string,
  toCurrency: string
): number {
  if (fromCurrency === toCurrency) {
    return amount
  }

  const rate = MOCK_EXCHANGE_RATES[fromCurrency]?.[toCurrency]
  if (!rate) {
    console.warn(`Exchange rate not found for ${fromCurrency} to ${toCurrency}`)
    return amount // Return original amount if no rate available
  }

  return Math.round(amount * rate * 100) / 100 // Round to 2 decimal places
}

/**
 * Get real-time exchange rates (production implementation)
 */
export async function fetchExchangeRates(): Promise<ExchangeRates | null> {
  try {
    // In production, use a service like:
    // - exchangerate-api.io
    // - fixer.io  
    // - currencylayer.com
    
    const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD')
    if (!response.ok) throw new Error('Failed to fetch rates')
    
    const data = await response.json()
    
    // Transform the response to our format
    // This is just an example - implement based on your chosen API
    return {
      'USD': data.rates,
      // ... transform other base currencies
    }
  } catch (error) {
    console.error('Failed to fetch exchange rates:', error)
    return null
  }
}

/**
 * Display price with conversion information for international users
 */
export interface PriceDisplayInfo {
  originalAmount: number
  originalCurrency: string
  convertedAmount?: number
  displayCurrency: string
  showConversion: boolean
  displayText: string
  tooltipText?: string
}

export function getPriceDisplayInfo(
  originalAmount: number,
  originalCurrency: string,
  userPreferredCurrency?: string
): PriceDisplayInfo {
  const preferredCurrency = userPreferredCurrency || getUserPreferredCurrency()
  const showConversion = originalCurrency !== preferredCurrency

  if (!showConversion) {
    return {
      originalAmount,
      originalCurrency,
      displayCurrency: originalCurrency,
      showConversion: false,
      displayText: formatCurrencyAmount(originalAmount, originalCurrency)
    }
  }

  const convertedAmount = convertCurrency(originalAmount, originalCurrency, preferredCurrency)
  
  return {
    originalAmount,
    originalCurrency,
    convertedAmount,
    displayCurrency: preferredCurrency,
    showConversion: true,
    displayText: formatCurrencyAmount(convertedAmount, preferredCurrency),
    tooltipText: `Original price: ${formatCurrencyAmount(originalAmount, originalCurrency)}`
  }
}

/**
 * Format currency amount (helper function)
 */
function formatCurrencyAmount(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(amount)
  } catch {
    // Fallback formatting
    const symbols: { [key: string]: string } = {
      'USD': '$', 'EUR': '€', 'GBP': '£', 'KES': 'KSh', 'INR': '₹'
    }
    const symbol = symbols[currency] || currency
    return `${symbol}${amount.toLocaleString()}`
  }
}

/**
 * Smart price display component data
 */
export interface SmartPriceDisplay {
  primary: string      // Main price to show
  secondary?: string   // Converted price (if different)
  tooltip?: string     // Additional info for tooltip
  isConverted: boolean // Whether price was converted
}

export function getSmartPriceDisplay(
  amount: number,
  apiCurrency: string,
  options?: {
    userCurrency?: string
    showBothPrices?: boolean
    format?: 'tooltip' | 'inline' | 'stacked'
  }
): SmartPriceDisplay {
  const userCurrency = options?.userCurrency || getUserPreferredCurrency()
  const showBothPrices = options?.showBothPrices ?? true
  const format = options?.format || 'tooltip'

  if (apiCurrency === userCurrency) {
    // Same currency - no conversion needed
    return {
      primary: formatCurrencyAmount(amount, apiCurrency),
      isConverted: false
    }
  }

  // Different currencies - show conversion
  const convertedAmount = convertCurrency(amount, apiCurrency, userCurrency)
  const originalFormatted = formatCurrencyAmount(amount, apiCurrency)
  const convertedFormatted = formatCurrencyAmount(convertedAmount, userCurrency)

  switch (format) {
    case 'inline':
      return {
        primary: `${convertedFormatted} (${originalFormatted})`,
        isConverted: true
      }
    
    case 'stacked':
      return {
        primary: convertedFormatted,
        secondary: originalFormatted,
        isConverted: true
      }
    
    case 'tooltip':
    default:
      return {
        primary: convertedFormatted,
        tooltip: `Original price: ${originalFormatted}`,
        isConverted: true
      }
  }
}

/**
 * Set user's preferred currency (save to localStorage)
 */
export function setUserPreferredCurrency(currency: string): void {
  localStorage.setItem('preferred_currency', currency)
}

/**
 * Currency conversion disclaimer
 */
export function getCurrencyDisclaimer(originalCurrency: string, displayCurrency: string): string {
  if (originalCurrency === displayCurrency) return ''
  
  return `Prices shown in ${displayCurrency} are approximate conversions from ${originalCurrency}. Final charges will be in ${originalCurrency}.`
}