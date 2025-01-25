import React, { useState } from "react";
import axios from "axios";

const AudioUpload = ({ onTranscription }) => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {//handle file selection
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {//send it to backend for transcription
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/talk", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const transcribedText = res.data.transcription || "Transcription not available.";
      onTranscription(transcribedText); // Call the callback with the transcription result
    } catch (error) {
      console.error("Error uploading file:", error);
      onTranscription("Error transcribing audio."); // Notify the chat about the error
    }
  };

  return (
    <div>
      <h2>Upload Audio</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload Audio</button>
    </div>
  );
};

export default AudioUpload;

