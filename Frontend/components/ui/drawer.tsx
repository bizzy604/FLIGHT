"use client"

import * as React from "react"
import * as Dialog from "@radix-ui/react-dialog"
import { cn } from "@/utils/cn"

const Drawer = ({
  children,
  ...props
}: React.ComponentProps<typeof Dialog.Root>) => (
  <Dialog.Root {...props}>
    {children}
  </Dialog.Root>
)
Drawer.displayName = "Drawer"

const DrawerTrigger = ({
  children,
  ...props
}: { children: React.ReactNode } & React.HTMLAttributes<HTMLButtonElement>) => (
  <Dialog.Trigger asChild {...props}>
    {children}
  </Dialog.Trigger>
)
DrawerTrigger.displayName = "DrawerTrigger"

const DrawerPortal = Dialog.Portal
const DrawerClose = Dialog.Close

const DrawerOverlay = React.forwardRef<
  React.ElementRef<typeof Dialog.Overlay>,
  React.ComponentProps<typeof Dialog.Overlay>
>(({ className, ...props }, ref) => (
  <Dialog.Overlay
    ref={ref}
    className={cn("fixed inset-0 z-50 bg-black/80", className)}
    {...props}
  />
))
DrawerOverlay.displayName = "DrawerOverlay"

interface DrawerContentProps extends React.ComponentProps<typeof Dialog.Content> {
  showBar?: boolean
}

const DrawerContent = React.forwardRef<
  React.ElementRef<typeof Dialog.Content>,
  DrawerContentProps
>(({ className, children, showBar = true, ...props }, ref) => (
  <DrawerPortal>
    <DrawerOverlay />
    <Dialog.Content
      ref={ref}
      className={cn(
        "fixed inset-x-0 bottom-0 z-50 mt-24 flex h-auto flex-col rounded-t-[10px] border bg-background",
        className
      )}
      {...props}
    >
      {showBar && (
        <div className="mx-auto mt-4 h-2 w-[100px] rounded-full bg-muted" />
      )}
      {children}
    </Dialog.Content>
  </DrawerPortal>
))
DrawerContent.displayName = "DrawerContent"

const DrawerHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn("grid gap-1.5 p-4 text-center sm:text-left", className)}
    {...props}
  />
)
DrawerHeader.displayName = "DrawerHeader"

const DrawerFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn("mt-auto flex flex-col gap-2 p-4", className)}
    {...props}
  />
)
DrawerFooter.displayName = "DrawerFooter"

const DrawerTitle = React.forwardRef<
  React.ElementRef<typeof Dialog.Title>,
  React.ComponentProps<typeof Dialog.Title>
>(({ className, ...props }, ref) => (
  <Dialog.Title
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
DrawerTitle.displayName = "DrawerTitle"

const DrawerDescription = React.forwardRef<
  React.ElementRef<typeof Dialog.Description>,
  React.ComponentProps<typeof Dialog.Description>
>(({ className, ...props }, ref) => (
  <Dialog.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
DrawerDescription.displayName = "DrawerDescription"

export {
  Drawer,
  DrawerTrigger,
  DrawerPortal,
  DrawerOverlay,
  DrawerClose,
  DrawerContent,
  DrawerHeader,
  DrawerFooter,
  DrawerTitle,
  DrawerDescription,
}
