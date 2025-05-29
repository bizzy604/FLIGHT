"use client"

import { FileText, Download, RefreshCw, AlertTriangle } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

export function AdminTools() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Admin Tools</CardTitle>
        <CardDescription>Quick access to reports and system tools</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2">
                  <FileText className="h-6 w-6" />
                  <span>Revenue Report</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Generate revenue reports</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2">
                  <Download className="h-6 w-6" />
                  <span>Export Data</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Export booking and customer data</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2">
                  <RefreshCw className="h-6 w-6" />
                  <span>Cache Refresh</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Refresh system cache</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2">
                  <AlertTriangle className="h-6 w-6" />
                  <span>System Logs</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>View system logs and errors</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <Button variant="default" className="mt-4 w-full">
          View All Tools
        </Button>
      </CardContent>
    </Card>
  )
}

