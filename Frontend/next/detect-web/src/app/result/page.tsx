import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { DetectionResponse, } from '../types';
import Link from 'next/link';

const ResultPage = () => {
    const router = useRouter();
    const [detectionResult, setDetectionResult] = useState<DetectionResponse | null>(null);
    const [isTaggging, setIsTagging] = useState(false);
    const [publicFigure, setPublicFigure] = useState("");
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
            {detectionResult ? detectionResult.isDeepfake ? (
                <div>
                    <p>This recording IS a deepfake</p>
                    <p>If you know the person in question who uttered this, help us tag it so others can be protected</p>
                    {!isTaggging ? <><button onClick={() => setIsTagging(true)}>Tag</button></> : <>
                        <input type='text' onChange={(e: any) => setPublicFigure(e.target.value)} />
                    </>}

                </div>
            ) :
                <>
                    <p>This recording is bonafide</p>
                    <Link href={'../'}>Detect another</Link>
                </>
                : (
                    <p>Loading...</p>
                )}
        </div>
    );
};

export default ResultPage;