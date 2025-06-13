// App.js
import React, { useState, useEffect, useRef } from "react";
import AudioUpload from "./AudioUpload";
import './App.css';

function App() {
  // State to hold the list of messages
  const [messages, setMessages] = useState([
    { type: "bot", text: "Upload your audio below or type a message to chat.  Or write /start to start the interview" },
  ]);
  const [input, setInput] = useState(""); // user input field
  const [isLoading, setIsLoading] = useState(false); // loading state
  const messagesEndRef = useRef(null);

  // Auto-scroll to the bottom of messages when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle text input submission
  const handleSend = async (e) => {
    e.preventDefault();
    if (input.trim()) {
      setMessages([...messages, { type: "user", text: input }]);
      setInput("");
      setIsLoading(true);
      
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
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: "bot", text: "Sorry, there was an error processing your request." },
        ]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  // Handle audio transcription submission
  const handleTranscription = async (transcribedText) => {
    if (!transcribedText.trim()) return;
    
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "user", text: transcribedText }, // Show user message
    ]);
    
    setIsLoading(true);
    
    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: transcribedText }),
      });
      
      if (!response.ok) {
        throw new Error("Error sending transcription.");
      }
      
      const data = await response.json();
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "bot", text: data.bot_response },
      ]);
    } catch (error) {
      console.error("Error sending transcription:", error);
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "bot", text: "Sorry, there was an error processing your audio." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="left-section">
        <h2 className="title">ChatbotAI</h2>
        <div className="app-info">
          <p>Welcome to ChatbotAI, your voice-enabled assistant.</p>
          <p>You can:</p>
          <ul>
            <li>Type your messages in the chat</li>
            <li>Upload audio files</li>
            <li>Record your voice directly</li>
          </ul>
        </div>
      </div>
      
      {/* Vertical Divider */}
      <div className="divider"></div>
      
      {/* Right Section with Chatbox */}
      <div className="right-section">
        <div className="chatbox">
          <div className="messages-container">
            <div className="messages">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={msg.type === "bot" ? "bot-message" : "user-message"}
                >
                  <span className="message-prefix">
                    {msg.type === "bot" ? "🤖 Bot: " : "👤 You: "}
                  </span>
                  {msg.text}
                </div>
              ))}
              {isLoading && (
                <div className="bot-message loading">
                  <span className="loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                  </span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          <div className="input-container">
            <form onSubmit={handleSend} className="input-form">
              <input
                type="text"
                placeholder="Type your message here..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isLoading}
                className="text-input"
              />
              <button type="submit" disabled={isLoading || !input.trim()} className="send-button">
                {isLoading ? "..." : "Send"}
              </button>
            </form>
            <AudioUpload onTranscription={handleTranscription} isDisabled={isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

//uvicorn main:app --reload  (command to run BackEnd)
//npm start  (command to run FrontEnd)
// you need a two terminal, first terminal to run backend and second one to run FrontEnd
