import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward the request to the backend
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';

    const response = await fetch(`${backendUrl}/api/verteil/flight-price`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    // Extract cache key from response metadata for frontend use
    // The backend returns { status: 'success', data: { metadata: { flight_price_cache_key: ... } } }
    if (data && data.data && data.data.metadata && data.data.metadata.flight_price_cache_key) {
      // Store cache key at top level for easier access
      data.flight_price_cache_key = data.data.metadata.flight_price_cache_key;
      console.log('[Flight Price API] Found flight_price_cache_key in metadata:', data.flight_price_cache_key);
    } else if (data && data.flight_price_cache_key) {
      // Backend might also send it at top level
      console.log('[Flight Price API] Found flight_price_cache_key at top level:', data.flight_price_cache_key);
    } else {
      console.warn('[Flight Price API] No flight_price_cache_key found in response');
    }

    // Pass through the raw_response from backend if it exists (when caching failed)
    // Otherwise, the backend has cached it and will retrieve using the cache key
    // Don't create a synthetic raw_response - use what the backend provides

    // Return the backend response directly without double-wrapping
    // The backend already returns the correct structure with status and data
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}