'use client';

import { useEffect } from 'react';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log the error to console or error reporting service
        console.error('Application error:', error);
    }, [error]);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-8 bg-gray-50">
            <div className="max-w-lg w-full bg-white border border-gray-200 rounded-lg shadow-lg p-8">
                <div className="flex items-center mb-6">
                    <div className="flex-shrink-0">
                        <svg
                            className="h-12 w-12 text-red-500"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            />
                        </svg>
                    </div>
                    <div className="ml-4">
                        <h2 className="text-2xl font-bold text-gray-900">
                            Something went wrong!
                        </h2>
                    </div>
                </div>

                <div className="mb-6">
                    <p className="text-gray-700 mb-4">
                        We encountered an unexpected error. This has been logged and we'll look into it.
                    </p>

                    {error.digest && (
                        <div className="bg-gray-100 rounded p-3 mb-4">
                            <p className="text-sm text-gray-600">
                                <span className="font-semibold">Error ID:</span> {error.digest}
                            </p>
                        </div>
                    )}

                    <details className="mb-4">
                        <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                            Technical details
                        </summary>
                        <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono text-gray-700 overflow-auto max-h-40">
                            {error.message}
                        </div>
                    </details>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={reset}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded transition-colors"
                    >
                        Try Again
                    </button>
                    <a
                        href="/"
                        className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded text-center transition-colors"
                    >
                        Go Home
                    </a>
                </div>
            </div>
        </div>
    );
}
