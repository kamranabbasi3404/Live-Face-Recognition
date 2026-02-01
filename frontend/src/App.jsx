import { useState, useRef, useCallback, useEffect } from 'react'
import Webcam from 'react-webcam'
import { AuthProvider, useAuth } from './AuthContext'
import { LoginPage, RegisterPage } from './AuthPages'
import Logo from './assets/Logo.png'
import './App.css'
import './Auth.css'

const API_URL = 'http://localhost:5000/api'

function AppContent() {
  const { user, token, loading: authLoading, logout, isAuthenticated } = useAuth()
  const [authMode, setAuthMode] = useState('login') // 'login' or 'register'

  const [currentPage, setCurrentPage] = useState('home')
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  // Enroll states
  const [enrollName, setEnrollName] = useState('')
  const [enrollUserId, setEnrollUserId] = useState('')
  const [capturedImages, setCapturedImages] = useState([])

  // Verify states
  const [verifyResult, setVerifyResult] = useState(null)

  const webcamRef = useRef(null)

  // Helper function to make authenticated API calls
  const authFetch = useCallback(async (url, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return fetch(url, { ...options, headers })
  }, [token])

  // Fetch users on load and when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchUsers()
    }
  }, [isAuthenticated])

  const fetchUsers = async () => {
    try {
      const res = await authFetch(`${API_URL}/users`)
      const data = await res.json()
      if (data.success) {
        setUsers(data.users)
      }
    } catch (err) {
      console.error('Error fetching users:', err)
    }
  }

  const captureImage = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot()
    if (imageSrc) {
      setCapturedImages(prev => [...prev, imageSrc])
    }
  }, [])

  const enrollUser = async () => {
    if (!enrollName.trim()) {
      setMessage({ type: 'error', text: 'Please enter a name' })
      return
    }
    if (capturedImages.length === 0) {
      setMessage({ type: 'error', text: 'Please capture at least one photo' })
      return
    }

    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/enroll`, {
        method: 'POST',
        body: JSON.stringify({
          name: enrollName,
          user_id: enrollUserId,
          image: capturedImages[0]
        })
      })
      const data = await res.json()

      if (data.success) {
        setMessage({ type: 'success', text: `✅ ${data.message}` })
        setEnrollName('')
        setEnrollUserId('')
        setCapturedImages([])
        fetchUsers()
      } else {
        setMessage({ type: 'error', text: `❌ ${data.error}` })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to connect to server' })
    }
    setLoading(false)
  }

  const verifyFace = async () => {
    const imageSrc = webcamRef.current?.getScreenshot()
    if (!imageSrc) {
      setMessage({ type: 'error', text: 'Failed to capture image' })
      return
    }

    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/verify`, {
        method: 'POST',
        body: JSON.stringify({ image: imageSrc })
      })
      const data = await res.json()
      setVerifyResult(data)
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to connect to server' })
    }
    setLoading(false)
  }

  const deleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return

    try {
      const res = await authFetch(`${API_URL}/users/${userId}`, { method: 'DELETE' })
      const data = await res.json()
      if (data.success) {
        setMessage({ type: 'success', text: '✅ User deleted' })
        fetchUsers()
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to delete user' })
    }
  }

  // Show loading spinner while checking auth
  if (authLoading) {
    return (
      <div className="auth-loading">
        <div className="loading-spinner">⏳</div>
      </div>
    )
  }

  // Show auth pages if not authenticated
  if (!isAuthenticated) {
    if (authMode === 'login') {
      return <LoginPage onSwitchToRegister={() => setAuthMode('register')} />
    }
    return <RegisterPage onSwitchToLogin={() => setAuthMode('login')} />
  }

  // Main app (authenticated)
  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo">
          <img src={Logo} alt="Logo" className="logo-img" />
          <h1>Face Recognition</h1>
        </div>

        {/* Account Box - Contains everything */}
        <div className="account-box">
          {/* User Name at top */}
          <div className="account-header">
            <span className="account-name">{user?.name}</span>
            <span className="account-email">{user?.email}</span>
          </div>

          {/* Nav buttons */}
          <nav className="nav">
            <button
              className={`nav-btn ${currentPage === 'home' ? 'active' : ''}`}
              onClick={() => setCurrentPage('home')}
            >
              🏠 Home
            </button>
            <button
              className={`nav-btn ${currentPage === 'enroll' ? 'active' : ''}`}
              onClick={() => setCurrentPage('enroll')}
            >
              ➕ Enroll User
            </button>
            <button
              className={`nav-btn ${currentPage === 'verify' ? 'active' : ''}`}
              onClick={() => setCurrentPage('verify')}
            >
              ✓ Verify Face
            </button>
            <button
              className={`nav-btn ${currentPage === 'users' ? 'active' : ''}`}
              onClick={() => setCurrentPage('users')}
            >
              👥 Manage Users
            </button>
          </nav>

          {/* Bottom section with enrolled count and logout */}
          <div className="sidebar-bottom">
            {/* Enrolled count */}
            <div className="enrolled-count">
              <span className="count-number">{users.length}</span>
              <span className="count-label">Enrolled Users</span>
            </div>

            {/* Logout at very bottom */}
            <button className="logout-btn" onClick={logout}>
              🚪 Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main">
        {message && (
          <div className={`message ${message.type}`}>
            {message.text}
            <button onClick={() => setMessage(null)}>×</button>
          </div>
        )}

        {currentPage === 'home' && <HomePage />}
        {currentPage === 'enroll' && (
          <EnrollPage
            webcamRef={webcamRef}
            enrollName={enrollName}
            setEnrollName={setEnrollName}
            enrollUserId={enrollUserId}
            setEnrollUserId={setEnrollUserId}
            capturedImages={capturedImages}
            captureImage={captureImage}
            enrollUser={enrollUser}
            loading={loading}
            setCapturedImages={setCapturedImages}
          />
        )}
        {currentPage === 'verify' && (
          <VerifyPage
            webcamRef={webcamRef}
            verifyFace={verifyFace}
            verifyResult={verifyResult}
            loading={loading}
            setVerifyResult={setVerifyResult}
          />
        )}
        {currentPage === 'users' && (
          <UsersPage
            users={users}
            deleteUser={deleteUser}
          />
        )}
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

