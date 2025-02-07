import React, { useState } from "react";
import AudioUpload from "./AudioUpload";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([
    { type: "bot", text: "Upload your audio below." },
  ]);
  const [input, setInput] = useState("");

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim()) {
      setMessages([...messages, { type: "user", text: input }]);
      setInput("");
      setTimeout(() => {
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: "bot", text: "Your message has been received." },
        ]);
      }, 1000);
    }
  };

  const handleTranscription = (transcribedText) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "user", text: transcribedText },
    ]);
    setTimeout(() => {
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "bot", text: "Thank you for uploading. What else can I help with?" },
      ]);
    }, 1000);
  };

  return (
    <div className="App">
      <div className="messages">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={msg.type === "bot" ? "bot-message" : "user-message"}
          >
            {msg.text}
          </div>
        ))}
      </div>
      <div className="input">
        <form onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Type your message here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" disabled={!input.trim()}>Send</button>
        </form>
      </div>
      <AudioUpload onTranscription={handleTranscription} />
    </div>
  );
}

export default App;
