'use client'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react';
import { DetectionResult } from '../types';
import { apiUrl } from '@/conts';
import AudioPlayer from '../components/audioPlayer';

const DetailPage = () => {
    const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
    const searchParams = useSearchParams()
    const id = searchParams.get('id');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`${apiUrl}/detail?id=${id}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch detection result');
                }
                const data = await response.json();
                console.log(data);
                setDetectionResult(data[0]);
            } catch (error) {
                console.error('Error fetching detection result:', error);
            }
        };

        if (id) {
            fetchData();
        }
    }, [id]);

    const date = detectionResult?.createdOn?.$date ? new Date(detectionResult.createdOn?.$date) : null;

    return (
        <div className="container flex justify-center">
            {detectionResult ? (
                <div className="border border-gray-300 rounded-md p-4">
                    <h1 className="text-2xl font-bold mb-4">{detectionResult.publicFigure}</h1>
                    <div className="flex justify-center mb-4"> {/* Horizontally center align the AudioPlayer */}
                        <AudioPlayer url={`${apiUrl}/stream-audio/?fileName=${detectionResult.fileName}`} />
                    </div>
                    <p className="mb-2 relative bg-gray-100 p-4 border border-gray-300 rounded-md">
                        <span className="text-gray-600 absolute top-0 left-0 transform -translate-x-2/3 -translate-y-2/3 text-8xl opacity-10">
                            &ldquo;
                        </span>
                        {detectionResult.transcript}
                        <span className="text-gray-600 absolute bottom-0 right-0 transform translate-x-2/3 translate-y-2/3 text-8xl opacity-10">
                            &rdquo;
                        </span>
                    </p>
                    {date && (
                        <p className="mt-4">Detected on {date.toLocaleDateString("en-US", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
                    )}
                    {/* Add more details as needed */}
                </div>
            ) : (
                <p>Loading...</p>
            )}
        </div>

    );
};

export default DetailPage;