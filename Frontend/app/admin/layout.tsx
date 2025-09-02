import type { ReactNode } from "react"
// import { AdminSidebar, AdminHeader, SimpleFooter } from "@/components/organisms"
import { SimpleFooter } from "@/components/organisms"

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* TODO: Create AdminHeader component */}
      <div className="bg-gray-800 text-white p-4">
        <h1 className="text-xl font-bold">Admin Header</h1>
        <p className="text-gray-300">Component not yet implemented</p>
      </div>
      
      <div className="flex flex-1">
        {/* TODO: Create AdminSidebar component */}
        <div className="w-64 bg-gray-100 p-4">
          <h2 className="text-lg font-semibold mb-4">Admin Sidebar</h2>
          <p className="text-gray-600">Component not yet implemented</p>
        </div>
        
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
      <SimpleFooter />
    </div>
  )
}

