import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

const API_URL = 'http://localhost:5000/api'

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(localStorage.getItem('token'))
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Check if token exists and validate it
        if (token) {
            validateToken()
        } else {
            setLoading(false)
        }
    }, [])

    const validateToken = async () => {
        try {
            const res = await fetch(`${API_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })
            const data = await res.json()

            if (data.success) {
                setUser(data.user)
            } else {
                // Token invalid, clear it
                logout()
            }
        } catch (err) {
            console.error('Token validation error:', err)
            logout()
        } finally {
            setLoading(false)
        }
    }

    const register = async (name, email, password) => {
        const res = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        })
        const data = await res.json()

        if (data.success) {
            setToken(data.token)
            setUser(data.user)
            localStorage.setItem('token', data.token)
        }

        return data
    }

    const login = async (email, password) => {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        })
        const data = await res.json()

        if (data.success) {
            setToken(data.token)
            setUser(data.user)
            localStorage.setItem('token', data.token)
        }

        return data
    }

    const logout = () => {
        setToken(null)
        setUser(null)
        localStorage.removeItem('token')
    }

    const value = {
        user,
        token,
        loading,
        register,
        login,
        logout,
        isAuthenticated: !!token && !!user
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
