import "@/App.css";
import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Dashboard } from "./components/Dashboard";
import { ProfileAnalyzer } from "./components/ProfileAnalyzer";
import { Login } from "./components/Login";
import { AgentsCenter } from "./components/AgentsCenter";
import { LegalLayout } from "./components/legal/LegalLayout";
import { PrivacyPolicy } from "./components/legal/PrivacyPolicy";
import { TermsOfUse } from "./components/legal/TermsOfUse";
import { CookiePolicy } from "./components/legal/CookiePolicy";
import { Toaster } from "./components/ui/sonner";
import api from "./lib/api";

const ProtectedRoute = ({ isAuthenticated, children }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const AppRoutes = ({ token, setToken, loginLoading, setLoginLoading, loginError, setLoginError }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const isAuthenticated = Boolean(token);
  const isLoginPage = location.pathname === "/login";
  const isLegalPage = location.pathname.startsWith("/legal");
  const showAppChrome = isAuthenticated && !isLoginPage && !isLegalPage;

  const handleAnalyze = async (profileData) => {
    const res = await api.post("/analyze-profile", profileData);
    return res.data;
  };

  const handleLogin = async ({ email, password }) => {
    setLoginLoading(true);
    setLoginError("");
    try {
      const res = await api.post("/auth/login", { email, password });
      const accessToken = res.data?.access_token;
      if (!accessToken) {
        throw new Error("Token manquant");
      }
      localStorage.setItem("auth_token", accessToken);
      setToken(accessToken);
      navigate("/", { replace: true });
    } catch (err) {
      setLoginError(err?.response?.data?.detail || "Connexion impossible");
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    setToken("");
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-[#050505]">
      {showAppChrome ? <Sidebar onLogout={handleLogout} /> : null}
      <main className={showAppChrome ? "ml-64 min-h-screen p-8" : "min-h-screen"}>
        <Routes>
          <Route path="/legal" element={<LegalLayout />}>
            <Route index element={<Navigate to="privacy" replace />} />
            <Route path="privacy" element={<PrivacyPolicy />} />
            <Route path="terms" element={<TermsOfUse />} />
            <Route path="cookies" element={<CookiePolicy />} />
          </Route>
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login onLogin={handleLogin} loading={loginLoading} error={loginError} />
              )
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analyze"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <ProfileAnalyzer onAnalyze={handleAnalyze} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/agents"
            element={
              <ProtectedRoute isAuthenticated={isAuthenticated}>
                <AgentsCenter />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
        </Routes>
      </main>
      <Toaster />
    </div>
  );
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("auth_token") || "");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState("");

  return (
    <BrowserRouter>
      <AppRoutes
        token={token}
        setToken={setToken}
        loginLoading={loginLoading}
        setLoginLoading={setLoginLoading}
        loginError={loginError}
        setLoginError={setLoginError}
      />
    </BrowserRouter>
  );
}

export default App;
