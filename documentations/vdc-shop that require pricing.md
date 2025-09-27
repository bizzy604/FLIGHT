Shopping and booking with Seat and Ancillary which requires pricing

Definition of use case
The user can shop for services like Excess baggage,  Lounge Access etc., using VDC ServiceList API. Seat can be selected using VDC SeatAvailability API. Once the required services and seats are selected, they must be priced using the VDC FlightPrice API before proceeding with booking.

Process
AirShoppingRQ
The user initiates a one way search for flights via the VDC system. The  VDC AirShoppingRQ for one way search for one PAX will look like below:
{
	"Travelers": {
		"Traveler": [
			{
				"AnonymousTraveler": [
					{
						"PTC": {
							"value": "ADT"
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
							"value": "CDG"
						},
						"Date": "2025-04-29"
					},
					"Arrival": {
						"AirportCode": {
							"value": "LHR"
						}
					},
					"OriginDestinationKey": "OD1"
				}
			]
		}
	},
	"Preference": {
		"FarePreferences": {
			"Types": {
				"Type": [
					{
						"Code": "PUBL"
					}
				]
			}
		}
	},
	"ResponseParameters": {
		"ShopResultPreference": "OPTIMIZED",
		"SortOrder": [...]
	}
}





FlightPrice
Once the user selects a particular offer from the VDC AirShopingRS, the VDC FlightPriceRQ has to be constructed using the OfferID, OfferItemID and Pax details for the offer that was selected. The FlightPriceRQ for one way search for one PAX will look like below:

