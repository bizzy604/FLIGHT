"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/loading-spinner"

export function SystemStatus() {
  const [isLoading, setIsLoading] = useState(true)
  const [systemStatus, setSystemStatus] = useState({
    overall: "healthy",
    components: [
      { name: "API Gateway", status: "healthy", uptime: "99.98%" },
      { name: "Database", status: "healthy", uptime: "99.99%" },
      { name: "Payment Processor", status: "healthy", uptime: "99.95%" },
      { name: "Search Engine", status: "degraded", uptime: "98.75%" },
      { name: "Notification Service", status: "healthy", uptime: "99.90%" },
    ],
    lastChecked: new Date().toISOString(),
  })

  useEffect(() => {
    // Simulate API call to fetch system status
    const fetchSystemStatus = async () => {
      try {
        // In a real app, this would be an API call
        await new Promise((resolve) => setTimeout(resolve, 1200))
        setSystemStatus({
          ...systemStatus,
          lastChecked: new Date().toISOString(),
        })
      } catch (error) {
        console.error("Failed to fetch system status:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchSystemStatus()

    // Refresh status every 30 seconds
    const intervalId = setInterval(fetchSystemStatus, 30000)

    return () => clearInterval(intervalId)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
      case "degraded":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400"
      case "down":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400"
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
        <CardDescription>Current status of all system components</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-4">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center">
                <div
                  className={`mr-2 h-3 w-3 rounded-full ${
                    systemStatus.overall === "healthy"
                      ? "bg-green-500"
                      : systemStatus.overall === "degraded"
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  }`}
                >
                  <div
                    className={`animate-ping h-3 w-3 rounded-full ${
                      systemStatus.overall === "healthy"
                        ? "bg-green-500"
                        : systemStatus.overall === "degraded"
                          ? "bg-yellow-500"
                          : "bg-red-500"
                    } opacity-75`}
                  ></div>
                </div>
                <span className="font-medium">
                  {systemStatus.overall === "healthy"
                    ? "All Systems Operational"
                    : systemStatus.overall === "degraded"
                      ? "Partial System Degradation"
                      : "System Outage"}
                </span>
              </div>
              <span className="text-xs text-muted-foreground">
                Last updated: {new Date(systemStatus.lastChecked).toLocaleTimeString()}
              </span>
            </div>

            <div className="space-y-2">
              {systemStatus.components.map((component) => (
                <div key={component.name} className="flex items-center justify-between rounded-md border p-2">
                  <span>{component.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{component.uptime}</span>
                    <Badge className={getStatusColor(component.status)} variant="outline">
                      {component.status.charAt(0).toUpperCase() + component.status.slice(1)}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>

            <Button variant="outline" size="sm" className="mt-4 w-full">
              View Detailed Status
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  )
}

