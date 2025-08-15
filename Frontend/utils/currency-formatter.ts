/**
 * Currency Formatter Utility
 * Provides dynamic currency formatting based on actual currency codes
 */

// Currency symbol mapping
const CURRENCY_SYMBOLS: Record<string, string> = {
  'USD': '$',
  'EUR': '€',
  'GBP': '£',
  'INR': '₹',
  'AED': 'د.إ',
  'SGD': 'S$',
  'CAD': 'C$',
  'AUD': 'A$',
  'JPY': '¥',
  'CNY': '¥',
  'CHF': 'CHF',
  'SEK': 'kr',
  'NOK': 'kr',
  'DKK': 'kr',
  'PLN': 'zł',
  'CZK': 'Kč',
  'HUF': 'Ft',
  'RUB': '₽',
  'BRL': 'R$',
  'MXN': '$',
  'COP': '$',
  'CLP': '$',
  'PEN': 'S/',
  'ARS': '$',
  'ZAR': 'R',
  'EGP': '£',
  'SAR': '﷼',
  'QAR': '﷼',
  'KWD': 'د.ك',
  'BHD': '.د.ب',
  'OMR': '﷼',
  'JOD': 'د.ا',
  'LBP': '£',
  'TRY': '₺',
  'ILS': '₪',
  'KRW': '₩',
  'THB': '฿',
  'MYR': 'RM',
  'PHP': '₱',
  'IDR': 'Rp',
  'VND': '₫',
  'TWD': 'NT$',
  'HKD': 'HK$',
  'NZD': 'NZ$',
  'KES': 'KSh',
  'UGX': 'USh',
  'TZS': 'TSh',
  'ETB': 'Br',
  'RWF': 'RF',
  'GHS': '₵',
  'NGN': '₦',
  'XOF': 'CFA',
  'XAF': 'FCFA',
  'MAD': 'د.م.',
  'TND': 'د.ت',
  'DZD': 'د.ج'
}

// Locale mapping for proper number formatting
const CURRENCY_LOCALES: Record<string, string> = {
  'USD': 'en-US',
  'EUR': 'de-DE',
  'GBP': 'en-GB', 
  'INR': 'en-IN',
  'AED': 'ar-AE',
  'SGD': 'en-SG',
  'CAD': 'en-CA',
  'AUD': 'en-AU',
  'JPY': 'ja-JP',
  'CNY': 'zh-CN',
  'CHF': 'de-CH',
  'SEK': 'sv-SE',
  'NOK': 'no-NO',
  'DKK': 'da-DK',
  'PLN': 'pl-PL',
  'CZK': 'cs-CZ',
  'HUF': 'hu-HU',
  'RUB': 'ru-RU',
  'BRL': 'pt-BR',
  'MXN': 'es-MX',
  'COP': 'es-CO',
  'CLP': 'es-CL',
  'PEN': 'es-PE',
  'ARS': 'es-AR',
  'ZAR': 'en-ZA',
  'EGP': 'ar-EG',
  'SAR': 'ar-SA',
  'QAR': 'ar-QA',
  'KWD': 'ar-KW',
  'BHD': 'ar-BH',
  'OMR': 'ar-OM',
  'JOD': 'ar-JO',
  'LBP': 'ar-LB',
  'TRY': 'tr-TR',
  'ILS': 'he-IL',
  'KRW': 'ko-KR',
  'THB': 'th-TH',
  'MYR': 'ms-MY',
  'PHP': 'en-PH',
  'IDR': 'id-ID',
  'VND': 'vi-VN',
  'TWD': 'zh-TW',
  'HKD': 'en-HK',
  'NZD': 'en-NZ',
  'KES': 'en-KE',
  'UGX': 'en-UG',
  'TZS': 'sw-TZ',
  'ETB': 'am-ET',
  'RWF': 'rw-RW',
  'GHS': 'en-GH',
  'NGN': 'en-NG',
  'XOF': 'fr-SN',
  'XAF': 'fr-CM',
  'MAD': 'ar-MA',
  'TND': 'ar-TN',
  'DZD': 'ar-DZ'
}

/**
 * Get currency symbol for a given currency code
 */
export function getCurrencySymbol(currencyCode: string): string {
  return CURRENCY_SYMBOLS[currencyCode.toUpperCase()] || currencyCode.toUpperCase()
}

/**
 * Get appropriate locale for a given currency code
 */
export function getCurrencyLocale(currencyCode: string): string {
  return CURRENCY_LOCALES[currencyCode.toUpperCase()] || 'en-US'
}

/**
 * Format currency amount with proper symbol and locale formatting
 */
export function formatCurrency(amount: number, currencyCode: string): string {
  const symbol = getCurrencySymbol(currencyCode)
  const locale = getCurrencyLocale(currencyCode)
  
  try {
    // Use native Intl.NumberFormat for proper formatting
    const formatter = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currencyCode.toUpperCase(),
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    })
    return formatter.format(amount)
  } catch (error) {
    // Fallback to manual formatting if Intl fails
    const formattedNumber = amount.toLocaleString(locale)
    return `${symbol}${formattedNumber}`
  }
}

/**
 * Format currency amount with symbol only (no locale-specific formatting)
 */
export function formatCurrencySimple(amount: number, currencyCode: string): string {
  const symbol = getCurrencySymbol(currencyCode)
  return `${symbol}${amount.toLocaleString()}`
}

/**
 * Get currency symbol for UI indicators (smaller symbol for icons)
 */
export function getCurrencyIndicator(currencyCode: string): string {
  const symbolMap: Record<string, string> = {
    'USD': '$',
    'EUR': '€', 
    'GBP': '£',
    'INR': '₹',
    'AED': 'د',
    'SGD': 'S$',
    'JPY': '¥',
    'CNY': '¥'
  }
  return symbolMap[currencyCode.toUpperCase()] || currencyCode.toUpperCase().charAt(0)
}

/**
 * Check if currency uses decimal places
 */
export function currencyUsesDecimals(currencyCode: string): boolean {
  const noDecimalCurrencies = ['JPY', 'KRW', 'VND', 'CLP', 'PYG', 'RWF', 'UGX', 'VUV', 'XAF', 'XOF', 'XPF']
  return !noDecimalCurrencies.includes(currencyCode.toUpperCase())
}

/**
 * Format currency for display in tooltips and summaries
 */
export function formatCurrencyForDisplay(amount: number, currencyCode: string): string {
  if (amount === 0) return 'FREE'
  return formatCurrency(amount, currencyCode)
}