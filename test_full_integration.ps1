Write-Host "Testing Frontend-Backend Integration" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Test 1: Backend Health Check
Write-Host "1. Testing Backend Health Check..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-WebRequest -Uri 'http://localhost:5000/api/health' -Method GET
    Write-Host "   ✓ Backend Health: Status $($healthResponse.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($healthResponse.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "   ✗ Backend Health Check Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Backend Flight Search API
Write-Host "`n2. Testing Backend Flight Search API..." -ForegroundColor Yellow
try {
    $searchResponse = Invoke-WebRequest -Uri 'http://localhost:5000/api/verteil/air-shopping' -Method POST -Headers @{'Content-Type'='application/json'} -Body '{"tripType":"ONE_WAY","odSegments":[{"origin":"JFK","destination":"LAX","departureDate":"2024-12-25"}],"numAdults":1,"numChildren":0,"numInfants":0,"cabinPreference":"ECONOMY","directOnly":false}'
    Write-Host "   ✓ Flight Search API: Status $($searchResponse.StatusCode)" -ForegroundColor Green
    $responseData = $searchResponse.Content | ConvertFrom-Json
    Write-Host "   Status: $($responseData.status)" -ForegroundColor Cyan
    Write-Host "   Request ID: $($responseData.request_id)" -ForegroundColor Cyan
    Write-Host "   Offers Count: $($responseData.data.data.offers.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "   ✗ Flight Search API Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Frontend Health Check
Write-Host "`n3. Testing Frontend Accessibility..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri 'http://localhost:3000' -Method GET -TimeoutSec 10
    Write-Host "   ✓ Frontend: Status $($frontendResponse.StatusCode)" -ForegroundColor Green
    if ($frontendResponse.Content -like "*Flight*" -or $frontendResponse.Content -like "*flight*") {
        Write-Host "   ✓ Frontend contains flight-related content" -ForegroundColor Green
    }
} catch {
    Write-Host "   ✗ Frontend Accessibility Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Frontend API Route
Write-Host "`n4. Testing Frontend API Route..." -ForegroundColor Yellow
try {
    $frontendApiResponse = Invoke-WebRequest -Uri 'http://localhost:3000/api/flights/search-advanced' -Method POST -Headers @{'Content-Type'='application/json'} -Body '{"CoreQuery":{"OriginDestinations":{"OriginDestination":[{"Departure":{"AirportCode":{"value":"JFK"},"Date":"2024-12-25"},"Arrival":{"AirportCode":{"value":"LAX"}},"OriginDestinationKey":"OD1"}]}},"Travelers":{"Traveler":[{"AnonymousTraveler":[{"PTC":{"value":"ADT"}}]}]},"Preference":{"CabinPreferences":{"CabinType":[{"Code":"Y"}]}}}'
    Write-Host "   ✓ Frontend API Route: Status $($frontendApiResponse.StatusCode)" -ForegroundColor Green
    $frontendApiData = $frontendApiResponse.Content | ConvertFrom-Json
    Write-Host "   Status: $($frontendApiData.status)" -ForegroundColor Cyan
} catch {
    Write-Host "   ✗ Frontend API Route Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "Integration Test Complete!" -ForegroundColor Green
Write-Host "Frontend URL: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend URL: http://localhost:5000" -ForegroundColor Cyan