"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Eye, EyeOff, RefreshCw } from "lucide-react"

export function AdminApiSettings() {
  const [showSecrets, setShowSecrets] = useState(false)
  const [settings, setSettings] = useState({
    flightApiEndpoint: "https://api.flights.example.com/v1",
    flightApiKey: "",
    paymentGateway: "paypal",
    paymentApiKey: "",
    paymentWebhookSecret: "",
    enableSandboxMode: true,
    enableCaching: true,
    cacheExpiration: "3600",
    rateLimitRequests: "100",
    rateLimitInterval: "60",
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setSettings((prev) => ({ ...prev, [name]: value }))
  }

  const handleSelectChange = (name: string, value: string) => {
    setSettings((prev) => ({ ...prev, [name]: value }))
  }

  const handleSwitchChange = (name: string, checked: boolean) => {
    setSettings((prev) => ({ ...prev, [name]: checked }))
  }

  const generateNewApiKey = () => {
    // In a real app, this would call an API to generate a new key
    const newKey = "sk_" + Math.random().toString(36).substring(2, 15)
    setSettings((prev) => ({ ...prev, flightApiKey: newKey }))
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={(e) => e.preventDefault()}>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium">Flight API Configuration</h3>
              <p className="text-sm text-muted-foreground">Configure the flight aggregator API integration</p>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="flightApiEndpoint">API Endpoint</Label>
                <Input
                  id="flightApiEndpoint"
                  name="flightApiEndpoint"
                  value={settings.flightApiEndpoint}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="flightApiKey">API Key</Label>
                <div className="flex space-x-2">
                  <div className="relative flex-1">
                    <Input
                      id="flightApiKey"
                      name="flightApiKey"
                      type={showSecrets ? "text" : "password"}
                      value={settings.flightApiKey}
                      onChange={handleChange}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full px-3"
                      onClick={() => setShowSecrets(!showSecrets)}
                    >
                      {showSecrets ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      <span className="sr-only">{showSecrets ? "Hide" : "Show"} API key</span>
                    </Button>
                  </div>
                  <Button type="button" variant="outline" onClick={generateNewApiKey}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Generate
                  </Button>
                </div>
              </div>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium">Payment Gateway</h3>
              <p className="text-sm text-muted-foreground">Configure payment processing integration</p>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="paymentGateway">Payment Provider</Label>
                <Select
                  value={settings.paymentGateway}
                  onValueChange={(value) => handleSelectChange("paymentGateway", value)}
                >
                  <SelectTrigger id="paymentGateway">
                    <SelectValue placeholder="Select payment gateway" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="paypal">PayPal</SelectItem>
                    <SelectItem value="adyen">Adyen</SelectItem>
                    <SelectItem value="braintree">Braintree</SelectItem>
                    <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="paymentApiKey">API Key</Label>
                <Input
                  id="paymentApiKey"
                  name="paymentApiKey"
                  type={showSecrets ? "text" : "password"}
                  value={settings.paymentApiKey}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="paymentWebhookSecret">Webhook Secret</Label>
                <Input
                  id="paymentWebhookSecret"
                  name="paymentWebhookSecret"
                  type={showSecrets ? "text" : "password"}
                  value={settings.paymentWebhookSecret}
                  onChange={handleChange}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="enableSandboxMode"
                  checked={settings.enableSandboxMode}
                  onCheckedChange={(checked) => handleSwitchChange("enableSandboxMode", checked)}
                />
                <Label htmlFor="enableSandboxMode">Enable Sandbox Mode</Label>
              </div>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium">API Performance</h3>
              <p className="text-sm text-muted-foreground">Configure API caching and rate limiting</p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="enableCaching"
                  checked={settings.enableCaching}
                  onCheckedChange={(checked) => handleSwitchChange("enableCaching", checked)}
                />
                <Label htmlFor="enableCaching">Enable API Response Caching</Label>
              </div>

              {settings.enableCaching && (
                <div className="space-y-2">
                  <Label htmlFor="cacheExpiration">Cache Expiration (seconds)</Label>
                  <Input
                    id="cacheExpiration"
                    name="cacheExpiration"
                    type="number"
                    value={settings.cacheExpiration}
                    onChange={handleChange}
                  />
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="rateLimitRequests">Rate Limit (requests)</Label>
                  <Input
                    id="rateLimitRequests"
                    name="rateLimitRequests"
                    type="number"
                    value={settings.rateLimitRequests}
                    onChange={handleChange}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="rateLimitInterval">Rate Limit Interval (seconds)</Label>
                  <Input
                    id="rateLimitInterval"
                    name="rateLimitInterval"
                    type="number"
                    value={settings.rateLimitInterval}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline">Reset to Defaults</Button>
              <Button type="submit">Save Settings</Button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

