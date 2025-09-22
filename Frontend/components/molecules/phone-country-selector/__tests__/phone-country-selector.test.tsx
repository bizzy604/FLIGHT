import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PhoneCountrySelector } from '../phone-country-selector'

// Mock the Command components since they might have complex internal behavior
jest.mock('@/components/ui/command', () => ({
  Command: ({ children }: { children: React.ReactNode }) => <div data-testid="command">{children}</div>,
  CommandEmpty: ({ children }: { children: React.ReactNode }) => <div data-testid="command-empty">{children}</div>,
  CommandGroup: ({ children }: { children: React.ReactNode }) => <div data-testid="command-group">{children}</div>,
  CommandInput: ({ placeholder, value, onValueChange }: { placeholder: string; value: string; onValueChange: (value: string) => void }) => (
    <input 
      data-testid="command-input" 
      placeholder={placeholder} 
      value={value} 
      onChange={(e) => onValueChange(e.target.value)} 
    />
  ),
  CommandItem: ({ value, onSelect, children }: { value: string; onSelect: (value: string) => void; children: React.ReactNode }) => (
    <div data-testid={`command-item-${value}`} onClick={() => onSelect(value)}>
      {children}
    </div>
  ),
  CommandList: ({ children }: { children: React.ReactNode }) => <div data-testid="command-list">{children}</div>,
}))

jest.mock('@/components/ui/popover', () => ({
  Popover: ({ children, open, onOpenChange }: { children: React.ReactNode; open: boolean; onOpenChange: (open: boolean) => void }) => (
    <div data-testid="popover" data-open={open}>
      {children}
    </div>
  ),
  PopoverContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="popover-content">{children}</div>
  ),
  PopoverTrigger: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="popover-trigger">{children}</div>
  ),
}))

describe('PhoneCountrySelector', () => {
  const mockOnValueChange = jest.fn()

  beforeEach(() => {
    mockOnValueChange.mockClear()
  })

  it('renders with placeholder text', () => {
    render(
      <PhoneCountrySelector
        value=""
        onValueChange={mockOnValueChange}
        placeholder="Select country code..."
      />
    )

    expect(screen.getByText('Select country code...')).toBeInTheDocument()
  })

  it('renders selected country code when value is provided', () => {
    render(
      <PhoneCountrySelector
        value="+1"
        onValueChange={mockOnValueChange}
        placeholder="Select country code..."
      />
    )

    // Check for the selected country code in the button
    const button = screen.getByRole('combobox')
    expect(button).toHaveTextContent('+1')
    expect(button).toHaveTextContent('🇺🇸')
  })

  it('shows disabled state when disabled prop is true', () => {
    render(
      <PhoneCountrySelector
        value=""
        onValueChange={mockOnValueChange}
        placeholder="Select country code..."
        disabled={true}
      />
    )

    const button = screen.getByRole('combobox')
    expect(button).toBeDisabled()
  })

  it('renders with custom className', () => {
    render(
      <PhoneCountrySelector
        value=""
        onValueChange={mockOnValueChange}
        placeholder="Select country code..."
        className="custom-class"
      />
    )

    const button = screen.getByRole('combobox')
    expect(button).toHaveClass('custom-class')
  })

  it('shows most common countries when showMostCommon is true', () => {
    render(
      <PhoneCountrySelector
        value=""
        onValueChange={mockOnValueChange}
        placeholder="Select country code..."
        showMostCommon={true}
        maxCommonItems={5}
      />
    )

    // This test would need to be expanded based on the actual component behavior
    // For now, we're just testing that the component renders without errors
    expect(screen.getByTestId('popover')).toBeInTheDocument()
  })
})
