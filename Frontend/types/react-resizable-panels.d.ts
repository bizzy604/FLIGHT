declare module 'react-resizable-panels' {
  import * as React from 'react';

  export interface PanelGroupProps extends React.HTMLAttributes<HTMLDivElement> {
    autoSaveId?: string;
    children?: React.ReactNode;
    className?: string;
    direction?: 'horizontal' | 'vertical';
    id?: string;
    onLayout?: (sizes: number[]) => void;
    style?: React.CSSProperties;
    tagName?: keyof JSX.IntrinsicElements;
  }

  export interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
    children?: React.ReactNode;
    className?: string;
    defaultSize?: number;
    id?: string;
    maxSize?: number;
    minSize?: number;
    onCollapse?: () => void;
    onExpand?: () => void;
    onResize?: (size: number) => void;
    order?: number;
    style?: React.CSSProperties;
    tagName?: keyof JSX.IntrinsicElements;
  }

  export interface PanelResizeHandleProps extends React.HTMLAttributes<HTMLDivElement> {
    children?: React.ReactNode;
    className?: string;
    disabled?: boolean;
    id?: string;
    style?: React.CSSProperties;
    tagName?: keyof JSX.IntrinsicElements;
  }

  export const PanelGroup: React.FC<PanelGroupProps> & {
    displayName?: string;
  };
  
  export const Panel: React.FC<PanelProps> & {
    displayName?: string;
  };
  
  export const PanelResizeHandle: React.FC<PanelResizeHandleProps> & {
    displayName?: string;
  };

  // Add the default export for backward compatibility
  const ResizablePanels: {
    PanelGroup: typeof PanelGroup;
    Panel: typeof Panel;
    PanelResizeHandle: typeof PanelResizeHandle;
  };

  export default ResizablePanels;
}
