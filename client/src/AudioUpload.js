import React, { useState } from "react";
import axios from "axios";

const AudioUpload = ({ onTranscription }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null); // Clear previous errors
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/talk", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const transcribedText = res.data.transcription || "Transcription not available.";
      onTranscription(transcribedText);
    } catch (err) {
      console.error("Error uploading file:", err);
      setError("Failed to upload audio. Please try again.");
      onTranscription("Error transcribing audio.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="audio-upload">
      <h2>Upload Audio</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? "Uploading..." : "Upload Audio"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
};

export default AudioUpload;
