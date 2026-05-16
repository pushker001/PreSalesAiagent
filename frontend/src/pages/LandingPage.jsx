import { Navigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  return <Navigate to={isAuthenticated ? "/dashboard" : "/auth"} replace />;
}
