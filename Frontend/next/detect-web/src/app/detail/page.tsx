import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { DetectionResult } from '../types';

const DetailPage = () => {
    const router = useRouter();
    const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
    const { id } = router.query;

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`YOUR_API_ENDPOINT/${id}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch detection result');
                }
                const data = await response.json();
                setDetectionResult(data);
            } catch (error) {
                console.error('Error fetching detection result:', error);
            }
        };

        if (id) {
            fetchData();
        }
    }, [id]);

    return (
        <div>
            {detectionResult ? (
                <div>
                    <h1>{detectionResult.publicFigure}</h1>
                    <p>{detectionResult.transcript}</p>
                    {/* Add more details as needed */}
                </div>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
};

export default DetailPage;