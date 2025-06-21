import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Plus, Search, Filter, Download } from "lucide-react"

export default function FlightsPage() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Flights Management</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add New Flight
        </Button>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex w-full max-w-sm items-center space-x-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input type="search" placeholder="Search flights..." className="w-full pl-8" />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
            <span className="sr-only">Filter</span>
          </Button>
          <Button variant="outline" size="icon">
            <Download className="h-4 w-4" />
            <span className="sr-only">Download</span>
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Flights</TabsTrigger>
          <TabsTrigger value="scheduled">Scheduled</TabsTrigger>
          <TabsTrigger value="in-progress">In Progress</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="cancelled">Cancelled</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Flight Schedule</CardTitle>
              <CardDescription>Manage all flights in the system</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Flight #</TableHead>
                    <TableHead>Route</TableHead>
                    <TableHead>Departure</TableHead>
                    <TableHead>Arrival</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Capacity</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[
                    {
                      id: "SW1234",
                      route: "JFK → LAX",
                      departure: "Apr 15, 2025 08:30",
                      arrival: "Apr 15, 2025 11:45",
                      status: "scheduled",
                      capacity: "85% (170/200)",
                    },
                    {
                      id: "SW2345",
                      route: "LAX → ORD",
                      departure: "Apr 15, 2025 13:15",
                      arrival: "Apr 15, 2025 19:20",
                      status: "in-progress",
                      capacity: "92% (184/200)",
                    },
                    {
                      id: "SW3456",
                      route: "ORD → MIA",
                      departure: "Apr 16, 2025 07:45",
                      arrival: "Apr 16, 2025 11:30",
                      status: "scheduled",
                      capacity: "65% (130/200)",
                    },
                    {
                      id: "SW4567",
                      route: "MIA → JFK",
                      departure: "Apr 14, 2025 14:30",
                      arrival: "Apr 14, 2025 17:45",
                      status: "completed",
                      capacity: "98% (196/200)",
                    },
                    {
                      id: "SW5678",
                      route: "SFO → SEA",
                      departure: "Apr 15, 2025 10:15",
                      arrival: "Apr 15, 2025 12:30",
                      status: "cancelled",
                      capacity: "0% (0/200)",
                    },
                  ].map((flight) => (
                    <TableRow key={flight.id}>
                      <TableCell className="font-medium">{flight.id}</TableCell>
                      <TableCell>{flight.route}</TableCell>
                      <TableCell>{flight.departure}</TableCell>
                      <TableCell>{flight.arrival}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            flight.status === "scheduled"
                              ? "outline"
                              : flight.status === "in-progress"
                                ? "default"
                                : flight.status === "completed"
                                  ? "secondary"
                                  : "destructive"
                          }
                        >
                          {flight.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{flight.capacity}</TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button variant="outline" size="sm">
                            Edit
                          </Button>
                          <Button variant="outline" size="sm">
                            View
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="scheduled" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Scheduled Flights</CardTitle>
              <CardDescription>All upcoming flights that are scheduled to depart</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Scheduled flights table will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="in-progress" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>In-Progress Flights</CardTitle>
              <CardDescription>Flights that are currently in the air</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">In-progress flights table will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="completed" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Completed Flights</CardTitle>
              <CardDescription>Flights that have successfully arrived at their destination</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Completed flights table will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="cancelled" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cancelled Flights</CardTitle>
              <CardDescription>Flights that were cancelled due to various reasons</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Cancelled flights table will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