function HomePage() {
  return (
    <div className="page home-page">
      {/* Hero Section */}
      <div className="hero-section">
        <img src={Logo} alt="Logo" className="hero-logo" />
        <h1 className="hero-title">Live Face Recognition</h1>
        <p className="hero-subtitle">Advanced Real-Time Face Verification System</p>
        <p className="hero-description">
          Powered by DeepFace AI with Facenet512 model for accurate face detection,
          enrollment, and verification. Secure, fast, and reliable.
        </p>
      </div>

      {/* Stats Section */}
      <div className="stats-section">
        <div className="stat-card">
          <span className="stat-icon">🎯</span>
          <span className="stat-number">99.6%</span>
          <span className="stat-text">Accuracy</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">⚡</span>
          <span className="stat-number">&lt;1s</span>
          <span className="stat-text">Response Time</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🔒</span>
          <span className="stat-number">512-D</span>
          <span className="stat-text">Embeddings</span>
        </div>
      </div>

      {/* Features */}
      <h2 className="section-title">Features</h2>
      <div className="features">
        <div className="feature-card">
          <div className="feature-icon-wrapper">
            <span className="feature-icon">➕</span>
          </div>
          <h3>Enroll User</h3>
          <p>Register new faces using your webcam with live duplicate detection</p>
          <ul className="feature-list">
            <li>✓ Live webcam capture</li>
            <li>✓ Duplicate face detection</li>
            <li>✓ Auto user ID generation</li>
          </ul>
        </div>
        <div className="feature-card">
          <div className="feature-icon-wrapper verify">
            <span className="feature-icon">✓</span>
          </div>
          <h3>Verify Face</h3>
          <p>Real-time face verification with confidence scoring</p>
          <ul className="feature-list">
            <li>✓ Instant verification</li>
            <li>✓ Confidence percentage</li>
            <li>✓ Access control</li>
          </ul>
        </div>
        <div className="feature-card">
          <div className="feature-icon-wrapper users">
            <span className="feature-icon">👥</span>
          </div>
          <h3>Manage Users</h3>
          <p>View, search, and manage enrolled users</p>
          <ul className="feature-list">
            <li>✓ User search</li>
            <li>✓ Delete users</li>
            <li>✓ View details</li>
          </ul>
        </div>
      </div>

      {/* Technology */}
      <div className="tech-section">
        <h3>Powered By</h3>
        <div className="tech-badges">
          <span className="tech-badge">DeepFace</span>
          <span className="tech-badge">Facenet512</span>
          <span className="tech-badge">TensorFlow</span>
          <span className="tech-badge">React</span>
          <span className="tech-badge">Flask</span>
        </div>
      </div>
    </div>
  )
}

