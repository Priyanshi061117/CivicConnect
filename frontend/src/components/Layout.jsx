
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const role = String(user?.role || "citizen").toLowerCase();

  function handleLogout() {
    logout();
    navigate("/", { replace: true });
  }

  const navClass = ({ isActive }) =>
    `rounded-lg px-3 py-2 text-sm font-medium ${
      isActive
        ? "bg-blue-50 text-blue-700"
        : "text-slate-600 hover:bg-slate-100"
    }`;

  const dashboardPath =
    role === "admin"
      ? "/admin"
      : role === "official"
        ? "/official"
        : "/dashboard";

  const dashboardLabel =
    role === "admin"
      ? "Admin dashboard"
      : role === "official"
        ? "Official dashboard"
        : "My complaints";

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4">
          <Link
            to={dashboardPath}
            className="flex items-center gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-700 text-lg font-bold text-white">
              C
            </div>

            <div>
              <p className="font-bold text-slate-900">
                CivicConnect
              </p>
              <p className="text-xs text-slate-500">
                AI Civic Complaint Router
              </p>
            </div>
          </Link>

          <nav className="flex flex-wrap items-center gap-2">
            <NavLink to={dashboardPath} className={navClass}>
              {dashboardLabel}
            </NavLink>

            {role === "admin" && (
              <NavLink to="/official" className={navClass}>
                Complaint Queue
              </NavLink>
            )}



            <span className="px-2 text-sm text-slate-500">
              {user?.full_name} ({role})
            </span>

            <button
              onClick={handleLogout}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Log out
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white px-5 py-5 text-center text-sm text-slate-500">
        AI Civic Complaint Router
      </footer>
    </div>
  );
}

