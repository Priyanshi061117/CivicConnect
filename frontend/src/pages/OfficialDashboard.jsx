import { useCallback, useEffect, useState } from "react";
import api from "../api";

const transitions = {
  SUBMITTED: ["CLASSIFIED", "ASSIGNED", "IN_PROGRESS", "REJECTED"],
  CLASSIFIED: ["ASSIGNED", "IN_PROGRESS", "REJECTED"],
  ASSIGNED: ["IN_PROGRESS", "REJECTED"],
  IN_PROGRESS: ["RESOLVED", "REJECTED"],
  RESOLVED: ["CLOSED", "IN_PROGRESS"],
  CLOSED: [],
  REJECTED: [],
};

export default function OfficialDashboard() {
  const [complaints, setComplaints] = useState([]);
  const [duplicates, setDuplicates] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setError("");

    try {
      const [complaintResponse, duplicateResponse, analyticsResponse] =
        await Promise.all([
          api.get("/api/official/complaints"),
          api.get("/api/official/duplicates"),
          api.get("/api/official/analytics"),
        ]);

      setComplaints(complaintResponse.data);
      setDuplicates(duplicateResponse.data);
      setAnalytics(analyticsResponse.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Could not load the official dashboard."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const visible = complaints.filter((c) => {
    const term = search.trim().toLowerCase();

    const matchesSearch =
      !term ||
      String(c.id).includes(term) ||
      (c.description || "").toLowerCase().includes(term) ||
      (c.locality || "").toLowerCase().includes(term);

    return (
      matchesSearch &&
      (!status || c.status === status) &&
      (!priority || c.priority === priority)
    );
  });

  async function changeStatus(complaint, newStatus) {
    if (!newStatus || newStatus === complaint.status) return;

    const comment = window.prompt(
      `Add an optional comment for status ${newStatus}:`,
      ""
    );

    if (comment === null) return;

    setBusyId(complaint.id);
    setError("");
    setMessage("");

    try {
      await api.patch(
        `/api/official/complaints/${complaint.id}/status`,
        { status: newStatus, comment }
      );

      setMessage(`Complaint #${complaint.id} updated to ${newStatus}.`);
      await load();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Status update failed."
      );
    } finally {
      setBusyId(null);
    }
  }

  async function reviewDuplicate(complaintId, decision) {
    const comment = window.prompt(
      `Optional review comment for ${decision}:`,
      ""
    );

    if (comment === null) return;

    setError("");
    setMessage("");

    try {
      await api.post(
        `/api/official/duplicates/${complaintId}/review`,
        { decision, comment }
      );

      setMessage(`Duplicate review saved for complaint #${complaintId}.`);
      await load();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Could not save duplicate review."
      );
    }
  }

  if (loading) return <p>Loading official dashboard...</p>;

  return (
    <div className="space-y-7">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          Official dashboard
        </h1>
        <p className="mt-1 text-slate-600">
          Review complaints and update their progress.
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

      {analytics && (
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            ["Total", analytics.total],
            ["Pending", analytics.pending],
            ["Resolved / closed", analytics.resolved],
          ].map(([label, value]) => (
            <div key={label} className="rounded-xl border bg-white p-5">
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-2 text-3xl font-bold">{value}</p>
            </div>
          ))}
        </div>
      )}

      <section className="space-y-4 rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">Complaint queue</h2>

        <div className="grid gap-3 sm:grid-cols-3">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search ID, description, locality"
            className="rounded-lg border p-3"
          />

          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-lg border p-3"
          >
            <option value="">All statuses</option>
            {Object.keys(transitions).map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>

          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="rounded-lg border p-3"
          >
            <option value="">All priorities</option>
            {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </div>

        <p className="text-sm text-slate-500">
          Showing {visible.length} of {complaints.length} complaints.
        </p>

        {visible.length === 0 ? (
          <p className="text-slate-500">No matching complaints.</p>
        ) : visible.map((c) => (
          <article key={c.id} className="rounded-lg border p-4">
            <div className="flex flex-wrap justify-between gap-2">
              <strong>Complaint #{c.id}</strong>
              <span className="font-semibold">{c.priority}</span>
            </div>

            <p className="mt-3 whitespace-pre-wrap">{c.description}</p>

            <p className="mt-2 text-sm text-slate-500">
              Locality: {c.locality || "Not provided"}
              {" · "}Status: {c.status}
            </p>

            {c.priority_reason && (
              <p className="mt-2 text-sm text-slate-600">
                Priority reason: {c.priority_reason}
              </p>
            )}

            <div className="mt-4 flex flex-wrap gap-2">
              <select
                defaultValue=""
                disabled={busyId === c.id}
                onChange={(e) => {
                  const next = e.target.value;
                  e.target.value = "";
                  if (next) changeStatus(c, next);
                }}
                className="rounded-lg border p-2"
              >
                <option value="">Update status...</option>
                {(transitions[c.status] || []).map((next) => (
                  <option key={next} value={next}>{next}</option>
                ))}
              </select>

              {c.duplicate_of_complaint_id && (
                <span className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
                  Possible duplicate of #{c.duplicate_of_complaint_id}
                  {c.duplicate_similarity != null
                    ? ` · Similarity ${(c.duplicate_similarity * 100).toFixed(1)}%`
                    : ""}
                </span>
              )}
            </div>
          </article>
        ))}
      </section>

      <section className="space-y-4 rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">Potential duplicate review</h2>
        <p className="text-sm text-slate-500">
          Reviewing a candidate does not merge or delete either complaint.
        </p>

        {duplicates.length === 0 ? (
          <p className="text-slate-500">No duplicate candidates found.</p>
        ) : duplicates.map((d) => (
          <article key={d.complaint_id} className="rounded-lg border p-4">
            <p className="font-semibold">
              Complaint #{d.complaint_id}
              {" · "}Original #{d.original_complaint_id ?? "Unavailable"}
            </p>

            <p className="mt-2">{d.description}</p>

            <p className="mt-2 text-sm text-slate-500">
              Locality: {d.locality || "Not provided"}
              {" · "}Priority: {d.priority}
              {" · "}Status: {d.status}
              {" · "}Similarity: {d.duplicate_similarity == null
                ? "N/A"
                : `${(d.duplicate_similarity * 100).toFixed(1)}%`}
            </p>

            {d.original_description && (
              <p className="mt-3 text-sm text-slate-600">
                Original complaint: {d.original_description}
              </p>
            )}

            {d.review_decision && (
              <p className="mt-3 text-sm font-semibold">
                Current review: {d.review_decision}
              </p>
            )}

            <div className="mt-4 flex flex-wrap gap-2">
              <button
                onClick={() => reviewDuplicate(d.complaint_id, "RELATED")}
                className="rounded-lg bg-blue-700 px-4 py-2 text-white"
              >
                Mark related
              </button>

              <button
                onClick={() => reviewDuplicate(d.complaint_id, "DISMISSED")}
                className="rounded-lg border px-4 py-2"
              >
                Dismiss suggestion
              </button>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}