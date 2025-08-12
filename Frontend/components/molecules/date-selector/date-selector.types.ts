export interface DateSelectorProps {
  label?: string
  value?: Date
  onChange: (date: Date | undefined) => void
  placeholder?: string
  disabled?: boolean
  minDate?: Date
  maxDate?: Date
  className?: string
  error?: string
}

export interface DateRangeProps {
  departDate?: Date
  returnDate?: Date
  onDepartDateChange: (date: Date | undefined) => void
  onReturnDateChange: (date: Date | undefined) => void
  disabled?: boolean
  minDate?: Date
  maxDate?: Date
  className?: string
  showReturnDate?: boolean
}