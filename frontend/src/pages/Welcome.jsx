
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Welcome() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        Loading...
      </div>
    );
  }

  if (user) {
    const role = String(user.role || "").toLowerCase();
    const destination =
      role === "admin"
        ? "/admin"
        : role === "official"
          ? "/official"
          : "/dashboard";

    return <Navigate to={destination} replace />;
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-6 py-5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-700 text-xl font-bold text-white">
            C
          </div>
          <div>
            <p className="text-lg font-bold text-slate-900">
              AI Civic Complaint Router
            </p>
            <p className="text-sm text-slate-500">
              CivicConnect
            </p>
          </div>
        </div>
      </header>

      <main className="flex flex-1 items-center">
        <div className="mx-auto grid w-full max-w-6xl gap-12 px-6 py-16 md:grid-cols-2 md:items-center">
          <section>
            <p className="font-semibold uppercase tracking-widest text-blue-700">
              Smarter civic services
            </p>

            <h1 className="mt-5 text-4xl font-bold leading-tight text-slate-900 md:text-5xl">
              Speak Up.
              <br />
              Get heard.
              <br />
              Track actions.
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
              Submit municipal complaints, get them routed to the
              appropriate department using AI, and track their
              progress from submission to resolution.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                to="/login"
                className="rounded-lg bg-white-700 px-6 py-3 font-semibold text-white hover:bg-blue-800"
              >
                Login
              </Link>

              <Link
                to="/register"
                className="rounded-lg border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-800 hover:bg-slate-100"
              >
                Register
              </Link>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="text-xl font-bold text-slate-900">
              How it works
            </h2>

            <div className="mt-6 space-y-6">
              {[
                {
                  number: "01",
                  title: "Submit a complaint",
                  description:
                    "Describe the civic issue and provide its locality.",
                },
                {
                  number: "02",
                  title: "AI-assisted routing",
                  description:
                    "The system predicts the responsible municipal department.",
                },
                {
                  number: "03",
                  title: "Track progress",
                  description:
                    "Follow status updates until the complaint is resolved.",
                },
              ].map((item) => (
                <div key={item.number} className="flex gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 font-bold text-blue-700">
                    {item.number}
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">
                      {item.title}
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white px-6 py-5 text-center text-sm text-slate-500">
        AI Civic Complaint Router · Municipal complaint management
      </footer>
    </div>
  );
}


