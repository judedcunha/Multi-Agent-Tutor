import React, { useState, useEffect, useRef, useCallback } from 'react';
import './TutoringStream.css';

const TutoringStream = ({ serverUrl = 'ws://localhost:8000/ws/learn' }) => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [currentTopic, setCurrentTopic] = useState('');
  const [studentProfile, setStudentProfile] = useState({
    name: 'Student',
    email: '',
    level: 'beginner',
    learning_style: 'mixed'
  });
  const [progress, setProgress] = useState({});
  const [content, setContent] = useState({
    lessonSections: [],
    practiceProblems: [],
    resources: [],
    assessment: null
  });
  const [inputQuestion, setInputQuestion] = useState('');
  const [isTeaching, setIsTeaching] = useState(false);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    try {
      const ws = new WebSocket(serverUrl);
      
      ws.onopen = () => {
        setConnectionStatus('connected');
        console.log('Connected to tutoring system');
        
        // Send initialization message
        ws.send(JSON.stringify({
          type: 'initialize',
          student: studentProfile
        }));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };
      
      ws.onclose = () => {
        setConnectionStatus('disconnected');
        console.log('Disconnected from tutoring system');
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          setConnectionStatus('reconnecting');
          connect();
        }, 3000);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect:', error);
      setConnectionStatus('error');
    }
  }, [serverUrl, studentProfile]);
  
  // Handle incoming messages
  const handleMessage = (data) => {
    console.log('Received:', data);
    
    switch (data.type) {
      case 'connection':
        setSessionId(data.session_id);
        break;
        
      case 'session_created':
        setSessionId(data.session_id);
        addMessage('System', `Session created: ${data.session_id}`);
        break;
        
      case 'progress':
        setProgress(prev => ({
          ...prev,
          [data.agent]: {
            progress: data.progress,
            message: data.details.message,
            status: data.details.status
          }
        }));
        break;
        
      case 'content':
        handleContentMessage(data.content_type, data.content);
        break;
        
      case 'complete':
        setIsTeaching(false);
        addMessage('System', 'Teaching session complete!');
        console.log('Session summary:', data.summary);
        break;
        
      case 'error':
        addMessage('Error', data.error, 'error');
        break;
        
      case 'pong':
        // Heartbeat response
        break;
        
      default:
        console.log('Unknown message type:', data.type);
    }
  };
  
  // Handle different content types
  const handleContentMessage = (contentType, contentData) => {
    switch (contentType) {
      case 'lesson_section':
        setContent(prev => ({
          ...prev,
          lessonSections: [...prev.lessonSections, contentData]
        }));
        break;
        
      case 'practice_problem':
        setContent(prev => ({
          ...prev,
          practiceProblems: [...prev.practiceProblems, contentData]
        }));
        break;
        
      case 'resources':
        setContent(prev => ({
          ...prev,
          resources: contentData
        }));
        break;
        
      case 'assessment':
        setContent(prev => ({
          ...prev,
          assessment: contentData
        }));
        break;
        
      case 'answer':
        addMessage('Tutor', contentData.answer, 'tutor');
        break;
        
      case 'hint':
        addMessage('Hint', contentData.hint, 'hint');
        break;
        
      case 'feedback':
        const feedbackClass = contentData.correct ? 'success' : 'error';
        addMessage('Feedback', contentData.feedback, feedbackClass);
        if (contentData.explanation) {
          addMessage('Explanation', contentData.explanation, 'info');
        }
        break;
        
      case 'thinking':
        addMessage('System', contentData.message, 'thinking');
        break;
        
      default:
        console.log('Unknown content type:', contentType);
    }
  };
  
  // Add message to chat
  const addMessage = (sender, text, type = 'normal') => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      sender,
      text,
      type,
      timestamp: new Date().toISOString()
    }]);
  };
  
  // Start teaching session
  const startTeaching = () => {
    if (!currentTopic || !wsRef.current) return;
    
    setIsTeaching(true);
    setContent({
      lessonSections: [],
      practiceProblems: [],
      resources: [],
      assessment: null
    });
    setProgress({});
    
    wsRef.current.send(JSON.stringify({
      type: 'teach',
      topic: currentTopic,
      level: studentProfile.level
    }));
    
    addMessage('System', `Starting lesson on: ${currentTopic}`);
  };
  
  // Ask a question
  const askQuestion = () => {
    if (!inputQuestion || !wsRef.current) return;
    
    addMessage('You', inputQuestion, 'user');
    
    wsRef.current.send(JSON.stringify({
      type: 'interaction',
      interaction: {
        type: 'ask_question',
        question: inputQuestion
      }
    }));
    
    setInputQuestion('');
  };
  
  // Request hint for a problem
  const requestHint = (problemId) => {
    if (!wsRef.current) return;
    
    wsRef.current.send(JSON.stringify({
      type: 'interaction',
      interaction: {
        type: 'request_hint',
        problem_id: problemId
      }
    }));
  };
  
  // Submit answer to a problem
  const submitAnswer = (problemId, answer) => {
    if (!wsRef.current) return;
    
    wsRef.current.send(JSON.stringify({
      type: 'interaction',
      interaction: {
        type: 'submit_answer',
        problem_id: problemId,
        answer: answer
      }
    }));
  };
  
  // Update student profile
  const updateProfile = (field, value) => {
    setStudentProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  // Adjust difficulty
  const adjustDifficulty = (level) => {
    if (!wsRef.current) return;
    
    updateProfile('level', level);
    
    wsRef.current.send(JSON.stringify({
      type: 'interaction',
      interaction: {
        type: 'adjust_difficulty',
        level: level
      }
    }));
  };
  
  // Initialize connection on mount
  useEffect(() => {
    connect();
    
    // Send heartbeat every 30 seconds
    const heartbeat = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
    
    return () => {
      clearInterval(heartbeat);
      clearTimeout(reconnectTimeoutRef.current);
      
      if (wsRef.current) {
        wsRef.current.send(JSON.stringify({ type: 'disconnect' }));
        wsRef.current.close();
      }
    };
  }, [connect]);
  
  // Auto-scroll messages
  useEffect(() => {
    const messagesContainer = document.getElementById('messages-container');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }, [messages]);
  
  // Calculate overall progress
  const overallProgress = Object.values(progress).reduce((acc, agent) => 
    acc + (agent.progress || 0), 0) / Math.max(Object.keys(progress).length, 1);
  
  return (
    <div className="tutoring-stream">
      {/* Header */}
      <div className="header">
        <h2>AI Tutoring System - Live Session</h2>
        <div className={`connection-status ${connectionStatus}`}>
          {connectionStatus === 'connected' && 'Connected'}
          {connectionStatus === 'disconnected' && 'Disconnected'}
          {connectionStatus === 'reconnecting' && 'Reconnecting...'}
          {connectionStatus === 'error' && 'Error'}
        </div>
      </div>
      
      {/* Student Profile */}
      <div className="profile-section">
        <h3>Student Profile</h3>
        <input
          type="text"
          placeholder="Name"
          value={studentProfile.name}
          onChange={(e) => updateProfile('name', e.target.value)}
          disabled={isTeaching}
        />
        <input
          type="email"
          placeholder="Email (optional)"
          value={studentProfile.email}
          onChange={(e) => updateProfile('email', e.target.value)}
          disabled={isTeaching}
        />
        <select
          value={studentProfile.level}
          onChange={(e) => updateProfile('level', e.target.value)}
          disabled={isTeaching}
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
        <select
          value={studentProfile.learning_style}
          onChange={(e) => updateProfile('learning_style', e.target.value)}
          disabled={isTeaching}
        >
          <option value="visual">Visual</option>
          <option value="auditory">Auditory</option>
          <option value="kinesthetic">Kinesthetic</option>
          <option value="mixed">Mixed</option>
        </select>
      </div>
      
      {/* Teaching Controls */}
      <div className="teaching-controls">
        <input
          type="text"
          placeholder="Enter topic to learn..."
          value={currentTopic}
          onChange={(e) => setCurrentTopic(e.target.value)}
          disabled={isTeaching}
        />
        <button
          onClick={startTeaching}
          disabled={!currentTopic || isTeaching || connectionStatus !== 'connected'}
        >
          {isTeaching ? 'Teaching in Progress...' : 'Start Learning'}
        </button>
      </div>
      
      {/* Progress Bar */}
      {isTeaching && (
        <div className="progress-section">
          <div className="overall-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${overallProgress * 100}%` }}
              />
            </div>
            <span>{Math.round(overallProgress * 100)}% Complete</span>
          </div>
          
          <div className="agent-progress">
            {Object.entries(progress).map(([agent, data]) => (
              <div key={agent} className={`agent-status ${data.status}`}>
                <span className="agent-name">{agent.replace(/_/g, ' ')}</span>
                <span className="agent-message">{data.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Content Display */}
      <div className="content-section">
        {/* Lesson Sections */}
        {content.lessonSections.length > 0 && (
          <div className="lesson-content">
            <h3>Lesson Content</h3>
            {content.lessonSections.map((section, idx) => (
              <div key={idx} className="lesson-section">
                <h4>{section.title}</h4>
                {Array.isArray(section.content) ? (
                  <ul>
                    {section.content.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p>{section.content}</p>
                )}
              </div>
            ))}
          </div>
        )}
        
        {/* Practice Problems */}
        {content.practiceProblems.length > 0 && (
          <div className="practice-content">
            <h3>Practice Problems</h3>
            {content.practiceProblems.map((problem) => (
              <div key={problem.id} className={`practice-problem ${problem.difficulty}`}>
                <div className="problem-header">
                  <span className="problem-id">Problem {problem.id}</span>
                  <span className="problem-difficulty">{problem.difficulty}</span>
                </div>
                <p className="problem-question">{problem.question}</p>
                <div className="problem-actions">
                  <button onClick={() => requestHint(problem.id)}>Get Hint</button>
                  <button onClick={() => {
                    const answer = prompt('Enter your answer:');
                    if (answer) submitAnswer(problem.id, answer);
                  }}>Submit Answer</button>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Resources */}
        {content.resources && Object.keys(content.resources).length > 0 && (
          <div className="resources-content">
            <h3>Additional Resources</h3>
            {Object.entries(content.resources).map(([type, items]) => (
              <div key={type} className="resource-type">
                <h4>{type.charAt(0).toUpperCase() + type.slice(1)}</h4>
                <ul>
                  {items.map((item, idx) => (
                    <li key={idx}>
                      <a href={item.url} target="_blank" rel="noopener noreferrer">
                        {item.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Chat Interface */}
      <div className="chat-section">
        <h3>Chat</h3>
        <div id="messages-container" className="messages-container">
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.type}`}>
              <span className="message-sender">{msg.sender}:</span>
              <span className="message-text">{msg.text}</span>
            </div>
          ))}
        </div>
        <div className="chat-input">
          <input
            type="text"
            placeholder="Ask a question..."
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
            disabled={connectionStatus !== 'connected'}
          />
          <button
            onClick={askQuestion}
            disabled={!inputQuestion || connectionStatus !== 'connected'}
          >
            Send
          </button>
        </div>
      </div>
      
      {/* Difficulty Adjustment */}
      <div className="difficulty-controls">
        <span>Adjust Difficulty:</span>
        <button onClick={() => adjustDifficulty('beginner')}>Beginner</button>
        <button onClick={() => adjustDifficulty('intermediate')}>Intermediate</button>
        <button onClick={() => adjustDifficulty('advanced')}>Advanced</button>
      </div>
    </div>
  );
};

export default TutoringStream;
