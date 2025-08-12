import type { Metadata } from "next"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AdminGeneralSettings, AdminApiSettings, AdminUserManagement } from "@/components/organisms"

export const metadata: Metadata = {
  title: "Rea Travel Admin - Settings",
  description: "Admin dashboard for Rea Travel flight booking portal",
}

export default function AdminSettingsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage system settings and configurations</p>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="api">API Configuration</TabsTrigger>
          <TabsTrigger value="users">User Management</TabsTrigger>
        </TabsList>
        <TabsContent value="general">
          <AdminGeneralSettings />
        </TabsContent>
        <TabsContent value="api">
          <AdminApiSettings />
        </TabsContent>
        <TabsContent value="users">
          <AdminUserManagement />
        </TabsContent>
      </Tabs>
    </div>
  )
}

