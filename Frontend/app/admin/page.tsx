"use client"
// import { DashboardMetrics, RecentBookings, SystemStatus, AdminTools } from "@/components/organisms"
import { Protect } from '@clerk/nextjs'

export default function AdminDashboardPage() {
  return (
    // <Protect
    // permission="org:team_settings:manage"
    // fallback={<p>You are not allowed to see this section.</p>}
    // >
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of bookings, revenue, and system status</p>
      </div>

      {/* TODO: Create DashboardMetrics component */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h2 className="text-lg font-semibold text-blue-900 mb-2">Dashboard Metrics</h2>
        <p className="text-blue-700">Component not yet implemented</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <div className="md:col-span-1 lg:col-span-5">
          {/* TODO: Create RecentBookings component */}
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <h2 className="text-lg font-semibold text-green-900 mb-2">Recent Bookings</h2>
            <p className="text-green-700">Component not yet implemented</p>
          </div>
        </div>
        <div className="md:col-span-1 lg:col-span-2">
          <div className="space-y-6">
            {/* TODO: Create SystemStatus component */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <h2 className="text-lg font-semibold text-yellow-900 mb-2">System Status</h2>
              <p className="text-yellow-700">Component not yet implemented</p>
            </div>
            {/* TODO: Create AdminTools component */}
            <div className="bg-purple-50 border border-purple-200 rounded-md p-4">
              <h2 className="text-lg font-semibold text-purple-900 mb-2">Admin Tools</h2>
              <p className="text-purple-700">Component not yet implemented</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

