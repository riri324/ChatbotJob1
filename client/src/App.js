import React, { useState } from "react";
import AudioUpload from "./AudioUpload";
import './App.css';

function App() {// to hold the list of messages
  const [messages, setMessages] = useState([
    { type: "bot", text: "Upload your audio below." },
  ]);
  const [input, setInput] = useState(""); // user input field

  const handleSend = (e) => {//handle the send button for user messages
    e.preventDefault();
    if (input.trim()) {
      // user message
      setMessages([...messages, { type: "user", text: input }]);
      setInput("");
      // bot response
      setTimeout(() => {
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: "bot", text: "Upload your audio below." },
        ]);
      }, 1000);
    }
  };

  const handleTranscription = (transcribedText) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "user", text: transcribedText }, // Add transcribed text as a user message
    ]);

    setTimeout(() => {
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "bot", text: "Upload the video below." },
      ]);
    }, 1000);
  };

  return (
    <div className="App">
      <h2>ChatbotAI</h2>
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
          <button type="submit">Send</button>
        </form>
      </div>
      <AudioUpload onTranscription={handleTranscription} />
    </div>
  );
}

export default App;
//uvicorn main:app --reload  (command to run BackEnd)
//npm start  (command to run FrontEnd)
// you need a two terminal, first terminal to run backend and second one to run FrontEnd