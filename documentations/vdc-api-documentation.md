# Shopping and Booking with Seat and Ancillary (No Pricing Required)

## Definition of Use Case

The user can shop for services—e.g., bags, meals, wheelchair assistance, etc.—using the VDC ServiceList API. Seat selection can be done through the VDC SeatAvailability API. Once the required services and seats are selected, if the `PricedInd` is true, it confirms that the selected ancillaries and seats have already been priced. In this case, there is no need to make an additional call to the FlightPrice API. The user can then proceed directly to complete the booking using the VDC OrderCreate API. To know more about PricedInd, please refer to the Concept section.

## Process Flow

### 1. AirShopping

The user searches for the flight. The ShoppingRQ for one way search for one PAX will look like below:

```json
{
  "Travelers": {
    "Traveler": [
      {
        "AnonymousTraveler": [
          {
            "PTC": {
              "value": "ADT" //Adult
            }
          }
        ]
      }
    ]
  },
  "CoreQuery": {
    "OriginDestinations": {
      "OriginDestination": [
        {
          "Departure": {
            "AirportCode": {
              "value": "BOM"
            },
            "Date": "2025-03-29"
          },
          "Arrival": {
            "AirportCode": {
              "value": "SIN"
            }
          },
          "OriginDestinationKey": "OD1" //Origin destination onward
        }
      ]
    }
  }
}
```

### 2. FlightPrice

Once the user selects a particular offer from the VDC AirShopingRS, the VDC FlightPriceRQ has to be constructed using the OfferID, OfferItemID and Pax details for the offer that was selected. The FlightPriceRQ for one way search for one PAX will look like below:

```json
{
  "Travelers": {
    "Traveler": [
      {
        "AnonymousTraveler": [
          {
            "PTC": {
              "value": "ADT", //Adult
              "Quantity": 1
            }
          }
        ]
      }
    ]
  },
  "Query": {
    "OriginDestination": [
      {
        "Flight": [...]
      }
    ],
    "Offers": {
      "Offer": [
        {
          "OfferID": {  //OfferId from AirShoppingRS
            "value": "1H126Z_37VVHBZJE4EMX3UZ6S86FGMQVOBY",
            "Owner": "26",
            "Channel": "NDC"
          },
          "OfferItemIDs": {
            "OfferItemID": [ //OfferItemID from AirShoppingRS
              {
                "value": "1H126Z_37VVHBZJE4EMX3UZ6S86FGMQVOBY-1-1",
                "refs": [
                  "26-PAX1"
                ]
              }
            ]
          }
        }
      ]
    }
  },
  "DataLists": {...},
  "ShoppingResponseID": {
    "Owner": "26",
    "ResponseID": {
      "value": "iqAIwcY2gr0h8T5oz7adzDx2Gf6sV6XdNuxZe3QSr4M-SQ"
    }
  }
}
```

#### Mapping Document: AirShoppingRS → FlightPriceRQ