{
	"Travelers": {
		"Traveler": [
			{
				"AnonymousTraveler": [
					{
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
				"Flight": [...]
			}
		],
		"Offers": {
			"Offer": [
				{
					"OfferID": {
						"value": "b2545361-654e-407e-9453-61654ec00001",
						"Owner": "26",
						"Channel": "NDC"
					},
					"OfferItemIDs": {
						"OfferItemID": [
							{
								"value": "a23aac53-6653-4ca4-baac-5366539ca497",
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
		"ResponseID": {
			"value": "6GJmkiaCYz1GgDVuOK1nXZfWu6UTfh5QBtwQHysxiWg-26"
		}
	}
}


ServiceList:
Once the user selects the priced offer from the VDC FlightPriceRS, the VDC ServiceListRQ has to be constructed using the OfferID, OfferItemID and Pax details for the offer that was selected. The ServiceListRQ for one way for one PAX search will look like below:

{
	"Travelers": {
		"Traveler": [
			{
				"AnonymousTraveler": [
					{
						"ObjectKey": "26-PAX1",
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
				"Flight": [
					{
						"SegmentKey": "SEG1",
						"Departure": {
							"AirportCode": {
								"value": "CDG"
							},
							"Date": "2025-04-29T07:35:00.000",
							"Time": "07:35"
						},
						"Arrival": {
							"AirportCode": {
								"value": "LHR"
							},
							"Date": "2025-04-29T08:00:00.000",
							"Time": "08:00"
						}
					}
				]
			}
		],
		"Offers": {
			"Offer": [
				{
					"OfferID": { //Offer details from FlightPriceRS
						"ObjectKey": "b2545361-654e-407e-9453-61654ec00001",
						"value": "b2545361-654e-407e-9453-61654ec00001",
						"Owner": "26",
						"Channel": "NDC"
					},
					"OfferItemIDs": {
						"OfferItemID": [
							{
								"value": "a23aac53-6653-4ca4-baac-5366539ca497"
							}
						]
					}
				}
			]
		}
	},
	"ShoppingResponseID": {
		"ResponseID": {
			"value": "6GJmkiaCYz1GgDVuOK1nXZfWu6UTfh5QBtwQHysxiWg-26"//From FlightPriceRS
		}
	}
}


Mapping Document
FlightPriceRS
ServiceListRQ
FlightPriceRS/DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey
ServiceListRQ/Travelers/Traveler/AnonymousTraveler/ObjectKey
FlightPriceRS/DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value
ServiceListRQ/Travelers/Traveler/AnonymousTraveler/PTC/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/SegmentKey 
ServiceListRQ/Query/OriginDestination/Flight/SegmentKey
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value
ServiceListRQ/Query/OriginDestination/Flight/Departure/AirportCode/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/Date
ServiceListRQ/Query/OriginDestination/Flight/Departure/Date
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/Time
ServiceListRQ/Query/OriginDestination/Flight/Departure/Time
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value
ServiceListRQ/Query/OriginDestination/Flight/Arrival/AirportCode/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Arrival/Terminal/Name
ServiceListRQ/Query/OriginDestination/Flight/Arrival/Terminal/Name
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/value
ServiceListRQ/Query/Offers/Offer/OfferID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner 
ServiceListRQ/Query/Offers/Offer/OfferID/Owner
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID
ServiceListRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/value
FlightPriceRS/ShoppingResponseID/ResponseID/value
ServiceListRQ/ShoppingResponseID/ResponseID/value



SeatAvailability:

The VDC SeatAvailability API allows users to search for seats per passenger based on the availability from the airline. The API has the ability to retrieve seat maps for one or more flight segments.
The SeatAvailabilityRQ for one way for one PAX search will look like below:
{
	"Travelers": {
		"Traveler": [
			{
				"AnonymousTraveler": [
					{
						"ObjectKey": "26-PAX1",
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
						"ref": "SEG1"
					}
				]
			}
		],
		"Offers": {
			"Offer": [
				{
					"OfferID": { //Offer details from FlightPriceRS
						"ObjectKey": "b2545361-654e-407e-9453-61654ec00001",
						"value": "b2545361-654e-407e-9453-61654ec00001",
						"Owner": "26",
						"Channel": "NDC"
					},
					"OfferItemIDs": {
						"OfferItemID": [
							{
								"value": "a23aac53-6653-4ca4-baac-5366539ca497"
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
					"SegmentKey": "SEG1",
					"Departure": {
						"AirportCode": {
							"value": "CDG"
						},
						"Date": "2025-04-29T00:00:00.000",
						"Time": "07:35"
					},
					"Arrival": {
						"AirportCode": {
							"value": "LHR"
						},
						"Date": "2025-04-29T00:00:00.000",
						"Time": "08:00"
					}
				}
			]
		},
		"FareList": {
			"FareGroup": [
				{
					"ListKey": "26-FG-VYSFBNLA-70J",
					"FareBasisCode": {
						"Code": "VYSFBNLA"
					}
				}
			]
		}
	},
	"ShoppingResponseID": {
		"ResponseID": {
			"value": "6GJmkiaCYz1GgDVuOK1nXZfWu6UTfh5QBtwQHysxiWg-26" //From FlightPriceRS
		}
	}
}





Mapping Document:

FlightPriceRS
SeatAvailabilityRQ
FlightPriceRS/DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey
SeatAvailabilityRQ/Travelers/Traveler/AnonymousTraveler/ObjectKey
FlightPriceRS/DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value
SeatAvailabilityRQ/Travelers/Traveler/AnonymousTraveler/PTC/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/SegmentKey 
SeatAvailabilityRQ/Query/OriginDestination/FlightSegmentReference/ref
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/value
SeatAvailabilityRQ/Query/Offers/Offer/OfferID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner 
SeatAvailabilityRQ/Query/Offers/Offer/OfferID/Owner
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID
SeatAvailabilityRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/value
FlightPriceRS/DataLists/FareList/FareGroup/ListKey
SeatAvailabilityRQ/DataLists/FareList/FareGroup/ListKey
FlightPriceRS/DataLists/FareList/FareGroup/FareBasisCode/Code
SeatAvailabilityRQ/DataLists/FareList/FareGroup/FareBasisCode/Code
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/SegmentKey 
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/SegmentKey
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Arrival/Date
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/Arrival/Date
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Arrival/Time
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/Arrival/Time
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/Date
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/Departure/Date
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/Time
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/Departure/Time
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/AirlineID/value
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/AirlineID/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/FlightNumber/value
SeatAvailabilityRQ/DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/FlightNumber/value
FlightPriceRS/ShoppingResponseID/ResponseID/value
SeatAvailabilityRQ/ShoppingResponseID/ResponseID/value


FlightPrice for pricing ancillary and seat
If the PricedInd is false for the selected offer for ancillaries and seat, the ancillaries and seat along with the flight item has to be priced using the VDC FlightPriceRQ API before proceeding with the booking. While pricing, ensure that the required quantity for each ancillary offer is accurately specified.
{
	"Travelers": {
		"Traveler": [
			{
				"AnonymousTraveler": [
					{
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
				"Flight": [
					{
						"SegmentKey": "SEG1",
						"Departure": {
							"AirportCode": {
								"value": "CDG"
							},
							"Date": "2025-04-29T00:00:00.000",
							"Time": "07:35",
							"Terminal": {
								"Name": "2E"
							}
						},
						"Arrival": {
							"AirportCode": {
								"value": "LHR"
							},
							"Date": "2025-04-29T00:00:00.000",
							"Time": "08:00",
							"Terminal": {
								"Name": "4"
							}
						},
						"MarketingCarrier": {
							"AirlineID": {
								"value": "26"
							},
							"FlightNumber": {
								"value": "1680"
							}
						},
						"OperatingCarrier": {
							"AirlineID": {
								"value": "26"
							}
						}
					}
				]
			}
		],
		"Offers": {
			"Offer": [
				{
					"OfferID": {
						"ObjectKey": "b2545361-654e-407e-9453-61654ec00001"
						"value": "b2545361-654e-407e-9453-61654ec00001", //The OfferID value is taken from the previous FlightPriceRS
						"Owner": "26",
						"Channel": "NDC"
					},
					"OfferItemIDs": {
						"OfferItemID": [
							{
								"value": "a23aac53-6653-4ca4-baac-5366539ca497", //Flight Item will be taken from previous FlightPriceRS
								"refs": [
									"PAX1"
								]
							},
							{
								"value": "a83f92af-d3c4-47d4-bf92-afd3c4070002", //Ancillary OfferItem will be taken from ServiceListRS
								"refs": [
									"PAX1"
								],
								"Quantity": 1 //The total quantity of ancillary product selected can be provided here.
							},
							{
								"value": "d7ffb7f9-8af7-4125-bfb7-f98af7310002", //Seat Item is taken from SeatAvailabilityRS
								"SelectedSeat": [
									{
										"Location": {
											"Column": "A",
											"Row": {
												"Number": {
													"value": "10"
												}
											},
											"Characteristics": {
												"Characteristic": [
													{
														"Code": "AM"
													},
													{
														"Code": "CH"
													},
													{
														"Code": "LS"
													},
													{
														"Code": "O"
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
														"SEG1"
													]
												},
												"TravelerReference": "PAX1"
											}
										]
									}
								],
								"Quantity": 1
							}
						]
					}
				}
			]
		}
	},
	"DataLists": {
		"AnonymousTravelerList": {
			"AnonymousTraveler": [
				{
					"ObjectKey": "PAX1",
					"PTC": {
						"value": "ADT"
					}
				}
			]
		}
	},
	"ShoppingResponseID": {
		"Owner": "26",
		"ResponseID": {
			"value": "6GJmkiaCYz1GgDVuOK1nXZfWu6UTfh5QBtwQHysxiWg-26" //Taken from previous FlightPriceRS
		}
	}
}


Mapping document:
FlightPriceRS (Received before triggering ServiceList/SeatAvailability)
FlightPriceRQ (For Pricing seat and ancillaries triggered after ServiceList/SeatAvailability)
FlightPriceRS/DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value
FlightPriceRQ/Travelers/Traveler/AnonymousTraveler/PTC/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/SegmentKey 
FlightPriceRQ/Query/OriginDestination/Flight/SegmentKey
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value
FlightPriceRQ/Query/OriginDestination/Flight/Departure/AirportCode/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/Date
FlightPriceRQ/Query/OriginDestination/Flight/Departure/Date
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value
FlightPriceRQ/Query/OriginDestination/Flight/Arrival/AirportCode/value
FlightPriceRS/AirlineOffers/AirlineOffer/PricedOffer/OfferID/value
FlightPriceRQ/Query/Offers/Offer/OfferID/value
FlightPriceRS/AirlineOffers/AirlineOffer/PricedOffer/OfferID/Owner
FlightPriceRQ/Query/Offers/Offer/OfferID/Owner
FlightPriceRS/AirlineOffers/AirlineOffer/PricedOffer/OfferID/Channel
FlightPriceRQ/Query/Offers/Offer/OfferID/Channel
FlightPriceRS/AirlineOffers/AirlineOffer/PricedOffer/OfferPrice/RequestedDate/Associations/AssociatedTraveler/TravelerReferences
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/refs
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/value
$.DataLists.FlightSegmentList.FlightSegment[0].Departure.Date
FlightPriceRQ/ShoppingResponseID/Owner
FlightPriceRS/ShoppingResponseID/ResponseID/value
FlightPriceRQ/ShoppingResponseID/ResponseID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner 
FlightPriceRQ/DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey
FlightPriceRS/DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value
FlightPriceRQ/DataLists/AnonymousTravelerList/AnonymousTraveler/PTC


ServiceListRS
FlightPriceRQ (Pricing seat and ancillaries triggered after ServiceList/SeatAvailability)
ServiceListRS/Services/Service/ServiceID/ObjectKey
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/value
ServiceListRS/Services/Service/Associations/Traveler/TravelerReferences
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/refs




SeatAvailabilityRS
FlightPriceRQ (For Pricing seat and ancillaries triggered after ServiceList/SeatAvailability)
SeatAvailabilityRS/Services/Service/ObjectKey 
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/value
SeatAvailabilityRS/Services/Service/Associations/Traveler/TravelerReferences
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/refs
SeatAvailabilityRS/DataLists/SeatList/Seats/Location/Column
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/SelectedSeat/Location/Column
SeatAvailabilityRS/DataLists/SeatList/Seats/Location/Row/Number/value
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/SelectedSeat/Location/Row/Number/value
SeatAvailabilityRS/DataLists/SeatList/Seats/Location/Characteristics/Characteristic/Code
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/SelectedSeat/Location/Characteristics/Characteristic/Code
SeatAvailabilityRS/DataLists/SeatList/Seats/Location/Characteristics/Characteristic/Remarks/Remark/value
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/SelectedSeat/Location/Characteristics/Characteristic/Remarks/Remark/value
SeatAvailabilityRS/Services/Service/Associations/Flight/originDestinationReferencesOrSegmentReferences/SegmentReferences/value
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/SelectedSeat/SeatAssociation/SegmentReferences/value
SeatAvailabilityRS/Services/Service/Associations/Traveler/TravelerReferences
FlightPriceRQ/Query/Offers/Offer/OfferItemIDs/OfferItemID/SelectedSeat/SeatAssociation/TravelerReference


OrderCreate:
Once the user receives a successful FlightPriceRS, the VDC OrderCreateRQ API is constructed by adding the required fields such as OfferRefId, OfferItemRefId and pax details. 
A sample One way OrderCreateRQ for One PAX would look like below:
{
	"Query": {
		"Passengers": {...},
		"OrderItems": {
			"ShoppingResponse": {
				"Owner": "26",
				"Offers": {
					"Offer": [
						{
							"OfferID": { //Offer details from latest FlightPriceRS
								"ObjectKey": "cb3cecd5-62b5-4073-bcec-d562b5800001",
								"value": "cb3cecd5-62b5-4073-bcec-d562b5800001",
								"Owner": "26",
								"Channel": "NDC"
							},
							"OfferItems": {
								"OfferItem": [
									{
										"OfferItemID": {
											"value": "d670f116-83f9-4f98-b0f1-1683f9ff98ae",
											"Owner": "26"
										}
									}
								]
							}
						}
					]
				},
				"ResponseID": {
					"value": "QNuOt8xFDSYvsH6JEr67BbaCyM7kSDEbKhzybYjD9Eo-AF"
				}
			},
			"OfferItem": [
				{
					"OfferItemID": {
						"value": "d670f116-83f9-4f98-b0f1-1683f9ff98ae",
						"Owner": "26",
						"Channel": "NDC"
					},
					"OfferItemType": {
						"DetailedFlightItem": [
							{
								"Price": {...},
								"OriginDestination": [...],	
								"refs": [
									"PAX1"
								]
							}
						]
					}
				},
				{
					"OfferItemID": {
						"value": "a58262f6-36c6-438b-8262-f636c693000c",
						"refs": [
							"cb3cecd5-62b5-4073-bcec-d562b5800001",
							"QNuOt8xFDSYvsH6JEr67BbaCyM7kSDEbKhzybYjD9Eo-AF"
						],
						"Owner": "26",
						"Channel": "NDC"
					},
					"OfferItemType": {
						"OtherItem": [
							{
								"refs": [
									"PAX1",
									"SRV1-BAG"
								],
								"Price": {...}
							}
						]
					}
				},
				{
					"OfferItemID": {
						"value": "eb27f9e4-68ed-4f55-a7f9-e468ed5f0002",
						"refs": [
							"cb3cecd5-62b5-4073-bcec-d562b5800001",
							"QNuOt8xFDSYvsH6JEr67BbaCyM7kSDEbKhzybYjD9Eo-26"
						],
						"Owner": "26",
						"Channel": "NDC"
					},
					"OfferItemType": {
						"SeatItem": [
							{
								"Price": {...},
								"Descriptions": {
									"Description": [
										{
											"Text": {
												"value": "ECONOMY COMFORT SEAT"
											}
										}
									]
								},
								"Location": {
									"Column": "C",
									"Row": {
										"Number": {
											"value": "6"
										}
									},
									"Characteristics": {
										"Characteristic": [
											{
												"Code": "AM"
											},
											{
												"Code": "CH"
											},
											{
												"Code": "LS"
											},
											{
												"Code": "O"
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
												"SEG1"
											]
										},
										"TravelerReference": "PAX1"
									}
								]
							}
						]
					}
				}
			]
		},
		"DataLists": {
			"FareList": {...},
			"ServiceList": {
				"Service": [
					{
						"ObjectKey": "a83f92af-d3c4-47d4-bf92-afd3c4070002",
						"ServiceID": {
							"value": "SRV1-BAG",
							"Owner": "26"
						},
						"Name": {
							"value": "BAG:LUGGAGE-FIRST ADDITIONAL BAG"
						},
						"Descriptions": {
							"Description": [
								{
									"Text": {
										"value": "1 ABAG x 23 KG"
									}
								}
							]
						},
						"Price": [
							{
								"Total": {
									"value": 8705,
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
													"SEG1"
												]
											}
										}
									]
								}
							}
						],
						"PricedInd": false
					},
					{
						"ObjectKey": "eb27f9e4-68ed-4f55-a7f9-e468ed5f0002",
						"ServiceID": {
							"value": "SRV2-SEAT",
							"Owner": "26"
						},
						"Name": {
							"value": "SEAT"
						},
						"Descriptions": {
							"Description": [
								{
									"Text": {
										"value": "ECONOMY COMFORT SEAT"
									}
								}
							]
						},
						"Price": [
							{
								"Total": {
									"value": 1887,
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
													"SEG1"
												]
											}
										}
									]
								}
							}
						],
						"PricedInd": false
					}
				]
			}
		},
		"Metadata": {...}
     }
}





Mapping Document:

FlightPriceRS
OrderCreateRQ
FlightPriceRS/DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey
OrderCreateRQ/Query/Passengers/Passenger/ObjectKey
FlightPriceRS/DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value
OrderCreateRQ/Query/Passengers/Passenger/PTC/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner
OrderCreateRQ/Query/OrderItems/ShoppingResponse/Owner
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/ObjectKey
OrderCreateRQ/Query/OrderItems/ShoppingResponse/Offers/Offer/OfferID/ObjectKey
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/value
OrderCreateRQ/Query/OrderItems/ShoppingResponse/Offers/Offer/OfferID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner
OrderCreateRQ/Query/OrderItems/ShoppingResponse/Offers/Offer/OfferID/Owner
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Channel
OrderCreateRQ/Query/OrderItems/ShoppingResponse/Offers/Offer/OfferID/Channel
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID
OrderCreateRQ/Query/OrderItems/ShoppingResponse/Offers/Offer/OfferItems/OfferItem/OfferItemID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner
OrderCreateRQ/Query/OrderItems/ShoppingResponse/Offers/Offer/OfferItems/OfferItem/OfferItemID/Owner  
FlightPriceRS/ShoppingResponseID/ResponseID/value
OrderCreateRQ/Query/OrderItems/ShoppingResponse/ResponseID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner 
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/Owner
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/BaseAmount/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price/BaseAmount/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/BaseAmount/Code
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price/BaseAmount/Code
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/Taxes/Total/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price/Taxes/Total/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/Taxes/Total/Code
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/Price/Taxes/Total/Code
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/AirportCode/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Departure/AirportCode/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Departure/Date
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Departure/Date
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/Arrival/AirportCode/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/Arrival/AirportCode/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/AirlineID/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/MarketingCarrier/AirlineID/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/MarketingCarrier/FlightNumber/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/MarketingCarrier/FlightNumber/value
FlightPriceRS/DataLists/FlightSegmentList/FlightSegment/SegmentKey 
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/OriginDestination/Flight/SegmentKey
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedTraveler/TravelerReferences
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/DetailedFlightItem/refs
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/Owner
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/refs
FlightPriceRS/ShoppingResponseID/ResponseID/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/refs
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/TotalAmount/SimpleCurrencyPrice/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/SeatItem/Price/Total/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/TotalAmount/SimpleCurrencyPrice/Code
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/SeatItem/Price/Total/Code
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedService/SeatAssignment/Seat/Location/Column
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location/Column
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedService/SeatAssignment/Seat/Location/Row/Number/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location/Row/Number/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedService/SeatAssignment/Seat/Location/Characteristics/Characteristic/Code
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location/Characteristics/Characteristic/Code
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedService/SeatAssignment/Seat/Location/Characteristics/Characteristic/Remarks/Remark/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/SeatItem/Location/Characteristics/Characteristic/Remarks/Remark/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/ApplicableFlight/FlightSegmentReference
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/SeatItem/SeatAssociation/SegmentReferences/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedTraveler/TravelerReferences
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/SeatItem/SeatAssociation/TravelerReference
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/Owner 
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/Owner
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferID/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/refs
FlightPriceRS/ShoppingResponseID/ResponseID/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemID/refs
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedTraveler/TravelerReferences
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/OtherItem/refs
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/ApplicableFlight/FlightSegmentReference/ref
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/OtherItem/refs
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/Associations/AssociatedService/ServiceReferences
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/OtherItem/refs
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/TotalAmount/SimpleCurrencyPrice/value
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/OtherItem/Price/SimpleCurrencyPrice/value
FlightPriceRS/PricedFlightOffers/PricedFlightOffer/OfferPrice/RequestedDate/PriceDetail/TotalAmount/SimpleCurrencyPrice/Code
OrderCreateRQ/Query/OrderItems/OfferItem/OfferItemType/OtherItem/Price/SimpleCurrencyPrice/Code
FlightPriceRS/DataLists/FareList/FareGroup/ListKey
OrderCreateRQ/Query/DataLists/FareList/FareGroup/ListKey 
FlightPriceRS/DataLists/FareList/FareGroup/FareBasisCode/Code
OrderCreateRQ/Query/DataLists/FareList/FareGroup/FareBasisCode/Code
FlightPriceRS/DataLists/ServiceList/Service/ObjectKey
OrderCreateRQ/Query/DataLists/ServiceList/Service/ObjectKey
FlightPriceRS/DataLists/ServiceList/Service/ServiceID/value
OrderCreateRQ/Query/DataLists/ServiceList/Service/ServiceID/value
FlightPriceRS/DataLists/ServiceList/Service/ServiceID/Owner
OrderCreateRQ/Query/DataLists/ServiceList/Service/ServiceID/Owner
FlightPriceRS/DataLists/ServiceList/Service/Name/value
OrderCreateRQ/Query/DataLists/ServiceList/Service/Name/value
FlightPriceRS/DataLists/ServiceList/Service/Price/Total/value
OrderCreateRQ/Query/DataLists/ServiceList/Service/Price/Total/value
FlightPriceRS/DataLists/ServiceList/Service/Price/Total/Code
OrderCreateRQ/Query/DataLists/ServiceList/Service/Price/Total/Code
FlightPriceRS/DataLists/ServiceList/Service/Associations/Traveler/TravelerReferences
OrderCreateRQ/Query/DataLists/ServiceList/Service/Associations/Traveler/TravelerReferences
FlightPriceRS/DataLists/ServiceList/Service/Associations/Flight/originDestinationReferencesOrSegmentReferences/SegmentReferences/value
OrderCreateRQ/Query/DataLists/ServiceList/Service/Associations/Flight/originDestinationReferencesOrSegmentReferences/SegmentReferences/value


Success
A successful transaction means the user completes a one-way flight booking with pricing and addition of both seat and ancillaries smoothly:
✅ AirShopping retrieves all relevant flights, including personalized offers.Read more details in the Concept Section.
✅ FlightPrice returns the correct fare, ensuring transparency in pricing.
✅ ServiceList successfully provides offers for paid or free services that can be added  to the order. 
✅ SeatAvailability successfully provides offers for paid or free seats that can be added to the order.
✅ FlightPrice returns the confirmed fare of the ancillary and seat selected, ensuring transparency in pricing. Read more details in the Concept Section.
✅ OrderCreate successfully adds the services, providing an immediate confirmation with an EMD-ticket in the response OrderViewRS if the payment is successful.


Click here to view worked examples on one way shop to book with seat and ancillaries which requires pricing

In addition to the combined shopping booking of seats and ancillaries together (where pricing is required), the following scenarios are also commonly encountered and must be handled by the API customer:

Shopping and booking with Seat which requires pricing
Definition of use case
Users can shop for available seats using the VDC SeatAvailability API. If the selected seat requires pricing, it must be priced using the VDC FlightPriceRQ API before proceeding with the booking.
Success
A successful transaction means the traveler completes a booking with the seat priced and added correctly to the order.
Click here to view worked examples on one way shop to book with seat which requires pricing
Shopping and booking with Ancillary which requires pricing
Definition of use case
Users can shop for additional ancillaries (e.g., baggage, lounge access) using the VDC ServiceList API. If the selected ancillary requires pricing, it must be priced using the VDC FlightPriceRQ API before proceeding with the booking.
Success
A successful transaction means the traveler completes a booking with the priced ancillary added correctly to the order.
Click here to view worked examples on one way shop to book with ancillary which requires pricing

Shopping and booking with Seat and Ancillary where either one of them requires pricing
Definition of use case
Users can shop for ancillary services like Excess Baggage, Lounge Access etc using the VDC ServiceList API, while seat selection is done through the VDC SeatAvailability API. If either the selected seat or ancillary service requires pricing, the specific item only must be priced using the VDC FlightPriceRQ API before proceeding with the booking. The item that doesn’t require pricing should be passed directly in the OrderCreate API.
Success
A successful transaction means the traveler completes a booking with both services (priced or unpriced as applicable) added correctly to the order,


Click here to view worked examples on one way shop to book with seat and ancillaries where either of the one requires pricing
Shop using FQTV
