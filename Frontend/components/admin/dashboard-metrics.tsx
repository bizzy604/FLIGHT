"use client"

import { useState, useEffect } from "react"
import { ArrowDown, ArrowUp, DollarSign, Users, Plane } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"

export function DashboardMetrics() {
  const [isLoading, setIsLoading] = useState(true)
  const [metrics, setMetrics] = useState({
    totalBookings: 0,
    todayBookings: 0,
    todayRevenue: 0,
    activeUsers: 0,
    bookingTrend: 0,
    revenueTrend: 0,
  })

  useEffect(() => {
    // Simulate API call to fetch metrics
    const fetchMetrics = async () => {
      try {
        // In a real app, this would be an API call
        await new Promise((resolve) => setTimeout(resolve, 1000))

        setMetrics({
          totalBookings: 12458,
          todayBookings: 142,
          todayRevenue: 45780,
          activeUsers: 328,
          bookingTrend: 12.5,
          revenueTrend: 8.2,
        })
      } catch (error) {
        console.error("Failed to fetch metrics:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="min-h-[140px] flex items-center justify-center">
            <LoadingSpinner />
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Bookings</CardTitle>
          <Plane className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.totalBookings.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">+{metrics.todayBookings} today</p>
          <div className="mt-2 flex items-center text-xs">
            {metrics.bookingTrend > 0 ? (
              <>
                <ArrowUp className="mr-1 h-3 w-3 text-green-500" />
                <span className="text-green-500">{metrics.bookingTrend}% increase</span>
              </>
            ) : (
              <>
                <ArrowDown className="mr-1 h-3 w-3 text-red-500" />
                <span className="text-red-500">{Math.abs(metrics.bookingTrend)}% decrease</span>
              </>
            )}
            <span className="ml-1 text-muted-foreground">from last month</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Today's Revenue</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">${metrics.todayRevenue.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">{metrics.todayBookings} bookings today</p>
          <div className="mt-2 flex items-center text-xs">
            {metrics.revenueTrend > 0 ? (
              <>
                <ArrowUp className="mr-1 h-3 w-3 text-green-500" />
                <span className="text-green-500">{metrics.revenueTrend}% increase</span>
              </>
            ) : (
              <>
                <ArrowDown className="mr-1 h-3 w-3 text-red-500" />
                <span className="text-red-500">{Math.abs(metrics.revenueTrend)}% decrease</span>
              </>
            )}
            <span className="ml-1 text-muted-foreground">from yesterday</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Users</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.activeUsers}</div>
          <p className="text-xs text-muted-foreground">Users currently online</p>
          <div className="mt-4 h-1 w-full rounded-full bg-muted">
            <div className="h-1 w-3/4 rounded-full bg-primary"></div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">System Status</CardTitle>
          <div className="flex h-2 w-2 rounded-full bg-green-500">
            <div className="animate-ping h-2 w-2 rounded-full bg-green-500 opacity-75"></div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">Healthy</div>
          <p className="text-xs text-muted-foreground">All systems operational</p>
          <div className="mt-2 grid grid-cols-3 gap-1">
            <div className="rounded-md bg-green-100 dark:bg-green-900/20 p-1">
              <p className="text-center text-xs font-medium text-green-700 dark:text-green-400">API</p>
            </div>
            <div className="rounded-md bg-green-100 dark:bg-green-900/20 p-1">
              <p className="text-center text-xs font-medium text-green-700 dark:text-green-400">DB</p>
            </div>
            <div className="rounded-md bg-green-100 dark:bg-green-900/20 p-1">
              <p className="text-center text-xs font-medium text-green-700 dark:text-green-400">Web</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

