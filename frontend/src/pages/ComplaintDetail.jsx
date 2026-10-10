
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../api";

export default function ComplaintDetail() {
  const { id } = useParams();

  const [complaint, setComplaint] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [complaintResponse, historyResponse] = await Promise.all([
          api.get(`/api/complaints/${id}`),
          api.get(`/api/complaints/${id}/history`),
        ]);

        if (active) {
          setComplaint(complaintResponse.data);
          setHistory(historyResponse.data);
        }
      } catch (err) {
        if (active) {
          setError(
            err.response?.data?.detail ||
              "Could not load complaint details."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [id]);

  if (loading) {
    return <p>Loading complaint...</p>;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <p role="alert" className="rounded-lg bg-red-50 p-4 text-red-700">
          {error}
        </p>
        <Link to="/dashboard" className="font-semibold text-blue-700">
          Back to my complaints
        </Link>
      </div>
    );
  }

  if (!complaint) {
    return <p>Complaint not found.</p>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link
        to="/dashboard"
        className="text-sm font-semibold text-blue-700"
      >
        ← Back to my complaints
      </Link>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold text-slate-900">
            Complaint #{complaint.id}
          </h1>

          <span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-800">
            {(complaint.status || "SUBMITTED").replaceAll("_", " ")}
          </span>
        </div>

        <h2 className="mt-6 font-semibold text-slate-900">
          Complaint description
        </h2>

        <p className="mt-2 whitespace-pre-wrap text-slate-700">
          {complaint.description}
        </p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm text-slate-500">Locality</p>
            <p className="mt-1 text-slate-800">
              {complaint.locality || "Not provided"}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">Date submitted</p>
            <p className="mt-1 text-slate-800">
              {complaint.created_at
                ? new Date(complaint.created_at).toLocaleString()
                : "Not available"}
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-bold text-slate-900">
          Status history
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Follow the progress of your complaint over time.
        </p>

        {history.length === 0 ? (
          <p className="mt-4 text-slate-500">
            No status history records are available yet.
          </p>
        ) : (
          <ol className="mt-6 space-y-5">
            {history.map((item) => (
              <li
                key={item.id}
                className="border-l-2 border-blue-200 pl-4"
              >
                <p className="font-semibold text-slate-900">
                  {(item.status || "").replaceAll("_", " ")}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  {item.created_at
                    ? new Date(item.created_at).toLocaleString()
                    : ""}
                </p>

                {item.comment && (
                  <p className="mt-2 text-slate-700">
                    {item.comment}
                  </p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}

