"use client"

import * as React from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface PassengerFormProps {
  passengerNumber: number
  passengerLabel?: string
  passengerType?: string
  passengerData: any;      // Data for this passenger
  onPassengerChange: (updatedData: any) => void; // Callback to update parent state
}

export function PassengerForm({ passengerNumber, passengerLabel, passengerType, passengerData, onPassengerChange }: PassengerFormProps) {
  const handleInputChange = (field: string, value: any) => {
    onPassengerChange({ ...passengerData, [field]: value });
  };

  // Set the passenger type from props if provided
  React.useEffect(() => {
    if (passengerType && passengerData?.type !== passengerType) {
      handleInputChange('type', passengerType);
    }
  }, [passengerType]);

  return (
    <div className="space-y-4 rounded-md border p-4" data-testid={`passenger-form-${passengerNumber - 1}`}>
      {passengerLabel && (
        <div className="mb-4">
          <h4 className="text-lg font-medium text-primary">{passengerLabel}</h4>
        </div>
      )}
      <div>
        <div className="mb-4 p-3 bg-muted/50 rounded-md">
          <Label className="text-sm font-medium">
            Passenger Type: {passengerType === 'adult' ? 'Adult (12+ years)' : 
                           passengerType === 'child' ? 'Child (2-11 years)' : 
                           'Infant (0-2 years)'}
          </Label>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor={`title-${passengerNumber}`}>Title</Label>
        <Select 
          value={passengerData?.title || ''} 
          onValueChange={(value) => handleInputChange('title', value)} >
          <SelectTrigger>
            <SelectValue placeholder="Select title" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="mr">Mr.</SelectItem>
            <SelectItem value="mrs">Mrs.</SelectItem>
            <SelectItem value="ms">Ms.</SelectItem>
            <SelectItem value="miss">Miss</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={`first-name-${passengerNumber}`}>Given Name (First Name)</Label>
          <Input 
            id={`first-name-${passengerNumber}`} 
            data-testid={`passenger-${passengerNumber - 1}-firstName`} 
            placeholder="Enter given name" 
            value={passengerData?.firstName || ''} 
            onChange={(e) => handleInputChange('firstName', e.target.value)} 
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`last-name-${passengerNumber}`}>Surname (Last Name)</Label>
          <Input 
            id={`last-name-${passengerNumber}`} 
            data-testid={`passenger-${passengerNumber - 1}-lastName`} 
            placeholder="Enter surname" 
            value={passengerData?.lastName || ''} 
            onChange={(e) => handleInputChange('lastName', e.target.value)} 
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={`dob-${passengerNumber}`}>Date of Birth</Label>
          <div className="grid grid-cols-3 gap-2">
            <Select 
              value={passengerData?.dob?.day || ''} 
              onValueChange={(value) => handleInputChange('dob', { ...passengerData?.dob, day: value })} >
              <SelectTrigger>
                <SelectValue placeholder="Day" />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
                  <SelectItem key={day} value={day.toString()}>
                    {day}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select 
              value={passengerData?.dob?.month || ''} 
              onValueChange={(value) => handleInputChange('dob', { ...passengerData?.dob, month: value })} >
              <SelectTrigger>
                <SelectValue placeholder="Month" />
              </SelectTrigger>
              <SelectContent>
                {[
                  "January",
                  "February",
                  "March",
                  "April",
                  "May",
                  "June",
                  "July",
                  "August",
                  "September",
                  "October",
                  "November",
                  "December",
                ].map((month, index) => (
                  <SelectItem key={month} value={(index + 1).toString()}>
                    {month}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select 
              value={passengerData?.dob?.year || ''} 
              onValueChange={(value) => handleInputChange('dob', { ...passengerData?.dob, year: value })} >
              <SelectTrigger>
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 100 }, (_, i) => new Date().getFullYear() - i).map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor={`gender-${passengerNumber}`}>Gender</Label>
          <Select 
            value={passengerData?.gender || ''} 
            onValueChange={(value) => handleInputChange('gender', value)} >
            <SelectTrigger>
              <SelectValue placeholder="Select gender" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="male">Male</SelectItem>
              <SelectItem value="female">Female</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label>Travel Document</Label>
        <RadioGroup 
          value={passengerData?.documentType || "passport"} 
          onValueChange={(value) => handleInputChange('documentType', value)} 
          className="flex flex-wrap gap-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="passport" id={`passport-${passengerNumber}`} />
            <Label htmlFor={`passport-${passengerNumber}`}>Passport</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="id-card" id={`id-card-${passengerNumber}`} />
            <Label htmlFor={`id-card-${passengerNumber}`}>ID Card</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={`document-number-${passengerNumber}`}>Document Number</Label>
          <Input 
            id={`document-number-${passengerNumber}`} 
            placeholder="Enter document number" 
            value={passengerData?.documentNumber || ''} 
            onChange={(e) => handleInputChange('documentNumber', e.target.value)} 
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`nationality-${passengerNumber}`}>Nationality</Label>
          <Select 
            value={passengerData?.nationality || ''} 
            onValueChange={(value) => handleInputChange('nationality', value)} >
            <SelectTrigger>
              <SelectValue placeholder="Select country" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="US">United States</SelectItem>
              <SelectItem value="CA">Canada</SelectItem>
              <SelectItem value="UK">United Kingdom</SelectItem>
              <SelectItem value="AU">Australia</SelectItem>
              <SelectItem value="FR">France</SelectItem>
              <SelectItem value="DE">Germany</SelectItem>
              <SelectItem value="JP">Japan</SelectItem>
              <SelectItem value="CN">China</SelectItem>
              <SelectItem value="IN">India</SelectItem>
              <SelectItem value="RU">Russia</SelectItem>
              <SelectItem value="BR">Brazil</SelectItem>
              <SelectItem value="KE">Kenya</SelectItem>
              <SelectItem value="ZA">South Africa</SelectItem>
              {/* Add more countries as needed */}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={`expiry-date-${passengerNumber}`}>Document Expiry Date</Label>
          <div className="grid grid-cols-3 gap-2">
            <Select 
              value={passengerData?.expiryDate?.day || ''} 
              onValueChange={(value) => handleInputChange('expiryDate', { ...passengerData?.expiryDate, day: value })} >
              <SelectTrigger>
                <SelectValue placeholder="Day" />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
                  <SelectItem key={day} value={day.toString()}>
                    {day}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select 
              value={passengerData?.expiryDate?.month || ''} 
              onValueChange={(value) => handleInputChange('expiryDate', { ...passengerData?.expiryDate, month: value })} >
              <SelectTrigger>
                <SelectValue placeholder="Month" />
              </SelectTrigger>
              <SelectContent>
                {[
                  "January",
                  "February",
                  "March",
                  "April",
                  "May",
                  "June",
                  "July",
                  "August",
                  "September",
                  "October",
                  "November",
                  "December",
                ].map((month, index) => (
                  <SelectItem key={month} value={(index + 1).toString()}>
                    {month}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select 
              value={passengerData?.expiryDate?.year || ''} 
              onValueChange={(value) => handleInputChange('expiryDate', { ...passengerData?.expiryDate, year: value })} >
              <SelectTrigger>
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 20 }, (_, i) => new Date().getFullYear() + i).map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor={`issuing-country-${passengerNumber}`}>Issuing Country</Label>
          <Select 
            value={passengerData?.issuingCountry || ''} 
            onValueChange={(value) => handleInputChange('issuingCountry', value)} >
            <SelectTrigger>
              <SelectValue placeholder="Select country" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="us">United States</SelectItem>
              <SelectItem value="ca">Canada</SelectItem>
              <SelectItem value="uk">United Kingdom</SelectItem>
              <SelectItem value="au">Australia</SelectItem>
              <SelectItem value="fr">France</SelectItem>
              <SelectItem value="de">Germany</SelectItem>
              <SelectItem value="jp">Japan</SelectItem>
              <SelectItem value="cn">China</SelectItem>
              <SelectItem value="in">India</SelectItem>
              <SelectItem value="br">Brazil</SelectItem>
              {/* Add more countries as needed */}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  )
}
