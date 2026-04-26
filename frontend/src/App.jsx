import { Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import AnalyzeLeadPage from "./pages/AnalyzeLeadPage";
import DashboardPage from "./pages/DashboardPage";
import LandingPage from "./pages/LandingPage";
import LeadDetailPage from "./pages/LeadDetailPage";

export default function App() {
  return (
    <Routes>
      <Route index element={<LandingPage />} />
      <Route element={<AppShell />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/analyze" element={<AnalyzeLeadPage />} />
        <Route path="/leads/:leadId" element={<LeadDetailPage />} />
      </Route>
    </Routes>
  );
}
