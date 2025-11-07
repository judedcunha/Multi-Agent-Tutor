import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './AnalyticsDashboard.css';

const AnalyticsDashboard = ({ serverUrl = 'http://localhost:8000' }) => {
  // State management
  const [studentId, setStudentId] = useState('demo_student_001');
  const [timeRange, setTimeRange] = useState('week'); // day, week, month, all
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  
  // Analytics data
  const [dashboardData, setDashboardData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [streaks, setStreaks] = useState(null);
  const [student, setStudent] = useState(null);

  // Fetch dashboard data from API
  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `${serverUrl}/analytics/dashboard/${studentId}?time_range=${timeRange}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setDashboardData(data);
        setAnalytics(data.analytics);
        setStreaks(data.streaks);
        setStudent(data.student);
        setLastUpdated(new Date());
      } else {
        throw new Error('Failed to fetch dashboard data');
      }
      
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err.message);
      
      // Set mock data for development/demo
      setMockData();
      
    } finally {
      setLoading(false);
    }
  }, [studentId, timeRange, serverUrl]);

  // Set mock data for demo/development
  const setMockData = () => {
    // Generate mock progress data for the last 14 days
    const generateProgressData = () => {
      const data = [];
      const now = new Date();
      
      for (let i = 13; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        
        // Generate realistic-looking data with some variation
        const sessions = Math.max(0, Math.floor(Math.random() * 3) + (i % 7 === 0 || i % 7 === 6 ? 0 : 1));
        const timeSpent = sessions > 0 ? Math.floor(Math.random() * 60) + 20 : 0;
        const problems = sessions * Math.floor(Math.random() * 4 + 2);
        
        data.push({
          date: dateStr,
          fullDate: date.toISOString().split('T')[0],
          sessions,
          timeSpent,
          problems,
          score: sessions > 0 ? Math.floor(Math.random() * 20 + 75) : 0
        });
      }
      return data;
    };
    
    // Generate mock topic performance data
    const generateTopicData = () => {
      const topics = [
        { name: 'Python Basics', sessions: 8, score: 92, problems: 24 },
        { name: 'Data Structures', sessions: 6, score: 85, problems: 18 },
        { name: 'Algorithms', sessions: 5, score: 78, problems: 15 },
        { name: 'Web Development', sessions: 3, score: 88, problems: 9 },
        { name: 'Machine Learning', sessions: 2, score: 72, problems: 6 }
      ];
      
      // Sort by score descending
      return topics.sort((a, b) => b.score - a.score);
    };
    
    // Generate mock practice problems data
    const generatePracticeData = () => {
      return [
        { name: 'Correct', value: 63, percentage: 87.5, color: '#10b981' },
        { name: 'Incorrect', value: 7, percentage: 9.7, color: '#ef4444' },
        { name: 'Incomplete', value: 2, percentage: 2.8, color: '#f59e0b' }
      ];
    };
    
    // Generate mock calendar/streak data for last 60 days
    const generateCalendarData = () => {
      const data = [];
      const now = new Date();
      
      for (let i = 59; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        
        // Simulate activity patterns (higher activity on weekdays, lower on weekends)
        const dayOfWeek = date.getDay();
        const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
        
        // Random activity with realistic patterns
        let sessions = 0;
        const random = Math.random();
        
        if (!isWeekend) {
          // Weekday: more likely to have activity
          if (random > 0.2) {
            sessions = Math.floor(Math.random() * 3) + 1;
          }
        } else {
          // Weekend: less activity
          if (random > 0.5) {
            sessions = Math.floor(Math.random() * 2);
          }
        }
        
        data.push({
          date: date.toISOString().split('T')[0],
          displayDate: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          sessions,
          day: date.getDate(),
          month: date.getMonth(),
          year: date.getFullYear(),
          dayOfWeek: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][dayOfWeek]
        });
      }
      
      return data;
    };
    
    const mockData = {
      student: {
        id: studentId,
        name: 'Demo Student',
        level: 'intermediate',
        learning_style: 'visual'
      },
      analytics: {
        total_sessions: 24,
        total_practice_problems: 72,
        average_score: 0.87,
        total_time_minutes: 640,
        topics_studied: 12,
        active_days: 18,
        progress_data: generateProgressData(),
        topic_data: generateTopicData(),
        practice_data: generatePracticeData(),
        calendar_data: generateCalendarData()
      },
      streaks: {
        current_streak: 7,
        longest_streak: 14,
        total_active_days: 18,
        last_active: new Date().toISOString()
      }
    };
    
    setDashboardData(mockData);
    setAnalytics(mockData.analytics);
    setStreaks(mockData.streaks);
    setStudent(mockData.student);
    setLastUpdated(new Date());
  };

  // Fetch data on component mount and when dependencies change
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Auto-refresh every 5 minutes (optional)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 5 * 60 * 1000); // 5 minutes
    
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  // Handle refresh button
  const handleRefresh = () => {
    fetchDashboardData();
  };

  // Handle student ID change
  const handleStudentIdChange = (e) => {
    setStudentId(e.target.value);
  };

  // Handle time range change
  const handleTimeRangeChange = (range) => {
    setTimeRange(range);
  };

  return (
    <div className="analytics-dashboard">
      {/* Header Section */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-title">
            <h1>📊 Learning Analytics Dashboard</h1>
            <p className="header-subtitle">Track your progress and achievements</p>
          </div>
          
          <div className="header-status">
            <div className={`connection-indicator ${error ? 'error' : 'connected'}`}>
              <span className="status-dot"></span>
              {error ? 'Error' : 'Connected'}
            </div>
            {lastUpdated && (
              <div className="last-updated">
                Updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Student Selector and Controls */}
      <div className="control-panel">
        <div className="student-selector">
          <label htmlFor="studentId">Student ID:</label>
          <input
            type="text"
            id="studentId"
            value={studentId}
            onChange={handleStudentIdChange}
            placeholder="Enter student ID..."
            disabled={loading}
          />
          {student && (
            <div className="student-info">
              <span className="student-name">{student.name}</span>
              <span className="student-level">{student.level}</span>
              <span className="student-style">{student.learning_style}</span>
            </div>
          )}
        </div>

        <div className="time-range-selector">
          <label>Time Range:</label>
          <div className="time-range-buttons">
            <button
              className={timeRange === 'day' ? 'active' : ''}
              onClick={() => handleTimeRangeChange('day')}
              disabled={loading}
            >
              Day
            </button>
            <button
              className={timeRange === 'week' ? 'active' : ''}
              onClick={() => handleTimeRangeChange('week')}
              disabled={loading}
            >
              Week
            </button>
            <button
              className={timeRange === 'month' ? 'active' : ''}
              onClick={() => handleTimeRangeChange('month')}
              disabled={loading}
            >
              Month
            </button>
            <button
              className={timeRange === 'all' ? 'active' : ''}
              onClick={() => handleTimeRangeChange('all')}
              disabled={loading}
            >
              All Time
            </button>
          </div>
        </div>

        <button
          className="refresh-button"
          onClick={handleRefresh}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Refreshing...
            </>
          ) : (
            <>
              🔄 Refresh
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span className="error-text">
            Could not connect to analytics server. Showing demo data.
          </span>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Loading analytics data...</p>
        </div>
      )}

      {/* Main Content */}
      {dashboardData && !loading && (
        <div className="dashboard-content">
          {/* Overview Stats Cards */}
          <div className="stats-grid">
            {/* Total Sessions Card */}
            <div className="stat-card">
              <div className="stat-icon sessions-icon">📚</div>
              <div className="stat-content">
                <div className="stat-label">Total Sessions</div>
                <div className="stat-value">
                  {analytics?.total_sessions || 0}
                </div>
                <div className="stat-subtitle">Learning sessions completed</div>
              </div>
            </div>

            {/* Average Score Card */}
            <div className="stat-card">
              <div className="stat-icon score-icon">🎯</div>
              <div className="stat-content">
                <div className="stat-label">Average Score</div>
                <div className="stat-value">
                  {analytics?.average_score 
                    ? `${Math.round(analytics.average_score * 100)}%` 
                    : '0%'}
                </div>
                <div className="stat-subtitle">Practice problem success rate</div>
              </div>
            </div>

            {/* Learning Streak Card */}
            <div className="stat-card streak-card">
              <div className="stat-icon streak-icon">🔥</div>
              <div className="stat-content">
                <div className="stat-label">Current Streak</div>
                <div className="stat-value">
                  {streaks?.current_streak || 0} days
                </div>
                <div className="stat-subtitle">
                  Longest: {streaks?.longest_streak || 0} days
                </div>
              </div>
            </div>

            {/* Total Time Card */}
            <div className="stat-card">
              <div className="stat-icon time-icon">⏱️</div>
              <div className="stat-content">
                <div className="stat-label">Time Spent</div>
                <div className="stat-value">
                  {analytics?.total_time_minutes 
                    ? `${Math.round(analytics.total_time_minutes / 60)}h ${analytics.total_time_minutes % 60}m`
                    : '0h 0m'}
                </div>
                <div className="stat-subtitle">Total learning time</div>
              </div>
            </div>

            {/* Topics Studied Card */}
            <div className="stat-card">
              <div className="stat-icon topics-icon">📖</div>
              <div className="stat-content">
                <div className="stat-label">Topics Studied</div>
                <div className="stat-value">
                  {analytics?.topics_studied || 0}
                </div>
                <div className="stat-subtitle">Different subjects explored</div>
              </div>
            </div>
          </div>

          {/* Learning Progress Chart */}
          {analytics?.progress_data && analytics.progress_data.length > 0 && (
            <div className="chart-container">
              <div className="chart-header">
                <h2>📈 Learning Progress Over Time</h2>
                <p className="chart-subtitle">Your activity and performance trends</p>
              </div>
              
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={analytics.progress_data}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#666"
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis 
                    stroke="#666"
                    style={{ fontSize: '12px' }}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      padding: '10px'
                    }}
                  />
                  <Legend 
                    wrapperStyle={{ fontSize: '14px' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sessions" 
                    stroke="#667eea" 
                    strokeWidth={3}
                    dot={{ fill: '#667eea', r: 5 }}
                    activeDot={{ r: 7 }}
                    name="Sessions"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="timeSpent" 
                    stroke="#764ba2" 
                    strokeWidth={2}
                    dot={{ fill: '#764ba2', r: 4 }}
                    activeDot={{ r: 6 }}
                    name="Time (min)"
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
              
              <div className="chart-legend-details">
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#667eea' }}></span>
                  <span>Sessions: Learning sessions completed each day</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#764ba2' }}></span>
                  <span>Time: Minutes spent learning each day</span>
                </div>
              </div>
            </div>
          )}

          {/* Topic Performance Chart */}
          {analytics?.topic_data && analytics.topic_data.length > 0 && (
            <div className="chart-container">
              <div className="chart-header">
                <h2>🎯 Topic Performance</h2>
                <p className="chart-subtitle">Your mastery level across different subjects</p>
              </div>
              
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={analytics.topic_data}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis 
                    type="number" 
                    domain={[0, 100]}
                    stroke="#666"
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis 
                    type="category" 
                    dataKey="name"
                    stroke="#666"
                    style={{ fontSize: '12px' }}
                    width={90}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      padding: '10px'
                    }}
                    formatter={(value, name, props) => {
                      if (name === 'score') return [`${value}%`, 'Score'];
                      return [value, name];
                    }}
                  />
                  <Bar 
                    dataKey="score" 
                    radius={[0, 8, 8, 0]}
                  >
                    {analytics.topic_data.map((entry, index) => {
                      // Color based on performance
                      let color = '#667eea'; // default purple
                      if (entry.score >= 90) color = '#10b981'; // green for excellent
                      else if (entry.score >= 80) color = '#667eea'; // purple for good
                      else if (entry.score >= 70) color = '#f59e0b'; // orange for okay
                      else color = '#ef4444'; // red for needs work
                      
                      return <Cell key={`cell-${index}`} fill={color} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              
              <div className="chart-legend-details">
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#10b981' }}></span>
                  <span>Excellent (90-100%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#667eea' }}></span>
                  <span>Good (80-89%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#f59e0b' }}></span>
                  <span>Needs Practice (70-79%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: '#ef4444' }}></span>
                  <span>Needs Work (&lt;70%)</span>
                </div>
              </div>
            </div>
          )}

          {/* Practice Success Rate Chart */}
          {analytics?.practice_data && analytics.practice_data.length > 0 && (
            <div className="chart-container">
              <div className="chart-header">
                <h2>🎯 Practice Success Rate</h2>
                <p className="chart-subtitle">Your performance on practice problems</p>
              </div>
              
              <div className="pie-chart-wrapper">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={analytics.practice_data}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ percent }) => `${(percent * 100).toFixed(1)}%`}
                      labelLine={true}
                    >
                      {analytics.practice_data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #ddd',
                        borderRadius: '8px',
                        padding: '10px'
                      }}
                      formatter={(value, name, props) => [
                        `${value} problems (${props.payload.percentage.toFixed(1)}%)`,
                        name
                      ]}
                    />
                    <Legend 
                      verticalAlign="bottom"
                      height={36}
                      formatter={(value, entry) => {
                        const data = analytics.practice_data.find(d => d.name === value);
                        return `${value}: ${data?.value || 0} (${data?.percentage.toFixed(1) || 0}%)`;
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                
                <div className="pie-center-text">
                  <div className="success-rate">{analytics.average_score ? `${Math.round(analytics.average_score * 100)}%` : '0%'}</div>
                  <div className="success-label">Success Rate</div>
                </div>
              </div>
              
              <div className="chart-stats">
                <div className="stat-item">
                  <span className="stat-icon" style={{ color: '#10b981' }}>✔</span>
                  <span className="stat-text">{analytics.practice_data[0]?.value || 0} Correct</span>
                </div>
                <div className="stat-item">
                  <span className="stat-icon" style={{ color: '#ef4444' }}>✘</span>
                  <span className="stat-text">{analytics.practice_data[1]?.value || 0} Incorrect</span>
                </div>
                <div className="stat-item">
                  <span className="stat-icon" style={{ color: '#f59e0b' }}>⌛</span>
                  <span className="stat-text">{analytics.practice_data[2]?.value || 0} Incomplete</span>
                </div>
              </div>
            </div>
          )}

          {/* Learning Streak Calendar */}
          {analytics?.calendar_data && analytics.calendar_data.length > 0 && (
            <div className="chart-container">
              <div className="chart-header">
                <h2>🔥 Learning Streak Calendar</h2>
                <p className="chart-subtitle">Your daily learning activity over the past 60 days</p>
              </div>
              
              <div className="calendar-wrapper">
                <div className="calendar-info">
                  <div className="streak-info">
                    <div className="streak-stat">
                      <span className="streak-number">{streaks?.current_streak || 0}</span>
                      <span className="streak-label">Current Streak</span>
                    </div>
                    <div className="streak-stat">
                      <span className="streak-number">{streaks?.longest_streak || 0}</span>
                      <span className="streak-label">Longest Streak</span>
                    </div>
                    <div className="streak-stat">
                      <span className="streak-number">{analytics?.active_days || 0}</span>
                      <span className="streak-label">Active Days</span>
                    </div>
                  </div>
                </div>
                
                <div className="calendar-grid">
                  {analytics.calendar_data.map((day, index) => {
                    // Determine color intensity based on sessions
                    let colorClass = 'activity-none';
                    if (day.sessions >= 3) colorClass = 'activity-high';
                    else if (day.sessions === 2) colorClass = 'activity-medium';
                    else if (day.sessions === 1) colorClass = 'activity-low';
                    
                    return (
                      <div
                        key={index}
                        className={`calendar-day ${colorClass}`}
                        title={`${day.displayDate}: ${day.sessions} session${day.sessions !== 1 ? 's' : ''}`}
                        data-tooltip={`${day.dayOfWeek}, ${day.displayDate}\n${day.sessions} session${day.sessions !== 1 ? 's' : ''}`}
                      >
                        <span className="day-number">{day.day === 1 ? day.displayDate.split(' ')[0].substring(0, 3) : ''}</span>
                      </div>
                    );
                  })}
                </div>
                
                <div className="calendar-legend">
                  <span className="legend-label">Less</span>
                  <div className="legend-square activity-none"></div>
                  <div className="legend-square activity-low"></div>
                  <div className="legend-square activity-medium"></div>
                  <div className="legend-square activity-high"></div>
                  <span className="legend-label">More</span>
                </div>
              </div>
              
              <div className="calendar-insights">
                <div className="insight-item">
                  <span className="insight-icon">🏆</span>
                  <span className="insight-text">
                    You're on a <strong>{streaks?.current_streak || 0}-day streak</strong>! Keep it going!
                  </span>
                </div>
                {streaks?.current_streak >= 7 && (
                  <div className="insight-item">
                    <span className="insight-icon">🔥</span>
                    <span className="insight-text">
                      Amazing! You've maintained consistency for over a week.
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          <p className="temp-message">Step 7 Complete! Almost done - CSS and demo page next.</p>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
