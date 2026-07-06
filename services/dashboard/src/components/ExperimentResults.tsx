import { useState, useEffect } from "react";
import type { ExperimentResult } from "../types";

interface Props {
  experimentId: string
  experimentName: string
}

export default function ExperimentResults({ experimentId, experimentName }: Props) {
  const [result, setResult] = useState<ExperimentResult | null>(null);

  useEffect(() => {
    setResult(null);
    fetch(`/api/results/${experimentId}`)
      .then((res) => res.json())
      .then((data) => setResult(data));
  }, [experimentId]);

  if (!result) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-400">
          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-sm">Loading results…</span>
        </div>
      </div>
    );
  }

  const variants = result.variants ?? [];
  const winner = variants.find(v => v.variant_name === result.winner);
  const totalUsers = variants.reduce((sum, v) => sum + v.users, 0);
  const maxRate = Math.max(...variants.map(v => v.conversion_rate), 0.01);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-100">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{experimentName}</h2>
            <p className="text-sm text-gray-500 mt-0.5">{totalUsers.toLocaleString()} total users</p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-xs text-gray-400 mb-0.5">p-value</p>
            <p className="text-sm font-mono font-semibold text-gray-700">
              {result.p_value != null ? result.p_value.toFixed(4) : "N/A"}
            </p>
          </div>
        </div>
      </div>

      {result.significant && winner ? (
        <div className="px-6 py-3 bg-green-50 border-b border-green-100 flex items-center gap-2.5">
          <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center shrink-0">
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-sm text-green-800">
            <span className="font-semibold">{winner.variant_name}</span> wins with{" "}
            <span className="font-semibold">{(winner.conversion_rate * 100).toFixed(1)}%</span> conversion —{" "}
            statistically significant
          </p>
        </div>
      ) : (
        <div className="px-6 py-3 bg-amber-50 border-b border-amber-100 flex items-center gap-2.5">
          <div className="w-5 h-5 rounded-full bg-amber-400 flex items-center justify-center shrink-0">
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01" />
            </svg>
          </div>
          <p className="text-sm text-amber-800">Not statistically significant yet — keep collecting data</p>
        </div>
      )}

      <div className="px-6 py-5 space-y-4">
        {variants.map((variant) => {
          const isWinner = variant.variant_name === result.winner;
          const barWidth = (variant.conversion_rate / maxRate) * 100;
          return (
            <div key={variant.variant_id} className={`rounded-lg p-4 border ${isWinner ? "border-green-200 bg-green-50" : "border-gray-100 bg-gray-50"}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-gray-800">{variant.variant_name}</p>
                  {isWinner && (
                    <span className="text-xs font-medium bg-green-200 text-green-800 px-1.5 py-0.5 rounded">winner</span>
                  )}
                </div>
                <p className={`text-xl font-bold ${isWinner ? "text-green-700" : "text-gray-700"}`}>
                  {(variant.conversion_rate * 100).toFixed(1)}%
                </p>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2.5">
                <div
                  className={`h-1.5 rounded-full transition-all ${isWinner ? "bg-green-500" : "bg-indigo-400"}`}
                  style={{ width: `${barWidth.toFixed(1)}%` }}
                />
              </div>
              <p className="text-xs text-gray-400">
                {variant.users.toLocaleString()} users &middot; {variant.conversions.toLocaleString()} conversions
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
