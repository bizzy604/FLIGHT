"use client"
import { DashboardMetrics } from "@/components/admin/dashboard-metrics"
import { RecentBookings } from "@/components/admin/recent-bookings"
import { SystemStatus } from "@/components/admin/system-status"
import { AdminTools } from "@/components/admin/admin-tools"
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

      <DashboardMetrics />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <div className="md:col-span-1 lg:col-span-5">
          <RecentBookings />
        </div>
        <div className="md:col-span-1 lg:col-span-2">
          <div className="space-y-6">
            <SystemStatus />
            <AdminTools />
          </div>
        </div>
      </div>
    </div>
  )
}

