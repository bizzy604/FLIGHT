"use client";

import React from 'react';

interface LoadingState {
    isLoading: boolean;
    error?: any;
    data?: any;
}

interface LoadingContextType {
    loadingState: LoadingState;
    setLoadingState: (state: LoadingState) => void;
}

const loadingContext = React.createContext<LoadingContextType | undefined>(undefined);

export const LoadingProvider = ({ children }: { children: React.ReactNode }) => {
    const [loadingState, setLoadingState] = React.useState<LoadingState>({
        isLoading: false,
        error: undefined,
        data: undefined,
    });

    return React.createElement(
        loadingContext.Provider,
        { value: { loadingState, setLoadingState } },
        children
    );
};

export const useLoading = (): LoadingContextType => {
    const context = React.useContext(loadingContext);
    if (context === undefined) {
        throw new Error('useLoading must be used within a LoadingProvider');
    }
    return context;
};
