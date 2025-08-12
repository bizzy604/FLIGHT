import type { ReactNode } from "react"
import { AdminSidebar, AdminHeader, SimpleFooter } from "@/components/organisms"

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <AdminHeader />
      <div className="flex flex-1">
        <AdminSidebar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
      <SimpleFooter />
    </div>
  )
}

