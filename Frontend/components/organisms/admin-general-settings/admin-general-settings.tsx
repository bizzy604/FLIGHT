"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Settings } from "lucide-react"

export function AdminGeneralSettings() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            General Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="site-name">Site Name</Label>
              <Input id="site-name" placeholder="Rea Travel" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="site-url">Site URL</Label>
              <Input id="site-url" placeholder="https://reatravels.com" />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="description">Site Description</Label>
            <Textarea id="description" placeholder="Book your flights with ease and find the best deals" />
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Switch id="maintenance" />
              <Label htmlFor="maintenance">Maintenance Mode</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="registrations" defaultChecked />
              <Label htmlFor="registrations">Allow New Registrations</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="notifications" defaultChecked />
              <Label htmlFor="notifications">Email Notifications</Label>
            </div>
          </div>

          <Button>Save Settings</Button>
        </CardContent>
      </Card>
    </div>
  )
}