import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  console.log('[[ DEBUG ]] Next.js /api/verteil/flight-price route HIT');
  try {
    const body = await request.json();
    
    // DEBUG: Log flight price request summary
    console.log('[[ DEBUG ]] Flight price request - Offer ID:', body.offer_id);
    console.log('[[ DEBUG ]] Shopping Response ID:', body.shopping_response_id);
    console.log('[[ DEBUG ]] Air Shopping RS present:', !!body.air_shopping_rs);
    
    // Forward the request to the backend
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';
    console.log('[[ DEBUG ]] Forwarding to backend URL:', `${backendUrl}/api/verteil/flight-price`);
    
    const response = await fetch(`${backendUrl}/api/verteil/flight-price`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    
    // DEBUG: Log the flight price response
    console.log('[[ DEBUG ]] Flight price backend response status:', response.status);
    console.log('[[ DEBUG ]] Flight price backend response keys:', data ? Object.keys(data) : 'No data');
    console.log('[[ DEBUG ]] Flight price response data:', JSON.stringify(data, null, 2));
    
    // Extract cache key from response metadata for frontend use
    if (data && data.metadata && data.metadata.cache_key) {
      console.log('[[ DEBUG ]] Flight price cache key:', data.metadata.cache_key);
      // Store cache key in response for frontend to use in order creation
      data.flight_price_cache_key = data.metadata.cache_key;
    } else {
      console.log('[[ DEBUG ]] No cache key found in response metadata');
      console.log('[[ DEBUG ]] Response structure:', data ? Object.keys(data) : 'No data');
      if (data && data.metadata) {
        console.log('[[ DEBUG ]] Metadata keys:', Object.keys(data.metadata));
      }
    }
    
    // Store the raw response for direct backend submission (cache bypass)
    // Create a copy of the response data to avoid circular references
    if (data) {
      const rawResponseCopy = JSON.parse(JSON.stringify(data));
      data.raw_response = rawResponseCopy;
      console.log('[[ DEBUG ]] Added raw_response to flight price data for cache bypass');
      console.log('[[ DEBUG ]] Raw response structure:', rawResponseCopy ? Object.keys(rawResponseCopy) : 'No raw response');
    }
    
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error forwarding flight-price request:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}