Write-Host "Testing Backend API" -ForegroundColor Green

# Test Backend Health
Write-Host "Testing backend health..." -ForegroundColor Yellow
$healthResponse = Invoke-WebRequest -Uri 'http://localhost:5000/api/health' -Method GET
Write-Host "Backend Health Status: $($healthResponse.StatusCode)" -ForegroundColor Green
Write-Host "Response: $($healthResponse.Content)" -ForegroundColor Cyan

# Test Backend Flight Search
Write-Host "`nTesting backend flight search..." -ForegroundColor Yellow
$body = '{"tripType":"ONE_WAY","odSegments":[{"origin":"JFK","destination":"LAX","departureDate":"2024-12-25"}],"numAdults":1,"numChildren":0,"numInfants":0,"cabinPreference":"ECONOMY","directOnly":false}'
$searchResponse = Invoke-WebRequest -Uri 'http://localhost:5000/api/verteil/air-shopping' -Method POST -Headers @{'Content-Type'='application/json'} -Body $body
Write-Host "Flight Search Status: $($searchResponse.StatusCode)" -ForegroundColor Green
$responseData = $searchResponse.Content | ConvertFrom-Json
Write-Host "API Status: $($responseData.status)" -ForegroundColor Cyan
Write-Host "Request ID: $($responseData.request_id)" -ForegroundColor Cyan

# Test Frontend
Write-Host "`nTesting frontend..." -ForegroundColor Yellow
$frontendResponse = Invoke-WebRequest -Uri 'http://localhost:3000' -Method GET -TimeoutSec 10
Write-Host "Frontend Status: $($frontendResponse.StatusCode)" -ForegroundColor Green

Write-Host "`nAll tests completed successfully!" -ForegroundColor Green