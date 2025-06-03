import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Plus, Search, Filter, Download } from "lucide-react"

export default function CustomersPage() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Customer Management</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Customer
        </Button>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex w-full max-w-sm items-center space-x-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input type="search" placeholder="Search customers..." className="w-full pl-8" />
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

      <Card>
        <CardHeader className="pb-3">
          <CardTitle>Customers</CardTitle>
          <CardDescription>Manage customer accounts and view their booking history</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Bookings</TableHead>
                <TableHead>Total Spent</TableHead>
                <TableHead>Last Activity</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[
                {
                  id: "1",
                  name: "Olivia Martin",
                  email: "olivia.martin@email.com",
                  avatar: "/placeholder.svg?height=32&width=32",
                  initials: "OM",
                  status: "active",
                  bookings: 12,
                  spent: "$3,450.00",
                  lastActivity: "2 hours ago",
                },
                {
                  id: "2",
                  name: "Jackson Lee",
                  email: "jackson.lee@email.com",
                  avatar: "/placeholder.svg?height=32&width=32",
                  initials: "JL",
                  status: "active",
                  bookings: 8,
                  spent: "$2,285.00",
                  lastActivity: "5 hours ago",
                },
                {
                  id: "3",
                  name: "Isabella Nguyen",
                  email: "isabella.nguyen@email.com",
                  avatar: "/placeholder.svg?height=32&width=32",
                  initials: "IN",
                  status: "inactive",
                  bookings: 3,
                  spent: "$1,420.00",
                  lastActivity: "2 days ago",
                },
                {
                  id: "4",
                  name: "William Kim",
                  email: "william.kim@email.com",
                  avatar: "/placeholder.svg?height=32&width=32",
                  initials: "WK",
                  status: "active",
                  bookings: 6,
                  spent: "$1,912.00",
                  lastActivity: "1 day ago",
                },
                {
                  id: "5",
                  name: "Sofia Rodriguez",
                  email: "sofia.rodriguez@email.com",
                  avatar: "/placeholder.svg?height=32&width=32",
                  initials: "SR",
                  status: "blocked",
                  bookings: 2,
                  spent: "$575.00",
                  lastActivity: "1 month ago",
                },
              ].map((customer) => (
                <TableRow key={customer.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar>
                        <AvatarImage src={customer.avatar} alt={customer.name} />
                        <AvatarFallback>{customer.initials}</AvatarFallback>
                      </Avatar>
                      <div className="font-medium">{customer.name}</div>
                    </div>
                  </TableCell>
                  <TableCell>{customer.email}</TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        customer.status === "active"
                          ? "default"
                          : customer.status === "inactive"
                            ? "outline"
                            : "destructive"
                      }
                    >
                      {customer.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{customer.bookings}</TableCell>
                  <TableCell>{customer.spent}</TableCell>
                  <TableCell>{customer.lastActivity}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm">
                        View
                      </Button>
                      <Button variant="outline" size="sm">
                        Edit
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

