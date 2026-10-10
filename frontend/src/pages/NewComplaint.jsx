
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";

export default function NewComplaint() {
  const navigate = useNavigate();

  const [description, setDescription] = useState("");
  const [locality, setLocality] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (description.trim().length < 10) {
      setError("Please enter at least 10 characters.");
      return;
    }

    setBusy(true);

    try {
      const response = await api.post("/api/complaints/", {
        description: description.trim(),
        locality: locality.trim() || null,
      });

      navigate(`/complaints/${response.data.id}`);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not submit your complaint. Please try again."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        to="/dashboard"
        className="text-sm font-medium text-blue-700"
      >
        ← Back to dashboard
      </Link>

      <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">
          New report
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Submit a complaint
        </h1>

        <p className="mt-3 text-slate-500">
          Describe the municipal issue clearly. The system will
          classify it and assign an initial priority.
        </p>

        {error && (
          <div role="alert" className="mt-6 rounded-lg bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-7 space-y-6">
          <div>
            <label className="mb-2 block font-medium text-slate-800">
              Complaint description *
            </label>

            <textarea
              required
              minLength={10}
              maxLength={5000}
              rows={7}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the issue, where it occurred, and any relevant details..."
              className="w-full resize-y rounded-xl border border-slate-300 px-4 py-3"
            />

            <p className="mt-2 text-right text-xs text-slate-500">
              {description.length}/5000 characters
            </p>
          </div>

          <div>
            <label className="mb-2 block font-medium text-slate-800">
              Locality or area
            </label>

            <input
              type="text"
              maxLength={150}
              value={locality}
              onChange={(e) => setLocality(e.target.value)}
              placeholder="e.g. Sector 12"
              className="w-full rounded-xl border border-slate-300 px-4 py-3"
            />

            <p className="mt-2 text-xs text-slate-500">
              Locality helps identify potentially related complaints.
            </p>
          </div>


          <div className="flex flex-wrap gap-3">
            <button
              disabled={busy}
              className="rounded-lg bg-blue-700 px-5 py-3 font-semibold text-white hover:bg-blue-800 disabled:opacity-60"
            >
              {busy ? "Processing..." : "Submit complaint"}
            </button>

            <Link
              to="/dashboard"
              className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
