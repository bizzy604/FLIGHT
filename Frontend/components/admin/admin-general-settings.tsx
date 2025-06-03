"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"

export function AdminGeneralSettings() {
  const [settings, setSettings] = useState({
    siteName: "SkyWay Flight Booking Portal",
    siteDescription: "Book your flights with ease and find the best deals",
    supportEmail: "support@skyway.com",
    supportPhone: "+1 (800) SKY-WAYS",
    enableMaintenanceMode: false,
    enableBookings: true,
    enablePayments: true,
    maintenanceMessage: "We're currently performing scheduled maintenance. Please check back soon.",
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setSettings((prev) => ({ ...prev, [name]: value }))
  }

  const handleSwitchChange = (name: string, checked: boolean) => {
    setSettings((prev) => ({ ...prev, [name]: checked }))
  }

  const handleSaveSettings = () => {
    // In a real app, this would save settings to the backend
    console.log("Saving settings:", settings)
    // Show success message
    alert("Settings saved successfully")
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSaveSettings()
          }}
        >
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium">Site Information</h3>
              <p className="text-sm text-muted-foreground">Basic information about your booking portal</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="siteName">Site Name</Label>
                <Input id="siteName" name="siteName" value={settings.siteName} onChange={handleChange} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="siteDescription">Site Description</Label>
                <Input
                  id="siteDescription"
                  name="siteDescription"
                  value={settings.siteDescription}
                  onChange={handleChange}
                />
              </div>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium">Contact Information</h3>
              <p className="text-sm text-muted-foreground">Support contact details displayed to users</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="supportEmail">Support Email</Label>
                <Input
                  id="supportEmail"
                  name="supportEmail"
                  type="email"
                  value={settings.supportEmail}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="supportPhone">Support Phone</Label>
                <Input id="supportPhone" name="supportPhone" value={settings.supportPhone} onChange={handleChange} />
              </div>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium">System Settings</h3>
              <p className="text-sm text-muted-foreground">Control system functionality</p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="enableBookings">Enable Bookings</Label>
                  <p className="text-sm text-muted-foreground">Allow users to make new bookings</p>
                </div>
                <Switch
                  id="enableBookings"
                  checked={settings.enableBookings}
                  onCheckedChange={(checked) => handleSwitchChange("enableBookings", checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="enablePayments">Enable Payments</Label>
                  <p className="text-sm text-muted-foreground">Allow payment processing</p>
                </div>
                <Switch
                  id="enablePayments"
                  checked={settings.enablePayments}
                  onCheckedChange={(checked) => handleSwitchChange("enablePayments", checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="enableMaintenanceMode">Maintenance Mode</Label>
                  <p className="text-sm text-muted-foreground">Put the site in maintenance mode</p>
                </div>
                <Switch
                  id="enableMaintenanceMode"
                  checked={settings.enableMaintenanceMode}
                  onCheckedChange={(checked) => handleSwitchChange("enableMaintenanceMode", checked)}
                />
              </div>

              {settings.enableMaintenanceMode && (
                <div className="space-y-2">
                  <Label htmlFor="maintenanceMessage">Maintenance Message</Label>
                  <Textarea
                    id="maintenanceMessage"
                    name="maintenanceMessage"
                    value={settings.maintenanceMessage}
                    onChange={handleChange}
                    rows={3}
                  />
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <Button type="submit">Save Settings</Button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

