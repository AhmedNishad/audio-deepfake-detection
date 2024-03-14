'use-client'
import React from 'react';
import './FileUploadProgressBar.css'; // Import CSS file for styling

interface Props{
    percentage: number;
}

const FileUploadProgressBar = ({ percentage }: Props) => {
    return (
        <div className="progress-container">
            <div className="progress-bar" style={{ width: `${percentage}%` }}>
                <span className="progress-text">{percentage}%</span>
            </div>
        </div>
    );
};

export default FileUploadProgressBar;