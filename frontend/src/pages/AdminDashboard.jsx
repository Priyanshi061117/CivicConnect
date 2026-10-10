import { useCallback, useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import api from "../api";

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [edits, setEdits] = useState({});
  const [departmentName, setDepartmentName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setError("");

    try {
      const [analyticsResponse, usersResponse, departmentsResponse] =
        await Promise.all([
          api.get("/api/admin/analytics"),
          api.get("/api/admin/users"),
          api.get("/api/admin/departments"),
        ]);

      setAnalytics(analyticsResponse.data);
      setUsers(usersResponse.data);
      setDepartments(departmentsResponse.data);

      setEdits((previous) => {
        const next = { ...previous };

        usersResponse.data.forEach((u) => {
          if (!next[u.id]) {
            next[u.id] = {
              role: u.role,
              department_id: u.department_id ?? "",
              is_active: u.is_active,
            };
          }
        });

        return next;
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Could not load administrator data."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function editUser(id, field, value) {
    setEdits((previous) => ({
      ...previous,
      [id]: {
        ...previous[id],
        [field]: value,
      },
    }));
  }

  async function saveUser(user) {
    const edit = edits[user.id] || {};

    if (edit.role === "official" && !edit.department_id) {
      setError("Select a department before assigning the official role.");
      return;
    }

    setError("");
    setMessage("");

    try {
      await api.patch(`/api/admin/users/${user.id}`, {
        role: edit.role,
        department_id:
          edit.role === "official" ? Number(edit.department_id) : null,
        is_active: Boolean(edit.is_active),
      });

      setMessage(`Updated account for ${user.full_name}.`);
      await load();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Could not update the user."
      );
    }
  }

  async function createDepartment(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    try {
      await api.post("/api/admin/departments", {
        name: departmentName,
      });

      setDepartmentName("");
      setMessage("Department created successfully.");
      await load();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Could not create department."
      );
    }
  }

  if (loading) return <p>Loading administration...</p>;

  const statusData = Object.entries(analytics?.by_status || {}).map(
    ([name, value]) => ({ name, value })
  );

  const priorityData = Object.entries(analytics?.by_priority || {}).map(
    ([name, value]) => ({ name, value })
  );

  const departmentData = Object.entries(
    analytics?.by_department || {}
  ).map(([name, value]) => ({ name, value }));

  function ChartPanel({ title, data }) {
    return (
      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-bold">{title}</h2>

        {data.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No data available.</p>
        ) : (
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ bottom: 35 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  interval={0}
                  angle={-20}
                  textAnchor="end"
                  height={65}
                />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>
    );
  }

  return (
    <div className="space-y-7">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          Administration
        </h1>
        <p className="mt-1 text-slate-600">
          Manage accounts, departments, and complaint analytics.
        </p>
      </div>

      {error && (
        <div role="alert" className="rounded-lg bg-red-50 p-4 text-red-700">
          {error}
        </div>
      )}

      {message && (
        <div className="rounded-lg bg-green-50 p-4 text-green-800">
          {message}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          ["Total complaints", analytics?.total],
          ["Pending complaints", analytics?.pending],
          ["Resolved / closed", analytics?.resolved],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border bg-white p-5">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-bold">{value ?? 0}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <ChartPanel title="Complaints by status" data={statusData} />
        <ChartPanel title="Complaints by priority" data={priorityData} />
        <div className="lg:col-span-2">
          <ChartPanel
            title="Complaints by department"
            data={departmentData}
          />
        </div>
      </div>

      <section className="space-y-4 rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">Manage departments</h2>

        <form
          onSubmit={createDepartment}
          className="flex flex-wrap gap-3"
        >
          <input
            value={departmentName}
            onChange={(e) => setDepartmentName(e.target.value)}
            required
            minLength={2}
            maxLength={120}
            placeholder="New department name"
            className="min-w-0 flex-1 rounded-lg border p-3"
          />
          <button className="rounded-lg bg-blue-700 px-4 py-3 font-semibold text-white">
            Add department
          </button>
        </form>

        <ul className="list-inside list-disc space-y-1 text-slate-700">
          {departments.map((d) => (
            <li key={d.id}>{d.name} (ID: {d.id})</li>
          ))}
        </ul>
      </section>

      <section className="space-y-4 rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">Manage users</h2>

        {users.map((user) => {
          const edit = edits[user.id] || {
            role: user.role,
            department_id: user.department_id ?? "",
            is_active: user.is_active,
          };

          return (
            <article key={user.id} className="space-y-3 rounded-lg border p-4">
              <div>
                <p className="font-semibold">{user.full_name}</p>
                <p className="text-sm text-slate-500">{user.email}</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <label className="text-sm">
                  Role
                  <select
                    value={edit.role}
                    onChange={(e) => {
                      const role = e.target.value;
                      setEdits((previous) => ({
                        ...previous,
                        [user.id]: {
                          ...edit,
                          role,
                          department_id:
                            role === "official"
                              ? edit.department_id
                              : "",
                        },
                      }));
                    }}
                    className="mt-1 w-full rounded-lg border p-2"
                  >
                    <option value="citizen">Citizen</option>
                    <option value="official">Official</option>
                    <option value="admin">Admin</option>
                  </select>
                </label>

                <label className="text-sm">
                  Department
                  <select
                    value={edit.department_id ?? ""}
                    disabled={edit.role !== "official"}
                    onChange={(e) =>
                      editUser(user.id, "department_id", e.target.value)
                    }
                    className="mt-1 w-full rounded-lg border p-2 disabled:bg-slate-100"
                  >
                    <option value="">Select department</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </label>

                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={Boolean(edit.is_active)}
                    onChange={(e) =>
                      editUser(user.id, "is_active", e.target.checked)
                    }
                  />
                  Account active
                </label>
              </div>

              <button
                onClick={() => saveUser(user)}
                className="rounded-lg bg-blue-700 px-4 py-2 font-semibold text-white"
              >
                Save user
              </button>
            </article>
          );
        })}
      </section>
    </div>
  );
}