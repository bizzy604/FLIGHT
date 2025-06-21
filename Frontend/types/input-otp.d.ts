declare module 'input-otp' {
  import * as React from 'react';

  export interface OTPInputContextValue {
    slots: Array<{
      char: string;
      hasFakeCaret: boolean;
      isActive: boolean;
    }>;
  }

  export const OTPInputContext: React.Context<OTPInputContextValue | null>;

  export interface OTPInputProps extends React.HTMLAttributes<HTMLDivElement> {
    maxLength?: number;
    value?: string;
    onChange?: (value: string) => void;
    children: React.ReactNode;
    render: (props: { value: string }) => React.ReactNode;
  }

  export const OTPInput: React.ForwardRefExoticComponent<
    OTPInputProps & React.RefAttributes<HTMLDivElement>
  >;
}
