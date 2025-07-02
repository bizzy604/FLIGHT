import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // [PASSENGER DEBUG] Log the request being forwarded to backend
    console.log('[PASSENGER DEBUG] Frontend API Route - Forwarding air shopping request to backend:');
    console.log('[PASSENGER DEBUG] Passenger counts:', {
      numAdults: body.numAdults,
      numChildren: body.numChildren,
      numInfants: body.numInfants,
      total: (body.numAdults || 0) + (body.numChildren || 0) + (body.numInfants || 0)
    });
    console.log('[PASSENGER DEBUG] Full request body:', JSON.stringify(body, null, 2));

    // Forward the request to the backend
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';
    const response = await fetch(`${backendUrl}/api/verteil/air-shopping`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    // [PASSENGER DEBUG] Log the response from backend
    console.log('[PASSENGER DEBUG] Frontend API Route - Received response from backend:');
    console.log('[PASSENGER DEBUG] Response status:', response.status);
    console.log('[PASSENGER DEBUG] Response data keys:', data ? Object.keys(data) : 'No data');
    if (data?.data?.raw_response?.DataLists?.AnonymousTravelerList) {
      console.log('[PASSENGER DEBUG] AnonymousTravelerList from backend:', JSON.stringify(data.data.raw_response.DataLists.AnonymousTravelerList, null, 2));
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error forwarding air-shopping request:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}