'use client'
import Image from "next/image";
import FileUploadProgressBar from "./shared/loader";
import Link from "next/link";
import { useState } from "react";

export default function Home() {
  const [fileToUpload, setFileToUpload] = useState(null);
  const [isUploadInProgress, setIsUploadInProgress] = useState(false);

  const handleUpload = (e: any) => {
    setIsUploadInProgress(true);
  }

  return (
    <div className="container">
      {(!isUploadInProgress ? (<>
      <h1>Detect Audio Recordings!</h1>
      <form action="#" method="post" encType="multipart/form-data" className="upload-form">
        <label htmlFor="file-upload" className="custom-file-upload">
          <input type="file" id="file-upload" name="file-upload" />
          Choose recording
        </label>
        <button onClick={handleUpload} type="button">Upload</button>
      </form>
      <div className="search-container">
        <input type="text" placeholder="Search..." />
        {/* <button type="button">Search</button> */}
        <Link
          href={'/search'}><p className="hidden md:block">Search</p></Link>
      </div>
      </>) :
      <>
        <FileUploadProgressBar percentage={10} />
      </>
      )}

    </div>
  );
}
