declare module 'vaul' {
  import * as React from 'react';

  export interface DrawerProps {
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
    children: React.ReactNode;
    className?: string;
    overlayClassName?: string;
    shouldScaleBackground?: boolean;
    scrollLockTimeout?: number;
    onDrag?: (event: React.PointerEvent<HTMLDivElement>) => void;
    onRelease?: (event: React.PointerEvent<HTMLDivElement>) => void;
  }

  export const Drawer: React.FC<DrawerProps> & {
    Trigger: React.FC<{ children: React.ReactNode }>;
    Content: React.FC<{ children: React.ReactNode; className?: string }>;
    Header: React.FC<{ children: React.ReactNode; className?: string }>;
    Body: React.FC<{ children: React.ReactNode; className?: string }>;
    Footer: React.FC<{ children: React.ReactNode; className?: string }>;
    Close: React.FC<{ children: React.ReactNode; className?: string }>;
  };
}
