import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar, Download } from "lucide-react"

export default function AnalyticsPage() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <div className="flex gap-2">
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            Date Range
          </Button>
          <Button>
            <Download className="mr-2 h-4 w-4" />
            Export Data
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Select defaultValue="last30">
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Time Period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="last7">Last 7 Days</SelectItem>
              <SelectItem value="last30">Last 30 Days</SelectItem>
              <SelectItem value="last90">Last 90 Days</SelectItem>
              <SelectItem value="year">This Year</SelectItem>
              <SelectItem value="custom">Custom Range</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24.8%</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+2.5%</span> from last period
            </p>
            <div className="mt-4 h-[80px] flex items-center justify-center border-t pt-4">
              <p className="text-xs text-muted-foreground">Conversion rate mini chart</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Average Order Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$357.42</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+4.3%</span> from last period
            </p>
            <div className="mt-4 h-[80px] flex items-center justify-center border-t pt-4">
              <p className="text-xs text-muted-foreground">AOV mini chart</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Bounce Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">32.1%</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-red-500">+1.8%</span> from last period
            </p>
            <div className="mt-4 h-[80px] flex items-center justify-center border-t pt-4">
              <p className="text-xs text-muted-foreground">Bounce rate mini chart</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">User Engagement</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.2 min</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+0.5 min</span> from last period
            </p>
            <div className="mt-4 h-[80px] flex items-center justify-center border-t pt-4">
              <p className="text-xs text-muted-foreground">Engagement mini chart</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="traffic" className="space-y-4">
        <TabsList>
          <TabsTrigger value="traffic">Traffic & Conversion</TabsTrigger>
          <TabsTrigger value="user">User Behavior</TabsTrigger>
          <TabsTrigger value="booking">Booking Funnel</TabsTrigger>
          <TabsTrigger value="marketing">Marketing Performance</TabsTrigger>
        </TabsList>
        <TabsContent value="traffic" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Traffic Sources</CardTitle>
                <CardDescription>Where your visitors are coming from</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[350px] flex items-center justify-center border rounded-md">
                  <p className="text-muted-foreground">Traffic sources chart will appear here</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Conversion by Channel</CardTitle>
                <CardDescription>Booking conversion rates by traffic source</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[350px] flex items-center justify-center border rounded-md">
                  <p className="text-muted-foreground">Conversion chart will appear here</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="user" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>User Behavior Analysis</CardTitle>
              <CardDescription>How users interact with your website</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[350px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">User behavior visualization will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="booking" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Booking Funnel Analysis</CardTitle>
              <CardDescription>Conversion at each step of the booking process</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[350px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Booking funnel visualization will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="marketing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Marketing Campaign Performance</CardTitle>
              <CardDescription>ROI and effectiveness of marketing campaigns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[350px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Marketing performance visualization will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Performing Pages</CardTitle>
            <CardDescription>Pages with highest conversion rates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                {
                  page: "/flights/new-york-to-los-angeles",
                  views: "12,543",
                  conversion: "8.2%",
                  value: "$45,320",
                },
                {
                  page: "/flights/san-francisco-to-chicago",
                  views: "8,721",
                  conversion: "7.5%",
                  value: "$32,150",
                },
                {
                  page: "/special-offers/summer-sale",
                  views: "6,432",
                  conversion: "12.3%",
                  value: "$28,750",
                },
                {
                  page: "/flights/miami-to-new-york",
                  views: "5,876",
                  conversion: "6.8%",
                  value: "$19,430",
                },
              ].map((page, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{page.page}</p>
                    <p className="text-sm text-muted-foreground">{page.views} views</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{page.conversion}</p>
                    <p className="text-sm text-muted-foreground">{page.value}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>User Demographics</CardTitle>
            <CardDescription>Breakdown of your customer base</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex items-center justify-center border rounded-md">
              <p className="text-muted-foreground">Demographics visualization will appear here</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}