| AirShoppingRS | FlightPriceRQ |
|--------------|---------------|
| `OffersGroup/AirlineOffers/AirlineOffer/OfferID/value` | `Query/Offers/Offer/OfferID/value` |
| `OffersGroup/AirlineOffers/AirlineOffer/OfferID/Owner` | `Query/Offers/Offer/OfferID/Owner` |
| `OffersGroup/AirlineOffers/AirlineOffer/OfferID/Channel` | `Query/Offers/Offer/OfferID/Channel` |
| `OffersGroup/AirlineOffers/AirlineOffer/PricedOffer/OfferPrice/OfferItemID` | `Query/Offers/Offer/OfferItemIDs/OfferItemID/value` |
| `OffersGroup/AirlineOffers/AirlineOffer/PricedOffer/OfferPrice/RequestedDate/Associations/AssociatedTraveler/TravelerReferences` | `Query/Offers/Offer/OfferItemIDs/OfferItemID/refs` |
| `DataLists/FlightSegmentList/FlightSegment/SegmentKey` | `Query/OriginDestination/Flight/SegmentKey` |
| `DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value` | `Query/OriginDestination/Flight/Departure/AirportCode/value` |
| `DataLists/FlightSegmentList/FlightSegment/Date` | `Query/OriginDestination/Flight/Departure/Date` |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value` | `Query/OriginDestination/Flight/Arrival/AirportCode/value` |
| `DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey` | `DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey` |
| `DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value` | `DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value` |
| `Metadata/Other/OtherMetadata/DescriptionMetadatas/DescriptionMetadata/AugmentationPoint/AugPoint/Key` | `ShoppingResponseID/ResponseID/value` |

### 3. ServiceList

Once the user selects a particular offer from the VDC FlightPriceRS, the VDC ServiceListRQ has to be constructed using the OfferID, OfferItemID and Pax details for the offer that was selected. The ServiceListRQ for one way for one PAX search will look like below:

```json
{
  "Travelers": {
    "Traveler": [
      {
        "AnonymousTraveler": [
          {
            "ObjectKey": "PAX1",
            "PTC": {
              "value": "ADT" //Adult
            }
          }
        ]
      }
    ]
  },
  "Query": {
    "OriginDestination": [
      {
        "Flight": [
          {
            "SegmentKey": "SEG2",
            "Departure": {
              "AirportCode": {
                "value": "BOM"
              },
              "Date": "2025-03-29T11:50:00.000",
              "Time": "11:50",
              "AirportName": "Chhatrapati Shivaji International Airport",
              "Terminal": {
                "Name": "2"
              }
            },
            "Arrival": {
              "AirportCode": {
                "value": "SIN"
              },
              "Date": "2025-03-29T19:50:00.000",
              "Time": "19:50",
              "AirportName": "Changi Airport",
              "Terminal": {
                "Name": "0"
              }
            },
            "MarketingCarrier": {...},
            "Equipment": {...},
            "FlightDetail": {...}
          }
        ]
      }
    ],
    "Offers": {
      "Offer": [
        {
          "OfferID": {
            "value": "1H126Z_37VVHBZJE4EMX3UZ6S86FGMQVOBY",
            "Owner": "26",
            "Channel": "NDC"
          },
          "OfferItemIDs": {
            "OfferItemID": [
              {
                "value": "1H126Z_37VVHBZJE4EMX3UZ6S86FGMQVOBY-1-1"
              }
            ]
          }
        }
      ]
    }
  },
  "ShoppingResponseID": {
    "ResponseID": {
      "value": "iqAIwcY2gr0h8T5oz7adzDx2Gf6sV6XdNuxZe3QSr4M-SQ"
    }
  }
}
```

#### Mapping Document: FlightPriceRS → ServiceListRQ

| FlightPriceRS | ServiceListRQ |
|--------------|---------------|
| `DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey` | `Travelers/Traveler/AnonymousTraveler/ObjectKey` |
| `DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value` | `Travelers/Traveler/AnonymousTraveler/PTC/value` |
| `DataLists/FlightSegmentList/FlightSegment/SegmentKey` | `Query/OriginDestination/Flight/SegmentKey` |
| `DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value` | `Query/OriginDestination/Flight/Departure/AirportCode/value` |
| `DataLists/FlightSegmentList/FlightSegment/Departure/Date` | `Query/OriginDestination/Flight/Departure/Date` |
| `DataLists/FlightSegmentList/FlightSegment/Departure/Time` | `Query/OriginDestination/Flight/Departure/Time` |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value` | `Query/OriginDestination/Flight/Arrival/AirportCode/value` |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/Terminal/Name` | `Query/OriginDestination/Flight/Arrival/Terminal/Name` |
| `PricedFlightOffers/PricedFlightOffer/OfferID/value` | `Query/Offers/Offer/OfferID/value` |
| `PricedFlightOffers/PricedFlightOffer/OfferID/Owner` | `Query/Offers/Offer/OfferID/Owner` |
| `PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID` | `Query/Offers/Offer/OfferItemIDs/OfferItemID/value` |
| `ShoppingResponseID/ResponseID/value` | `ShoppingResponseID/ResponseID/value` |

### 4. SeatAvailability

The VDC SeatAvailability API allows users to search for seats per passenger based on the availability from the airline. The API has the ability to retrieve seat maps for one or more flight segments. This service returns a priced seat map for the requested flight segments in a requested cabin.

The SeatAvailabilityRQ of one way one PAX will look like below:

```json
{
  "Travelers": {
    "Traveler": [
      {
        "RecognizedTraveler": [...],
        "AnonymousTraveler": [
          {
            "ObjectKey": "PAX1",
            "PTC": {
              "value": "ADT"
            }
          }
        ]
      }
    ]
  },
  "Query": {
    "OriginDestination": [
      {
        "FlightSegmentReference": [
          {
            "ref": "SEG2"
          }
        ]
      }
    ],
    "Offers": {
      "Offer": [
        {
          "OfferID": {
            "value": "1H126Z_37VVHBZJE4EMX3UZ6S86FGMQVOBY",
            "Owner": "26",
            "Channel": "NDC"
          },
          "OfferItemIDs": {
            "OfferItemID": [
              {
                "value": "1H126Z_37VVHBZJE4EMX3UZ6S86FGMQVOBY-1-1"
              }
            ]
          }
        }
      ]
    }
  },
  "DataLists": {
    "FlightSegmentList": {
      "FlightSegment": [
        {
          "SegmentKey": "SEG2",
          "Departure": {
            "AirportCode": {
              "value": "BOM"
            },
            "Date": "2025-03-29T11:50:00.000",
            "Time": "11:50",
            "AirportName": "Chhatrapati Shivaji International Airport",
            "Terminal": {
              "Name": "2"
            }
          },
          "Arrival": {
            "AirportCode": {
              "value": "SIN"
            },
            "Date": "2025-03-29T19:50:00.000",
            "Time": "19:50",
            "AirportName": "Changi Airport",
            "Terminal": {
              "Name": "0"
            }
          },
          "MarketingCarrier": {...},
          "Equipment": {...},
          "FlightDetail": {...}
        }
      ]
    },
    "FareList": {
      "FareGroup": [
        {
          "ListKey": "FG-120813743178554",
          "Fare": {
            "FareCode": {
              "Code": "749"
            }
          },
          "FareBasisCode": {
            "Code": "W14IIOB1"
          }
        }
      ]
    }
  },
  "ShoppingResponseID": {
    "ResponseID": {
      "value": "iqAIwcY2gr0h8T5oz7adzDx2Gf6sV6XdNuxZe3QSr4M-SQ"
    }
  }
}
```

#### Mapping Document: FlightPriceRS → SeatAvailabilityRQ

| FlightPriceRS | SeatAvailabilityRQ |
|--------------|-------------------|
| `DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey` | `Travelers/Traveler/AnonymousTraveler/ObjectKey` |
| `DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value` | `Travelers/Traveler/AnonymousTraveler/PTC/value` |
| `DataLists/FlightSegmentList/FlightSegment/SegmentKey` | `Query/OriginDestination/FlightSegmentReference/ref` |
| `PricedFlightOffers/PricedFlightOffer/OfferID/value` | `Query/Offers/Offer/OfferID/value` |
| `PricedFlightOffers/PricedFlightOffer/OfferID/Owner` | `Query/Offers/Offer/OfferID/Owner` |
| `PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID` | `Query/Offers/Offer/OfferItemIDs/OfferItemID/value` |
| `DataLists/FareList/FareGroup/ListKey` | `DataLists/FareList/FareGroup/ListKey` |
| `DataLists/FareList/FareGroup/FareBasisCode/Code` | `DataLists/FareList/FareGroup/FareBasisCode/Code` |
| `DataLists/FlightSegmentList/FlightSegment/SegmentKey` | `DataLists/FlightSegmentList/FlightSegment/SegmentKey` |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value` | `DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value` |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/Date` | `DataLists/FlightSegmentList/FlightSegment/Arrival/Date` |
| `DataLists/FlightSegmentList/FlightSegment/Arrival/Time` | `DataLists/FlightSegmentList/FlightSegment/Arrival/Time` |
| `DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value` | `DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value` |
| `DataLists/FlightSegmentList/FlightSegment/Departure/Date` | `DataLists/FlightSegmentList/FlightSegment/Departure/Date` |
| `DataLists/FlightSegmentList/FlightSegment/Departure/Time` | `DataLists/FlightSegmentList/FlightSegment/Departure/Time` |
| `DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/AirlineID/value` | `DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/AirlineID/value` |
| `DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/FlightNumber/value` | `DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/FlightNumber/value` |
| `ShoppingResponseID/ResponseID/value` | `ShoppingResponseID/ResponseID/value` |

### 5. OrderCreate

Once the user receives a successful ServiceListRS and SeatAvailabilityRS, the VDC OrderCreateRQ API is constructed by adding the required fields such as OfferRefId, OfferItemRefId and pax details.

A sample One way OrderCreateRQ for One PAX would look like below:

```json
{
  "Query": {
    "Passengers": { //Passenger details
      "Passenger": [
        {
          "ObjectKey": "PAX1",
          "PTC": {
            "value": "ADT"
          },
          "Name": {
            "Surname": {
              "value": "DOE"
            },
            "Given": [
              {
                "value": "JON"
              }
            ],
            "Title": "Mr"
          },
          "AdditionalRoles": {
            "PaymentContactInd": true
          },
          "Contacts": {
            "Contact": [
              {
                "AddressContact": {
                  "Street": [
                    "Thapasya Building, 3rd ",
                    "Floor, Infopark Campus"
                  ],
                  "CityName": "Cochin",
                  "CountrySubDivisionCode": "",
                  "PostalCode": "673328",
                  "CountryCode": {
                    "value": "IN"
                  }
                },
                "EmailContact": {
                  "Address": {
                    "value": "ABC.XYZ@CC.COM"
                  }
                },
                "PhoneContact": {
                  "Application": "Home",
                  "Number": [
                    {
                      "value": "9987655232",
                      "CountryCode": "91"
                    }
                  ]
                }
              }
            ]
          },
          "Age": {
            "BirthDate": {
              "value": "1983-06-11"
            }
          },
          "Gender": {
            "value": "Male"
          }
        }
      ]
    },
    "OrderItems": {
      "ShoppingResponse": {
        "Owner": "26",
        "Offers": {
          "Offer": [
            {
              "OfferID": { // OfferID from FlightPriceRS
                "ObjectKey": "1H126Z_SYASZF7UUDCFW8WCD9C2ALWNBXRB",
                "value": "1H126Z_SYASZF7UUDCFW8WCD9C2ALWNBXRB",
                "Owner": "26",
                "Channel": "NDC"
              },
              "OfferItems": {
                "OfferItem": [ //OfferItemID from FlightPriceRS
                  {
                    "OfferItemID": {
                      "value": "1H126Z_SYASZF7UUDCFW8WCD9C2ALWNBXRB-1-1",
                      "Owner": "26",
                      "Channel": "NDC"
                    }
                  }
                ]
              }
            }
          ]
        },
        "ResponseID": {
          "value": "cvQvB9a83M7vgW7J5-W1hH8Xb71aPrrWatfqPdXTJEQ-26"
        }
      },
      "OfferItem": [
        {
          "OfferItemID": {
            "value": "1H126Z_SYASZF7UUDCFW8WCD9C2ALWNBXRB-1-1",
            "Owner": "26",
            "Channel": "NDC"
          },
          "OfferItemType": {
            "DetailedFlightItem": [
              {
                "Price": {
                  "BaseAmount": {
                    "value": 36300,
                    "Code": "INR"
                  },
                  "Taxes": {
                    "Total": {
                      "value": 3246,
                      "Code": "INR"
                    }
                  }
                },
                "FareDetail": { ... },
                "OriginDestination": [
                  {
                    "Flight": [
                      {
                        "Departure": {
                          "Time": "11:45",
                          "AirportCode": {
                            "value": "BOM"
                          },
                          "Date": "2025-05-21",
                          "Terminal": {
                            "Name": "2"
                          }
                        },
                        "Arrival": {
                          "Time": "19:50",
                          "AirportCode": {
                            "value": "SIN"
                          },
                          "Date": "2025-05-21",
                          "Terminal": {
                            "Name": "0"
                          }
                        },
                        "MarketingCarrier": {
                          "AirlineID": {
                            "value": "26"
                          },
                          "Name": "26",
                          "FlightNumber": {
                            "value": "421"
                          }
                        },
                        "Equipment": { ... },
                        "Details": { ... },
                        "ClassOfService": { ... },
                        "SegmentKey": "SEG2"
                      }
                    ],
                    "OriginDestinationKey": "OD1"
                  }
                ],
                "refs": [
                  "PAX1"
                ]
              }
            ]
          }
        },
        {
          "OfferItemID": { //OfferItemID from SeatAvailabilityRS
            "value": "PRICE1-SEG2",
            "refs": [
              "PRICE",
              "cvQvB9a83M7vgW7J5-W1hH8Xb71aPrrWatfqPdXTJEQ-26"
            ],
            "Channel": "NDC"
          },
          "OfferItemType": {
            "SeatItem": [
              {
                "Price": {
                  "Total": {
                    "value": 0,
                    "Code": "INR"
                  }
                },
                "Descriptions": {
                  "Description": [
                    {
                      "Text": {
                        "value": "Service not refundable but value of EMD can be applied on future purchase"
                      }
                    },
                    {
                      "Text": {
                        "value": "Service is not Commissionable"
                      }
                    }
                  ]
                },
                "Location": {
                  "Column": "K",
                  "Row": {
                    "Number": {
                      "value": "42"
                    }
                  },
                  "Characteristics": {
                    "Characteristic": [
                      {
                        "Code": "CH"
                      },
                      {
                        "Code": "FC"
                      },
                      {
                        "Code": "OW"
                      },
                      {
                        "Code": "W"
                      },
                      {
                        "Remarks": {
                          "Remark": [
                            {
                              "value": "A"
                            }
                          ]
                        }
                      }
                    ]
                  }
                },
                "SeatAssociation": [
                  {
                    "SegmentReferences": {
                      "value": [
                        "SEG2"
                      ]
                    },
                    "TravelerReference": "PAX1"
                  }
                ]
              }
            ]
          }
        },
        {
          "OfferItemID": { //OfferItemID from ServiceListRS
            "value": "1H126Z_SYASZF7UUDCFW8WCD9C2ALWNBXRB-27",
            "Owner": "26",
            "refs": [
              "1H126Z_SYASZF7UUDCFW8WCD9C2ALWNBXRB",
              "cvQvB9a83M7vgW7J5-W1hH8Xb71aPrrWatfqPdXTJEQ-26"
            ],
            "Channel": "NDC"
          },
          "OfferItemType": {
            "OtherItem": [
              {
                "refs": [
                  "PAX1",
                  "1-ServiceId26-17"
                ],
                "Price": {
                  "SimpleCurrencyPrice": {
                    "value": 0,
                    "Code": "INR"
                  }
                }
              }
            ]
          }
        }
      ]
    },
    "DataLists": {
      "ServiceList": {
        "Service": [
          {
            "ObjectKey": "PRICE1-SEG2",
            "ServiceID": {
              "value": "SERVICE-1"
            },
            "Name": {
              "value": "FORWARD ZONE"
            },
            "Descriptions": {
              "Description": [
                {
                  "Text": {
                    "value": "Service not refundable but value of EMD can be applied on future purchase"
                  }
                },
                {
                  "Text": {
                    "value": "Service is not Commissionable"
                  }
                }
              ]
            },
            "Price": [
              {
                "Total": {
                  "value": 0,
                  "Code": "INR"
                }
              }
            ],
            "Associations": [
              {
                "Traveler": {
                  "TravelerReferences": [
                    "PAX1"
                  ]
                },
                "Flight": {
                  "originDestinationReferencesOrSegmentReferences": [
                    {
                      "SegmentReferences": {
                        "value": [
                          "SEG2"
                        ]
                      }
                    }
                  ]
                },
                "Offer": {
                  "OfferReferences": [
                    "PRICE"
                  ]
                }
              }
            ],
            "PricedInd": true
          },
          {
            "ObjectKey": "1-ServiceId26-17",
            "ServiceID": {
              "ObjectKey": "1H126Z_SYASZF7UUDCFW8WCD9C2ALWNBXRB-27",
              "value": "SRV17",
              "Owner": "26"
            },
            "Name": {
              "value": "MEAL:LOW FAT MEAL"
            },
            "Descriptions": {
              "Description": [
                {
                  "Text": {
                    "value": "LOW FAT MEAL"
                  }
                },
                {
                  "Text": {
                    "value": "Free"
                  }
                },
                {
                  "Text": {
                    "value": "MEAL"
                  }
                }
              ]
            },
            "Price": [
              {
                "Total": {
                  "value": 0,
                  "Code": "INR"
                }
              }
            ],
            "BookingInstructions": {
              "SSRCode": [
                "LFML"
              ],
              "Method": "SSR"
            },
            "Associations": [
              {
                "Traveler": {
                  "TravelerReferences": [
                    "PAX1"
                  ]
                },
                "Flight": {
                  "originDestinationReferencesOrSegmentReferences": [
                    {
                      "SegmentReferences": {
                        "value": [
                          "SEG2"
                        ]
                      }
                    }
                  ]
                }
              }
            ],
            "PricedInd": true
          }
        ]
      }
    }
  }
}
```

#### Mapping Documents for OrderCreateRQ

##### FlightPriceRS → OrderCreateRQ

Mapping 1: FlightPriceRS to OrderCreateRQ
Source (FlightPriceRS)

Destination (OrderCreateRQ)

DataLists/RecognizedTravelerList/RecognizedTraveler/ObjectKey

Query/Passengers/Passenger/ObjectKey

PricedFlightOffers/PricedFlightOffer/OfferID/Owner

Query/OrderItems/ShoppingResponse/Owner

OfferExpiration/ObjectKey

Query/OrderItems/ShoppingResponse/Offers/Offer/OfferID/value

ShoppingResponseID/ResponseID

Query/OrderItems/ShoppingResponse/ResponseID

PricedFlightOffers/PricedFlightOffer/OfferID/value

Query/OrderItems/ShoppingResponse/Offers/Offer/OfferID/value

PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID

Query/OrderItems/ShoppingResponse/Offers/Offer/OfferItems/OfferItem/OfferItemID/value

PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail

Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price

PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/BaseAmount

Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price/BaseAmount

PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/Taxes

Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price/Taxes

DataLists/FlightSegmentList/FlightSegment/SegmentKey

Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/SegmentKey

DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/FlightNumber/value

Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/MarketingCarrier/FlightNumber/value

DataLists/FareList/FareGroup/FareBasisCode

Query/DataLists/FareList/FareGroup/FareBasisCode

Mapping 2: SeatAvailabilityRS to OrderCreateRQ
Source (SeatAvailabilityRS)

Destination (OrderCreateRQ)

Services/Service/ObjectKey

Query/OrderItems/OfferItem/OfferItemID/value

ShoppingResponseID/ResponseID/value

Query/OrderItems/OfferItem/OfferItemID/refs

Services/Service/Price

Query/OrderItems/OfferItem/OfferItemType/SeatItem/Price

DataLists/SeatList/Seats/Location

Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location

DataLists/SeatList/Seats/Location/Characteristics/Characteristic

Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location/Characteristics/Characteristic

Services/Service/Associations/Flight/.../SegmentReferences/value

Query/OrderItems/OfferItem/OfferItemType/SeatItem/SeatAssociation/SegmentReferences/value

Mapping 3: ServiceListRS to OrderCreateRQ
Source (ServiceListRS)

Destination (OrderCreateRQ)

Services/Service/ServiceID/ObjectKey

Query/OrderItems/OfferItem/OfferItemID/value

Services/Service/ServiceID/Owner

Query/OrderItems/OfferItem/OfferItemID/Owner

ShoppingResponseID/ResponseID/value

Query/OrderItems/OfferItem/OfferItemID/refs

Services/Service/Associations/Traveler/TravelerReferences

Query/OrderItems/OfferItem/OfferItemType/OtherItem/refs

Services/Service/Price

Query/OrderItems/OfferItem/OfferItemType/OtherItem/Price

Services/Service/Price/Total

Query/OrderItems/OfferItem/OfferItemType/OtherItem/Price/SimpleCurrencyPrice