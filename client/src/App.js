import React, { useState } from "react";
import AudioUpload from "./AudioUpload";
import './App.css';
import { useEffect, useRef } from "react";


function App() {// to hold the list of messages
  const [messages, setMessages] = useState([
    { type: "bot", text: "Upload your audio below." },
  ]);
  const [input, setInput] = useState(""); // user input field

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
    <div className="container">
      <div className="left-section">
        <h2 className="title">ChatbotAI</h2>
      </div>
  
      {/* Vertical Divider */}
      <div className="divider"></div>
  
      {/* Right Section with Chatbox */}
      <div className="right-section">
        <div className="chatbox">
          <div className="messages">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={msg.type === "bot" ? "bot-message" : "user-message"}
              >
                {msg.text}
              </div>
            ))}
            <div ref={messagesEndRef} />
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
      </div>
    </div>
  );
  
  
}

export default App;

//npm i --save @fortawesome/free-solid-svg-icons
//npm i --save @fortawesome/free-regular-svg-icons
//npm i --save @fortawesome/free-brands-svg-icons
//npm i --save @fortawesome/react-fontawesome@latest
//run this first 

//uvicorn main:app --reload  (command to run BackEnd)
//npm start  (command to run FrontEnd)
// you need a two terminal, first terminal to run backend and second one to run FrontEnd