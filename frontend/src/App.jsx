
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleRoute from "./components/RoleRoute";
import Layout from "./components/Layout";

import Welcome from "./pages/Welcome";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import NewComplaint from "./pages/NewComplaint";
import ComplaintDetail from "./pages/ComplaintDetail";
import OfficialDashboard from "./pages/OfficialDashboard";
import AdminDashboard from "./pages/AdminDashboard";

function DashboardRedirect() {
  const { user } = useAuth();
  const role = String(user?.role || "").toLowerCase();

  if (role === "admin") {
    return <Navigate to="/admin" replace />;
  }

  if (role === "official") {
    return <Navigate to="/official" replace />;
  }

  return <Dashboard />;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public pages */}
      <Route path="/" element={<Welcome />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Pages requiring login */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route
            path="/dashboard"
            element={<DashboardRedirect />}
          />

          {/* Citizen-only pages */}
          <Route element={<RoleRoute roles={["citizen"]} />}>
            <Route
              path="/complaints/new"
              element={<NewComplaint />}
            />
            <Route
              path="/complaints/:id"
              element={<ComplaintDetail />}
            />
          </Route>

          {/* Official operational dashboard */}
          <Route element={<RoleRoute roles={["official", "admin"]} />}>
            <Route
              path="/official"
              element={<OfficialDashboard />}
            />
          </Route>

          {/* Admin dashboard and management */}
          <Route element={<RoleRoute roles={["admin"]} />}>
            <Route
              path="/admin"
              element={<AdminDashboard />}
            />
          </Route>
        </Route>
      </Route>

      {/* Unknown URLs return to the welcome page */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}


