import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function RoleRoute({ roles }) {
  const { user } = useAuth();

  if (!user || !roles.includes(String(user.role).toLowerCase())) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}