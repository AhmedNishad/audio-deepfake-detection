'use client'
import Image from "next/image";
import FileUploadProgressBar from "./shared/loader";
import Link from "next/link";
import { useEffect, useState } from "react";
import { MongoId } from "./types";
import { apiUrl } from "@/conts";
import AttributeRecording from "./components/attribute";

export interface AudioPredictionResponse {
  _id: MongoId;
  isDeepfake: boolean;
}

export const capitalizeEachWord = (input: string) => {
  const words = input.split(" ");

  const capitalizedWords = words.map(word => {
    return word.charAt(0).toUpperCase() + word.slice(1);
  });

  return capitalizedWords.join(" ");
}

function getRandomNumber(limit: number) {
  // Generate a random decimal between 0 (inclusive) and 1 (exclusive)
  const randomDecimal = Math.random();
  
  // Scale the random decimal to a number between 1 and 20
  const randomNumber = Math.floor(randomDecimal * limit) + 1;
  
  return randomNumber;
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadPercentage, setUploadPercentage] = useState(0);
  const [completedUploadResponse, setCompletedUploadResponse] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [celebrities, setCelebrities] = useState([]);

  useEffect(() => {
    if (searchTerm && searchTerm !== "") {
      (async () => {
        const response = await fetch(`https://api.api-ninjas.com/v1/celebrity?name=${searchTerm}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'X-Api-Key': ''
          },
        });
        const data = await response.json();
        console.log(data);
        const celebrityNames = data.sort((d: any) => d.net_worth).slice(0, 5).map((d: any) => capitalizeEachWord(d.name))
        console.log(celebrityNames);
        setCelebrities(celebrityNames);
      })();
    }
  }, [searchTerm])

  const handleFileChange = (event: any) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('Please select a file.');
      return;
    }

    if (!selectedFile.name.endsWith('.wav')) {
      alert('Please select a .wav file.');
      return;
    }

    let localUploadPercentage = 3;
    setUploadPercentage(localUploadPercentage); // todo - simulate increasing
    setInterval(() => {
      const rand = getRandomNumber(99 - localUploadPercentage);
      console.log("Upload percentage", localUploadPercentage, "random", rand)
      let newPercentage = localUploadPercentage + rand;
      if(newPercentage < 100){
        setUploadPercentage(newPercentage);
      }
    }, 1000);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${apiUrl}/predict`, {
        method: 'POST',
        body: formData,
      });
      console.log(response);
      if (response.ok) {
        setUploadPercentage(100);
        const responseBody = await response.json();
        console.log('Response body:', responseBody);
        setCompletedUploadResponse(responseBody);
        // Handle any further actions upon successful upload
        alert('File uploaded successfully!');
      } else {
        alert('Failed to upload file.');
        setUploadPercentage(0)
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file. Please try again later.');
    }
  };

  return (
    <div className="container">
      {uploadPercentage === 0 ? (
        <>
        <h1 className="text-3xl font-bold mb-8">Detect Audio Recordings!</h1>
        <form action="#" method="post" encType="multipart/form-data" className="upload-form mb-8">
          <label htmlFor="file-upload" className="custom-file-upload bg-black text-black py-2 px-4 rounded-md cursor-pointer">
            <input type="file" id="file-upload" name="file-upload" onChange={handleFileChange} className="hidden" />
            {selectedFile ? selectedFile.name : "Choose recording (.wav only)"}
          </label>
          {selectedFile && (
            <button onClick={handleUpload} type="button" className="bg-black text-white py-2 px-4 rounded-md ml-4">
              Upload
            </button>
          )}
        </form>
        <div className="search-container relative">
          <input
            type="text"
            placeholder="Search..."
            value={searchTerm}
            onInput={(e: any) => setSearchTerm(e.target.value)}
            className="border border-gray-300 rounded-l-md py-2 px-4 mb-4 mr-4"
          />
          {celebrities.length > 0 && (
            <ul style={{top: '40px'}} className="absolute left-0 z-10 bg-white border border-gray-300 rounded-b-md shadow-md mt-2 w-full">
              {celebrities.map((celebrity, index) => (
                <li
                  key={index}
                  onClick={() => { setSearchTerm(celebrity); setCelebrities([]) }}
                  className="py-2 px-4 cursor-pointer hover:bg-gray-100"
                >
                  {celebrity}
                </li>
              ))}
            </ul>
          )}
          <Link className="bg-black text-white py-2 px-4 rounded-r-md hover:bg-blue-600 flex items-center" href={`search?text=${searchTerm}`}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.928 13.52A4.5 4.5 0 1 1 13.5 9a4.5 4.5 0 0 1-3.572 4.42l-1.758 1.758a1 1 0 0 1-1.414-1.414l1.758-1.758zm.778-.778a3.5 3.5 0 1 0-4.95-4.95 3.5 3.5 0 0 0 4.95 4.95z" clipRule="evenodd" />
            </svg>
            Search
          </Link>
        </div>
      </>
      ) : !completedUploadResponse ? (
        <>
          <FileUploadProgressBar percentage={uploadPercentage} />
        </>
      ) : (
        <>
          <AttributeRecording result={completedUploadResponse} />
        </>
      )}
    </div>

  );
}
