/**
 * authService.js
 * Authentication service for login, logout, and token handling.
 */

import api from './api'

export const authService = {
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    const { access_token, user } = response.data
    if (access_token) {
      localStorage.setItem('access_token', access_token)
    }
    if (user) {
      localStorage.setItem('user_profile', JSON.stringify(user))
    }
    return response.data
  },

  async register(payload) {
    const response = await api.post('/auth/register', payload)
    return response.data
  },

  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_profile')
  },

  getCurrentUser() {
    const raw = localStorage.getItem('user_profile')
    try {
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  },

  getToken() {
    return localStorage.getItem('access_token')
  },

  isAuthenticated() {
    return Boolean(localStorage.getItem('access_token'))
  },

  async fetchMe() {
    const response = await api.get('/auth/me')
    if (response.data) {
      localStorage.setItem('user_profile', JSON.stringify(response.data))
    }
    return response.data
  },
}

export const registerUser = (payload) => authService.register(payload)
export const loginUser = (email, password) => authService.login(email, password)
export const getCurrentUser = () => authService.getCurrentUser()
export const logoutUser = () => authService.logout()

export default authService
