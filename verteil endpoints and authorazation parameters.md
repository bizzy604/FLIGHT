# Authorization parameters
 endpoint https://api.stage.verteil.com/oauth2/token?grant_type=client_credentials&scope=api

 Authorization: Basic Auth
 username: reatravel_apitestuser
 password: UZrNcyxpIFn2TOdiU5uc9kZrqJwxU44KdlyFBpiDOaaNom1xSySEtQmRq9IcDq3c

 # response will be something like this
 {
    "access_token": "eyJraWQiOiJiZjA1ODMxYS0zNzFmLTRlY2UtYWExYS04YTUyNGRlZmMwMWMiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJyZWF0cmF2ZWxfYXBpdGVzdHVzZXIiLCJhdWQiOiJyZWF0cmF2ZWxfYXBpdGVzdHVzZXIiLCJuYmYiOjE3NDgyNDA5NzQsImdyYW50LXR5cGUiOiJjbGllbnRfY3JlZGVudGlhbHMiLCJkZWZhdWx0LW9mZmljZSI6Ik9GRjM3NDYiLCJzY29wZSI6WyJhcGkiXSwiaXNzIjoiaHR0cDovL2F1dGgtc2VydmljZSIsImFjY2Vzc1JpZ2h0cyI6WyJvZmZlci5yZXByaWNlb3JkZXIiLCJvZmZlci5yZWZ1bmRxdW90ZSIsIm9mZmVyLnJlc2hvcG9yZGVyIiwib2ZmZXIuc2hvcCIsIm9mZmVyLnByaWNlIiwib2ZmZXIubGlzdHNlcnZpY2VzIiwib2ZmZXIubG9hZGV4Y2hhbmdlcmF0ZSIsIm9mZmVyLmxpc3RzZWF0cyIsIm9mZmVyLmFpcmF2YWlsYWJpbGl0eSIsIm9mZmVyLmZhcmVydWxlcyIsIm9mZmVyLnNlcnZpY2VpbmZvIl0sIm9mZmljZSI6WyJPRkYzNzQ2Il0sImV4cCI6MTc0ODI4NDE3NCwiaWF0IjoxNzQ4MjQwOTc0LCJVc2VyVHlwZSI6IkFQSS1Vc2VyIn0.ANMtvQiREdXthMnRxyVgaEZuChj8S6xCj6h4-kVc-a5Jy6oAQUnIZkiUiuhiDub9yVAx47xu0J4oE1spHmpl6y4gjbJrjDAzOIE426wFe3hjwk6vKAwi1rqk4G00CiVdaOHuF3Ek-JZ9PSdAjsHEbAamC8P8z7rXltds8KdnGHBS6D2CBBrjc0J77drxhUJTmlbOF1D3QqdqNxwInleaSfyerW3GiMD9oxUzUGScZSCVWPOktpcjSGqZtSHDQz5sw_r50-cTKKwVXKsbQL1ArvVKOohPPTkJgvoaOVYGksPPgMhwE3WoSQWQt0HehFT8CF5RkQzoqRJJEgVyOGYr9Q",
    "scope": "api",
    "token_type": "Bearer",
    "expires_in": 43199
}
 This token is the ones we will use in this project endpoints to authorize requests as Bearer tokens

# Airshopping endpoint
 endpoint https://api.stage.verteil.com/entrygate/rest/request:airShopping
 Authorazation : Bearer token

 Headers :
 Content-Type: application/json
 Accept: */*
 Accept-Encoding: gzip, deflate, br
 Connection: keep-alive
 service: AirShopping
 ThirdPartyId: {specified Airline ID}
 OfficeId: OFF3748

# FlightPrice endpoint
 endpoint https://api.stage.verteil.com/entrygate/rest/request:flightPrice
 Authorazation : Bearer token

 Headers :
 Content-Type: application/json
 Accept: */*
 Accept-Encoding: gzip, deflate, br
 Connection: keep-alive
 service: FlightPrice
 ThirdPartyId: {specified Airline ID}
 OfficeId: OFF3748

# OrderCreate endpoint
 endpoint https://api.stage.verteil.com/entrygate/rest/request:orderCreate
 Authorazation : Bearer token

 Headers :
 Content-Type: application/json
 Accept: */*
 Accept-Encoding: gzip, deflate, br
 Connection: keep-alive
 service: OrderCreate
 ThirdPartyId: {specified Airline ID}
 OfficeId: OFF3748