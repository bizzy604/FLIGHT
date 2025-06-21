import { NextResponse } from 'next/server';
import { logger } from './logger';

type ErrorWithMessage = {
  message: string;
  status?: number;
  code?: string;
  details?: any;
};

export class ApiError extends Error {
  status: number;
  code: string;
  details: any;

  constructor({ message, status = 500, code = 'INTERNAL_ERROR', details = null }: ErrorWithMessage) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// Helper function to create an unauthorized error
export const createUnauthorizedError = (message = 'Unauthorized') => {
  return new ApiError({
    message,
    status: 401,
    code: 'UNAUTHORIZED'
  });
};

// Helper function to create a forbidden error
export const createForbiddenError = (message = 'Forbidden') => {
  return new ApiError({
    message,
    status: 403,
    code: 'FORBIDDEN'
  });
};

// Helper function to create a validation error
export const createValidationError = (message = 'Validation Error', details: any = null) => {
  return new ApiError({
    message,
    status: 400,
    code: 'VALIDATION_ERROR',
    details
  });
};

// Helper function to create a not found error
export const createNotFoundError = (message = 'Not Found') => {
  return new ApiError({
    message,
    status: 404,
    code: 'NOT_FOUND'
  });
};

export const handleApiError = (error: unknown) => {
  logger.error('API Error', { error });

  if (error instanceof ApiError) {
    return NextResponse.json(
      {
        success: false,
        error: {
          message: error.message,
          code: error.code,
          details: error.details,
        },
      },
      { status: error.status || 500 }
    );
  }

  if (error instanceof Error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          message: error.message || 'An unexpected error occurred',
          code: 'UNEXPECTED_ERROR',
        },
      },
      { status: 500 }
    );
  }

  return NextResponse.json(
    {
      success: false,
      error: {
        message: 'An unknown error occurred',
        code: 'UNKNOWN_ERROR',
      },
    },
    { status: 500 }
  );
};

export const handleClientError = (error: unknown) => {
  if (error instanceof Error) {
    return {
      success: false as const,
      error: {
        message: error.message || 'An error occurred',
        code: 'CLIENT_ERROR',
      },
    };
  }

  return {
    success: false as const,
    error: {
      message: 'An unknown error occurred',
      code: 'UNKNOWN_ERROR',
    },
  };
};
