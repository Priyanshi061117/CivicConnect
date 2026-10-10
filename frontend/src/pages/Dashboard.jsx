
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";

export default function Dashboard() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadComplaints() {
      try {
        const { data } = await api.get("/api/complaints/");

        if (active) {
          setComplaints(
            Array.isArray(data) ? data : data.items || []
          );
        }
      } catch (err) {
        if (active) {
          setError(
            err.response?.data?.detail ||
              "Could not load your complaints. Please try again."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadComplaints();

    return () => {
      active = false;
    };
  }, []);

  const pending = complaints.filter(
    (c) => !["RESOLVED", "CLOSED", "REJECTED"].includes(c.status)
  ).length;

  const resolved = complaints.filter(
    (c) => ["RESOLVED", "CLOSED"].includes(c.status)
  ).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            My complaints
          </h1>
          <p className="mt-1 text-slate-600">
            View your submitted complaints and track their progress.
          </p>
        </div>

        <Link
          to="/complaints/new"
          className="rounded-lg bg-white-700 px-5 py-3 font-semibold text-white hover:bg-blue-800"
        >
          + New complaint
        </Link>
      </div>

      {error && (
        <div role="alert" className="rounded-lg bg-red-50 p-4 text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          ["Total complaints", complaints.length],
          ["Pending complaints", pending],
          ["Resolved complaints", resolved],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {loading ? "..." : value}
            </p>
          </div>
        ))}
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-xl font-bold text-slate-900">
          Your submitted complaints
        </h2>

        {loading ? (
          <p className="mt-4 text-slate-500">
            Loading your complaints...
          </p>
        ) : complaints.length === 0 ? (
          <div className="mt-4 rounded-lg bg-slate-50 p-6 text-center">
            <p className="font-medium text-slate-700">
              You have not submitted any complaints yet.
            </p>
            <Link
              to="/complaints/new"
              className="mt-3 inline-block font-semibold text-blue-700"
            >
              Submit your first complaint
            </Link>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {complaints.map((complaint) => (
              <Link
                key={complaint.id}
                to={`/complaints/${complaint.id}`}
                className="block rounded-lg border border-slate-200 p-4 hover:border-blue-400 hover:bg-slate-50"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <strong className="text-slate-900">
                    Complaint #{complaint.id}
                  </strong>

                  <span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-800">
                    {(complaint.status || "SUBMITTED").replaceAll("_", " ")}
                  </span>
                </div>

                <p className="mt-3 whitespace-pre-wrap text-slate-700">
                  {complaint.description}
                </p>

                <p className="mt-2 text-sm text-slate-500">
                  Locality: {complaint.locality || "Not provided"}
                </p>

                <p className="mt-1 text-xs text-slate-400">
                  Submitted:{" "}
                  {complaint.created_at
                    ? new Date(complaint.created_at).toLocaleString()
                    : "Not available"}
                </p>

                <p className="mt-3 text-sm font-semibold text-blue-700">
                  View complaint and status history →
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

