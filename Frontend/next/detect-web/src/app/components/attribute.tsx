'use client'
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { DetectionResponse, } from '../types';
import Link from 'next/link';
import { apiUrl } from '@/conts';
import { AudioPredictionResponse, capitalizeEachWord } from '../page';

interface Props {
    result: AudioPredictionResponse;
}
const AttributeRecording = ({ result }: Props) => {
    const router = useRouter();
    const [isTaggging, setIsTagging] = useState(false);
    const [publicFigure, setPublicFigure] = useState("");
    const [celebrities, setCelebrities] = useState([]);

    useEffect(() => {
        if (publicFigure && publicFigure !== "") {
            (async () => {
                const response = await fetch(`https://api.api-ninjas.com/v1/celebrity?name=${publicFigure}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Api-Key': 'ZzzuCKOo/zf/F3GMXgXz1w==UNVkljCUHfJ48ZdU'
                    },
                });
                const data = await response.json();
                console.log(data);
                const celebrityNames = data.sort((d: any) => d.net_worth).slice(0, 5).map((d: any) => capitalizeEachWord(d.name))
                console.log(celebrityNames);
                setCelebrities(celebrityNames);
            })();
        }
    }, [publicFigure])

    const handleTag = async () => {
        const body = {
            id: result._id.$oid,
            publicFigure
        }

        const response = await fetch(`${apiUrl}/attribute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body),
        });

        if (response.ok) {
            alert('Recording tagged successfully!');
            router.push(`detail?id=${result._id.$oid}`);
        } else {
            alert('Failed to tag recording.');
        }
    }

    return (
        <div>
            {result && result.isDeepfake ? (
                <div className="bg-red-100 p-6 rounded-lg shadow-md">
                    <p className="text-xl font-semibold text-red-900 mb-4">This recording is a deepfake</p>
                    <p className="text-lg text-red-800 mb-4">If you know the person in question who uttered this, help us tag it so others can be protected</p>
                    {!isTaggging ? (
                        <button onClick={() => setIsTagging(true)} className="bg-red-500 text-white py-2 px-4 rounded-md hover:bg-red-600">
                            Tag
                        </button>
                    ) : (
                        <>
                            <div className="search-container relative">
                                <input
                                    type="text"
                                    value={publicFigure}
                                    onChange={(e: any) => setPublicFigure(e.target.value)}
                                    placeholder="Enter the person's name"
                                    className="border border-gray-300 rounded-md py-2 px-4 mb-4"
                                />
                                {celebrities.length > 0 && (
                                    <ul style={{ top: '40px' }} className="absolute left-0 z-10 bg-white border border-gray-300 rounded-b-md shadow-md mt-2 w-full">
                                        {celebrities.map((celebrity, index) => (
                                            <li
                                                key={index}
                                                onClick={() => { setPublicFigure(celebrity); setCelebrities([]) }}
                                                className="py-2 px-4 cursor-pointer hover:bg-gray-100"
                                            >
                                                {celebrity}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                                {publicFigure !== "" && (
                                <button onClick={handleTag} type="button" className="bg-red-500 text-white py-2 px-4 rounded-md hover:bg-red-600">
                                    Tag
                                </button>
                            )}
                            </div>
                        </>
                    )}
                </div>

            ) :
                <div className="bg-green-100 p-6 rounded-lg shadow-md">
                    <p className="text-xl font-semibold text-green-900 mb-4">This recording is genuine</p>
                    <button onClick={() => window.location.reload()} className="bg-green-500 text-white py-2 px-4 rounded-md hover:bg-green-600">
                        Detect another
                    </button>
                </div>
            }
        </div>
    );
};

export default AttributeRecording;