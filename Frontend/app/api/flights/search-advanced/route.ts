// app/api/flights/search-advanced/route.ts
import { NextResponse } from 'next/server';
import { logger } from '@/utils/logger';
import axios from 'axios';

export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  try {
    const ndcPayload = await req.json();
    logger.info('Advanced flight search request - forwarding NDC payload to backend', { 
      payload: JSON.stringify(ndcPayload, null, 2) 
    });

    // Forward the raw NDC payload directly to the existing backend endpoint
    const response = await axios.post(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/verteil/air-shopping`,
      ndcPayload,
      {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      }
    );

    return NextResponse.json(response.data);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    logger.error('Error in advanced flight search', { error: errorMessage });
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}