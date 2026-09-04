import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Watchlist from "./pages/Watchlist";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Loading...</div>;
  return user ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/watchlist" element={
            <ProtectedRoute>
              <Watchlist />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
