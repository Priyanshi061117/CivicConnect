
import {
    createContext,
    useContext,
    useEffect,
    useState,
  } from "react";
  
  import api from "../api";
  
  const AuthContext = createContext(null);
  
  export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
  
    useEffect(() => {
      const token = localStorage.getItem("token");
  
      if (!token) {
        setLoading(false);
        return;
      }
  
      api
        .get("/api/auth/me")
        .then((response) => {
          setUser(response.data);
        })
        .catch(() => {
          localStorage.removeItem("token");
          setUser(null);
        })
        .finally(() => {
          setLoading(false);
        });
    }, []);
  
    async function login(credentials) {
      const response = await api.post(
        "/api/auth/login",
        credentials
      );
  
      localStorage.setItem(
        "token",
        response.data.access_token
      );
  
      try {
        const profile = await api.get("/api/auth/me");
        setUser(profile.data);
        return profile.data;
      } catch (error) {
        localStorage.removeItem("token");
        setUser(null);
        throw error;
      }
    }
  
    function logout() {
      localStorage.removeItem("token");
      setUser(null);
    }
  
    return (
      <AuthContext.Provider
        value={{ user, loading, login, logout }}
      >
        {children}
      </AuthContext.Provider>
    );
  }
  
  export function useAuth() {
    const context = useContext(AuthContext);
  
    if (!context) {
      throw new Error(
        "useAuth must be used inside AuthProvider"
      );
    }
  
    return context;
  }
  