"use client";
// Next.js (App Router). Set NEXT_PUBLIC_API=http://localhost:8000 in .env.local
import { useEffect, useState } from "react";

type Result = {
  strategy: string;
  roads_fixed: string[];
  spent: number;
  unspent: number;
  harm_avoided_pct: number;
  complaints_resolved: number;
  impact_per_lakh: number;
};
type Data = { winner: string; uplift_vs_best_baseline_pct: number; results: Result[] };

const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8000";

export default function StrategyComparison() {
  const [budget, setBudget] = useState(200);
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/api/strategy-comparison`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ budget }),
        });
        if (!res.ok) throw new Error(`API returned ${res.status}`);
        setData(await res.json());
        setError("");
      } catch (e) {
        setError("Could not reach the API. Start it with: uvicorn main:app --port 8000");
      }
    }, 200); // debounce slider
    return () => clearTimeout(t);
  }, [budget]);

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: 24, fontFamily: "system-ui" }}>
      <h1>Budget smarts: same budget, three strategies</h1>
      <p>Spending the same money three ways shows which plan avoids the most harm.</p>

      <label>
        Budget: <b>₹ {budget} lakh</b>
        <input
          type="range" min={50} max={500} step={10} value={budget}
          onChange={(e) => setBudget(+e.target.value)}
          style={{ width: "100%" }}
        />
      </label>

      {error && <p role="alert" style={{ color: "crimson" }}>{error}</p>}

      {data && (
        <>
          <p>
            <b>{data.winner}</b> wins, avoiding{" "}
            <b>{data.uplift_vs_best_baseline_pct} points</b> more harm than the best alternative.
          </p>
          <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))" }}>
            {data.results.map((r) => (
              <section key={r.strategy}
                style={{ border: `2px solid ${r.strategy === data.winner ? "#0a8" : "#ccc"}`, borderRadius: 12, padding: 16 }}>
                <h2 style={{ fontSize: 18 }}>{r.strategy}</h2>
                <div style={{ background: "#eee", borderRadius: 6, height: 12 }}>
                  <div style={{ width: `${r.harm_avoided_pct}%`, height: "100%", borderRadius: 6,
                    background: r.strategy === data.winner ? "#0a8" : "#59f", transition: "width .3s" }} />
                </div>
                <p><b>{r.harm_avoided_pct}%</b> of harm avoided</p>
                <p>{r.complaints_resolved} complaints resolved · ₹ {r.spent} lakh spent</p>
                <small>{r.roads_fixed.join(", ") || "No road fits the budget"}</small>
              </section>
            ))}
          </div>
        </>
      )}
    </main>
  );
}
