"use client"

import * as React from "react"
import { OTPInput, OTPInputContext } from "input-otp"
import { Dot } from "lucide-react"

import { cn } from "@/utils/cn"

// Extend the OTPInput props to include our custom className props
interface InputOTPProps extends React.ComponentProps<typeof OTPInput> {
  containerClassName?: string;
  className?: string;
}

// Create a type for the OTPInput component with our extended props
type OTPInputElement = React.ElementRef<typeof OTPInput>;

declare module 'input-otp' {
  interface OTPInputProps {
    containerClassName?: string;
  }
}

const InputOTP = React.forwardRef<OTPInputElement, InputOTPProps>(
  ({ className, containerClassName, ...props }, ref) => {
    const containerClass = cn(
      "flex items-center gap-2 has-[:disabled]:opacity-50",
      containerClassName
    );
    
    return (
      <div className={containerClass}>
        <OTPInput
          ref={ref}
          className={cn("disabled:cursor-not-allowed", className)}
          {...props}
        />
      </div>
    );
  }
);
InputOTP.displayName = "InputOTP"

const InputOTPGroup = React.forwardRef<
  React.ElementRef<"div">,
  React.ComponentPropsWithoutRef<"div">
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("flex items-center", className)} {...props} />
))
InputOTPGroup.displayName = "InputOTPGroup"

const InputOTPSlot = React.forwardRef<
  React.ElementRef<"div">,
  React.ComponentPropsWithoutRef<"div"> & { index: number }
>(({ index, className, ...props }, ref) => {
  const inputOTPContext = React.useContext(OTPInputContext);
  if (!inputOTPContext) return null;
  
  const { char, hasFakeCaret, isActive } = inputOTPContext.slots[index]

  return (
    <div
      ref={ref}
      className={cn(
        "relative flex h-10 w-10 items-center justify-center border-y border-r border-input text-sm transition-all first:rounded-l-md first:border-l last:rounded-r-md",
        isActive && "z-10 ring-2 ring-ring ring-offset-background",
        className
      )}
      {...props}
    >
      {char}
      {hasFakeCaret && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="h-4 w-px animate-caret-blink bg-foreground duration-1000" />
        </div>
      )}
    </div>
  )
})
InputOTPSlot.displayName = "InputOTPSlot"

const InputOTPSeparator = React.forwardRef<
  React.ElementRef<"div">,
  React.ComponentPropsWithoutRef<"div">
>(({ ...props }, ref) => (
  <div ref={ref} role="separator" {...props}>
    <Dot />
  </div>
))
InputOTPSeparator.displayName = "InputOTPSeparator"

export { InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator }
