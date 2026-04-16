import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Dashboard } from "./components/Dashboard";
import { ProfileAnalyzer } from "./components/ProfileAnalyzer";
import { Toaster } from "./components/ui/sonner";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function App() {
  const handleAnalyze = async (profileData) => {
    const res = await axios.post(`${API}/analyze-profile`, profileData);
    return res.data;
  };

  return (
    <div className="min-h-screen bg-[#050505]">
      <BrowserRouter>
        <Sidebar />
        <main className="ml-64 min-h-screen p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route
              path="/analyze"
              element={<ProfileAnalyzer onAnalyze={handleAnalyze} />}
            />
          </Routes>
        </main>
        <Toaster />
      </BrowserRouter>
    </div>
  );
}

export default App;
