import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Search, Filter, MessageSquare, Plus } from "lucide-react"

export default function SupportPage() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Customer Support</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Create Ticket
        </Button>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex w-full max-w-sm items-center space-x-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input type="search" placeholder="Search tickets..." className="w-full pl-8" />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
            <span className="sr-only">Filter</span>
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Tickets</TabsTrigger>
          <TabsTrigger value="open">Open</TabsTrigger>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="resolved">Resolved</TabsTrigger>
          <TabsTrigger value="closed">Closed</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Support Tickets</CardTitle>
              <CardDescription>Manage and respond to customer support requests</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ticket ID</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Subject</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Last Updated</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[
                    {
                      id: "T-1001",
                      customer: {
                        name: "Olivia Martin",
                        email: "olivia.martin@email.com",
                        avatar: "/placeholder.svg?height=32&width=32",
                        initials: "OM",
                      },
                      subject: "Refund for cancelled flight",
                      category: "Refunds",
                      status: "open",
                      created: "Apr 15, 2025 08:30",
                      updated: "Apr 15, 2025 09:45",
                    },
                    {
                      id: "T-1002",
                      customer: {
                        name: "Jackson Lee",
                        email: "jackson.lee@email.com",
                        avatar: "/placeholder.svg?height=32&width=32",
                        initials: "JL",
                      },
                      subject: "Seat assignment issue",
                      category: "Booking",
                      status: "pending",
                      created: "Apr 14, 2025 14:15",
                      updated: "Apr 15, 2025 10:30",
                    },
                    {
                      id: "T-1003",
                      customer: {
                        name: "Isabella Nguyen",
                        email: "isabella.nguyen@email.com",
                        avatar: "/placeholder.svg?height=32&width=32",
                        initials: "IN",
                      },
                      subject: "Missing loyalty points",
                      category: "Loyalty Program",
                      status: "open",
                      created: "Apr 14, 2025 11:20",
                      updated: "Apr 14, 2025 16:45",
                    },
                    {
                      id: "T-1004",
                      customer: {
                        name: "William Kim",
                        email: "william.kim@email.com",
                        avatar: "/placeholder.svg?height=32&width=32",
                        initials: "WK",
                      },
                      subject: "Flight delay compensation",
                      category: "Compensation",
                      status: "resolved",
                      created: "Apr 13, 2025 09:10",
                      updated: "Apr 14, 2025 14:30",
                    },
                    {
                      id: "T-1005",
                      customer: {
                        name: "Sofia Rodriguez",
                        email: "sofia.rodriguez@email.com",
                        avatar: "/placeholder.svg?height=32&width=32",
                        initials: "SR",
                      },
                      subject: "Website technical issue",
                      category: "Technical",
                      status: "closed",
                      created: "Apr 12, 2025 16:45",
                      updated: "Apr 13, 2025 11:20",
                    },
                  ].map((ticket) => (
                    <TableRow key={ticket.id}>
                      <TableCell className="font-medium">{ticket.id}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8">
                            <AvatarImage src={ticket.customer.avatar} alt={ticket.customer.name} />
                            <AvatarFallback>{ticket.customer.initials}</AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-sm font-medium">{ticket.customer.name}</p>
                            <p className="text-xs text-muted-foreground">{ticket.customer.email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{ticket.subject}</TableCell>
                      <TableCell>{ticket.category}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            ticket.status === "open"
                              ? "default"
                              : ticket.status === "pending"
                                ? "outline"
                                : ticket.status === "resolved"
                                  ? "secondary"
                                  : "destructive"
                          }
                        >
                          {ticket.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{ticket.created}</TableCell>
                      <TableCell>{ticket.updated}</TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button variant="outline" size="sm">
                            <MessageSquare className="mr-2 h-4 w-4" />
                            Reply
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
        <TabsContent value="open" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Open Tickets</CardTitle>
              <CardDescription>Tickets that require immediate attention</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Open tickets table will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="pending" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Pending Tickets</CardTitle>
              <CardDescription>Tickets awaiting customer response</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Pending tickets table will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="resolved" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Resolved Tickets</CardTitle>
              <CardDescription>Tickets that have been successfully resolved</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Resolved tickets table will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="closed" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Closed Tickets</CardTitle>
              <CardDescription>Tickets that have been permanently closed</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border rounded-md">
                <p className="text-muted-foreground">Closed tickets table will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Open Tickets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-red-500">+5</span> from yesterday
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Average Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2.5 hours</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">-0.5 hours</span> from last week
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Resolution Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">92%</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+2%</span> from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Customer Satisfaction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.7/5</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+0.2</span> from last month
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// This code is a React component for a customer support page in an admin dashboard. It includes a header with a title and button to create a ticket, a search bar, and tabs for different ticket statuses (all, open, pending, resolved, closed). Each tab contains a table of tickets with details like ID, customer info, subject, category, status, created date, last updated date, and actions. There are also cards displaying metrics like open tickets, average response time, resolution rate, and customer satisfaction.