function EnrollPage({ webcamRef, enrollName, setEnrollName, enrollUserId, setEnrollUserId, capturedImages, captureImage, enrollUser, loading, setCapturedImages }) {
  return (
    <div className="page enroll-page">
      <h2>➕ Enroll New User</h2>

      <div className="enroll-grid">
        <div className="form-section">
          <div className="form-group">
            <label>User ID (optional)</label>
            <input
              type="text"
              value={enrollUserId}
              onChange={e => setEnrollUserId(e.target.value)}
              placeholder="Leave empty for auto-generate"
            />
          </div>

          <div className="form-group">
            <label>Full Name *</label>
            <input
              type="text"
              value={enrollName}
              onChange={e => setEnrollName(e.target.value)}
              placeholder="Enter full name"
              required
            />
          </div>

          <div className="captured-count">
            📸 Captured: {capturedImages.length} images
          </div>

          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${Math.min(capturedImages.length / 5 * 100, 100)}%` }}
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={enrollUser}
            disabled={loading || !enrollName.trim() || capturedImages.length === 0}
          >
            {loading ? '⏳ Saving...' : '💾 Save User'}
          </button>

          <button
            className="btn btn-secondary"
            onClick={() => {
              setEnrollName('')
              setEnrollUserId('')
              setCapturedImages([])
            }}
          >
            🔄 Reset
          </button>
        </div>

        <div className="camera-section">
          <div className="webcam-container">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              videoConstraints={{ facingMode: 'user' }}
              className="webcam"
            />
          </div>

          <button
            className="btn btn-capture"
            onClick={captureImage}
          >
            📸 Capture
          </button>
        </div>
      </div>
    </div>
  )
}

function VerifyPage({ webcamRef, verifyFace, verifyResult, loading, setVerifyResult }) {
  return (
    <div className="page verify-page">
      <h2>✓ Face Verification</h2>

      <div className="verify-layout">
        {/* Camera Section - Left/Main */}
        <div className="verify-camera-box">
          <div className="webcam-container-large">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              videoConstraints={{ facingMode: 'user', width: 640, height: 480 }}
              className="webcam"
            />
          </div>

          <button
            className="btn btn-verify-large"
            onClick={verifyFace}
            disabled={loading}
          >
            {loading ? '⏳ Verifying...' : '🔍 Verify Face'}
          </button>
        </div>

        {/* Result Section - Right */}
        <div className="verify-result-box">
          {verifyResult ? (
            <div className={`result-card ${verifyResult.verified ? 'success' : 'denied'}`}>
              <div className="result-icon-large">{verifyResult.verified ? '✅' : '❌'}</div>
              <h3>{verifyResult.verified ? 'ACCESS GRANTED' : 'ACCESS DENIED'}</h3>
              {verifyResult.verified ? (
                <>
                  <p className="welcome-text">Welcome, {verifyResult.user_name}!</p>
                  <div className="confidence-bar">
                    <div className="confidence-fill" style={{ width: `${verifyResult.confidence}%` }}></div>
                  </div>
                  <p className="confidence-text">{verifyResult.confidence?.toFixed(1)}% Confidence</p>
                </>
              ) : (
                <p className="denied-text">Face not recognized in database</p>
              )}
              <button className="btn btn-secondary" onClick={() => setVerifyResult(null)}>
                🔄 Try Again
              </button>
            </div>
          ) : (
            <div className="verify-instructions">
              <div className="instruction-icon">📷</div>
              <h3>Ready to Verify</h3>
              <ul className="instruction-list">
                <li>Position your face in the camera</li>
                <li>Ensure good lighting</li>
                <li>Look directly at the camera</li>
                <li>Click "Verify Face" button</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function UsersPage({ users, deleteUser }) {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredUsers = users.filter(u =>
    u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.user_id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="page users-page">
      <h2>👥 Manage Users</h2>

      <div className="search-bar">
        <input
          type="text"
          placeholder="🔍 Search users..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="users-count">
        Total: {filteredUsers.length} users
      </div>

      <div className="users-list">
        {filteredUsers.map(user => (
          <div key={user.user_id} className="user-card">
            <div className="user-avatar">👤</div>
            <div className="user-info">
              <h4>{user.name}</h4>
              <p>ID: {user.user_id}</p>
              <small>Enrolled: {user.created_at}</small>
            </div>
            <button
              className="btn btn-danger"
              onClick={() => deleteUser(user.user_id)}
            >
              🗑️ Delete
            </button>
          </div>
        ))}

        {filteredUsers.length === 0 && (
          <p className="no-users">No users found</p>
        )}
      </div>
    </div>
  )
}

export default App
