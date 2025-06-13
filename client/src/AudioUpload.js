// AudioUpload.js
import React, { useState, useRef } from 'react';
import './AudioUpload.css';

const AudioUpload = ({ onTranscription, isDisabled }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Check file type
    if (!file.type.startsWith('audio/')) {
      setErrorMessage("Please upload an audio file.");
      setTimeout(() => setErrorMessage(""), 3000);
      return;
    }
    
    setIsUploading(true);
    setUploadProgress(0);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const newProgress = prev + 10;
          return newProgress < 90 ? newProgress : prev;
        });
      }, 300);
      
      const response = await fetch('http://localhost:8000/talk', {
        method: 'POST',
        body: formData,
      });
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (!response.ok) {
        throw new Error('Error transcribing audio.');
      }
      
      const data = await response.json();
      
      if (data.transcription) {
        onTranscription(data.transcription);
      } else {
        throw new Error('No transcription received.');
      }
    } catch (error) {
      console.error('Error:', error);
      setErrorMessage("Failed to process audio. Please try again.");
      setTimeout(() => setErrorMessage(""), 3000);
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 500);
    }
  };

  // Start recording
  const startRecording = async () => {
    try {
      setErrorMessage("");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        
        // Send the recorded audio to the server
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        
        setIsUploading(true);
        setUploadProgress(0);
        
        try {
          // Simulate progress
          const progressInterval = setInterval(() => {
            setUploadProgress(prev => {
              const newProgress = prev + 10;
              return newProgress < 90 ? newProgress : prev;
            });
          }, 200);
          
          const response = await fetch('http://localhost:8000/talk', {
            method: 'POST',
            body: formData,
          });
          
          clearInterval(progressInterval);
          setUploadProgress(100);
          
          if (!response.ok) {
            throw new Error('Error transcribing audio.');
          }
          
          const data = await response.json();
          
          if (data.transcription) {
            onTranscription(data.transcription);
          } else {
            throw new Error('No transcription received.');
          }
        } catch (error) {
          console.error('Error:', error);
          setErrorMessage("Failed to process recording. Please try again.");
          setTimeout(() => setErrorMessage(""), 3000);
        } finally {
          setTimeout(() => {
            setIsUploading(false);
            setUploadProgress(0);
          }, 500);
        }
        
        // Stop all tracks from the stream
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      
      // Start timer
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setErrorMessage("Could not access microphone. Please check permissions.");
      setTimeout(() => setErrorMessage(""), 3000);
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  // Format time for display
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };
  
  return (
    <div className="audio-upload-container">
      {errorMessage && <div className="error-message">{errorMessage}</div>}
      
      {isUploading ? (
        <div className="upload-progress">
          <div className="progress-bar">
            <div className="progress" style={{ width: `${uploadProgress}%` }}></div>
          </div>
          <span>Processing audio... {uploadProgress}%</span>
        </div>
      ) : (
        <div className="audio-controls">
          {isRecording ? (
            <div className="recording-controls">
              <div className="recording-indicator">
                <span className="recording-dot"></span>
                Recording... {formatTime(recordingTime)}
              </div>
              <button 
                className="stop-button" 
                onClick={stopRecording}
                disabled={isDisabled}
              >
                Stop
              </button>
            </div>
          ) : (
            <div className="input-buttons">
              <label className="upload-button">
                <input 
                  type="file" 
                  accept="audio/*" 
                  onChange={handleFileUpload} 
                  disabled={isDisabled}
                />
                Upload Audio
              </label>
              <button 
                className="record-button" 
                onClick={startRecording}
                disabled={isDisabled}
              >
                Record
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AudioUpload;
