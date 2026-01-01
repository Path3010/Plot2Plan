'use client';

import { useState, useCallback } from 'react';

interface DXFUploaderProps {
  onUploadSuccess: (data: any) => void;
  onUploadError: (error: string) => void;
}

export default function DXFUploader({ onUploadSuccess, onUploadError }: DXFUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const uploadFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.dxf')) {
      onUploadError('Please upload a DXF file');
      return;
    }

    setIsUploading(true);
    setFileName(file.name);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const data = await response.json();
      onUploadSuccess(data);
    } catch (error) {
      onUploadError(error instanceof Error ? error.message : 'Upload failed');
      setFileName(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  };

  return (
    <div
      className={`upload-zone ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".dxf"
        onChange={handleFileSelect}
        className="hidden"
        id="dxf-upload"
        disabled={isUploading}
      />
      
      <div className="upload-icon">
        {isUploading ? (
          <svg style={{ width: 32, height: 32, animation: 'spin 1s linear infinite' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        ) : (
          <svg style={{ width: 32, height: 32, color: 'var(--primary-500)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        )}
      </div>

      <div className="upload-title">
        {isUploading ? `Uploading ${fileName}...` : 'Drop your DXF file here'}
      </div>
      <div className="upload-subtitle">
        or click to browse your files
      </div>

      <label htmlFor="dxf-upload" className="btn btn-primary" style={{ cursor: isUploading ? 'not-allowed' : 'pointer' }}>
        {isUploading ? 'Uploading...' : 'Select DXF File'}
      </label>
    </div>
  );
}
