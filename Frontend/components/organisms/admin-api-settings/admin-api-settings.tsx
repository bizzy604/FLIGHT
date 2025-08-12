"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Settings, Key } from "lucide-react"

export function AdminApiSettings() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            API Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="api-url">API Base URL</Label>
            <Input id="api-url" placeholder="https://api.example.com" />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="api-key">API Key</Label>
            <Input id="api-key" type="password" placeholder="Enter API key" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="rate-limit">Rate Limit (requests per minute)</Label>
            <Input id="rate-limit" type="number" placeholder="1000" />
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Switch id="api-logging" defaultChecked />
              <Label htmlFor="api-logging">Enable API Logging</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="rate-limiting" defaultChecked />
              <Label htmlFor="rate-limiting">Enable Rate Limiting</Label>
            </div>
          </div>

          <Button>Save API Settings</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5" />
            API Keys
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 border rounded">
              <div>
                <p className="font-medium">Main API Key</p>
                <p className="text-sm text-muted-foreground">Created 2 days ago</p>
              </div>
              <Button variant="outline" size="sm">Regenerate</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}