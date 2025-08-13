// Flight test data for ServiceSelection and SeatSelection testing
export const mockFlightPriceResponse = {
  "Document": {
    "id": "document"
  },
  "Warnings": {
    "Warning": [
      {
        "ShortText": "null - Base amount guaranteed until 2025-08-12 23:59:59"
      },
      {
        "ShortText": "null - Tax summary guaranteed until 2025-08-12 23:59:59"
      },
      {
        "ShortText": "null - Price guarantee will be recalculated at time of order/booking creation."
      }
    ]
  },
  "ShoppingResponseID": {
    "ResponseID": {
      "value": "8OzQUysefUo0Bjxq--tjFIlxRUmEtzbpVOjbknXt6nQ-LHG"
    }
  },
  "PricedFlightOffers": {
    "PricedFlightOffer": [
      {
        "OfferID": {
          "ObjectKey": "PF71DBAE9-48C6-40F3-AD576p486d5w3ube7-1",
          "value": "PF71DBAE9-48C6-40F3-AD576p486d5w3ube7-1",
          "Owner": "SN",
          "Channel": "NDC"
        },
        "OfferPrice": [
          {
            "RequestedDate": {
              "Associations": [
                {
                  "AssociatedTraveler": {
                    "TravelerReferences": [
                      "LHG-T1"
                    ]
                  },
                  "ApplicableFlight": {
                    "FlightSegmentReference": [
                      {
                        "ClassOfService": {
                          "Code": {
                            "value": "W"
                          },
                          "MarketingName": {
                            "value": "ECONOMY"
                          }
                        },
                        "FlightSegment": {
                          "value": "FS1"
                        }
                      }
                    ]
                  }
                }
              ]
            },
            "TotalAmount": {
              "SimpleCurrencyPrice": {
                "value": 842.60,
                "Code": "USD"
              }
            }
          }
        ]
      }
    ]
  }
}

// Mock passengers for testing
export const mockPassengers = [
  {
    objectKey: "PAX1",
    name: "John Doe", 
    type: "adult"
  }
]