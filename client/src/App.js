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

  const handleSend = async (e) => {
    e.preventDefault();
    if (input.trim()) {
      setMessages([...messages, { type: "user", text: input }]);
      setInput("");
  
      try {
        const response = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: input }),
        });
  
        if (!response.ok) {
          throw new Error("Error fetching response.");
        }
  
        const data = await response.json();
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: "bot", text: data.bot_response },
        ]);
      } catch (error) {
        console.error("Error:", error);
      }
    }
  };
  

  const handleTranscription = async (transcribedText) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "user", text: transcribedText }, // Show user message
    ]);
  
    try {
      const response = await fetch("http://localhost:8000/chat", { // New endpoint for text-based chat
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: transcribedText }), // Send text instead of a file
      });
  
      if (!response.ok) {
        throw new Error("Error sending transcription.");
      }
  
      const data = await response.json();
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "bot", text: data.bot_response }, // Show bot's response
      ]);
    } catch (error) {
      console.error("Error sending transcription:", error);
    }
  };
  const handleClearChat = async() => {
    try{ 
      const response = await fetch("http://localhost:8000/clear", {method: "Get"});

      if(response.ok) {
        setMessages([{type: "bot", text: "Chat has been cleared. Type /start to start an interview again!"}])
      }else {
        console.error("Failed to clear chat");
      }
    }catch (error){
      console.error("Error clearing chat:", error);
    }
  };

  return (
    <div className="container">
      <div className="left-section">
        <h2 className="title">ChatbotAI</h2>
        <button type="button" className="clear-chat" onClick={handleClearChat} >Clear Chat</button>
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


//uvicorn main:app --reload  (command to run BackEnd)
//npm start  (command to run FrontEnd)
// you need a two terminal, first terminal to run backend and second one to run FrontEnd