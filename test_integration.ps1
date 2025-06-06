$response = Invoke-WebRequest -Uri 'http://localhost:5000/api/verteil/air-shopping' -Method POST -Headers @{'Content-Type'='application/json'} -Body '{"tripType":"ONE_WAY","odSegments":[{"origin":"JFK","destination":"LAX","departureDate":"2024-12-25"}],"numAdults":1,"numChildren":0,"numInfants":0,"cabinPreference":"ECONOMY","directOnly":false}'
Write-Output "Status Code: $($response.StatusCode)"
Write-Output "Response Content:"
Write-Output $response.Content