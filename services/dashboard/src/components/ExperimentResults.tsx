import { useState, useEffect } from "react";
import type {  ExperimentResult } from "../types";

interface Props {
  experimentId: string
  experimentName: string
}

export default function ExperimentResults({ experimentId, experimentName }: Props) {
  const [result, setResult] = useState<ExperimentResult | null>(null);

  useEffect(() => {
    fetch(`/api/results/${experimentId}`)
      .then((res) => res.json())
      .then((data) => setResult(data));
  }, [experimentId]);

if (!result) return <p>Loading...</p>

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Experiment Results</h2>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 divide-y divide-gray-100">
        {result && (
          <div key={result.experiment_id} className="px-6 py-4">
            <p className="font-medium text-gray-900">{experimentName}</p>
            <p className="text-sm text-gray-500 mt-0.5">P-value: {result.p_value != null ? result.p_value.toFixed(4) : "N/A"}</p>
            <p className="text-sm text-gray-500 mt-0.5">Significant: {result.significant ? "Yes" : "No"}</p>
            <p className="text-sm text-gray-500 mt-0.5">Winner: {result.winner ?? "N/A"}</p>
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Variants</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                {(result.variants ?? []).map((variant) => (                  <div key={variant.variant_id} className="flex justify-between items-center mb-2">
                    <p className="text-sm text-gray-600">{variant.variant_name}</p>
                    <p className="text-sm text-gray-600">Users: {variant.users}</p>
                    <p className="text-sm text-gray-600">Conversions: {variant.conversions}</p>
                    <p className="text-sm text-gray-600">Conversion Rate: {(variant.conversion_rate * 100).toFixed(2)}%</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )} 
      </div>
    </div>
  ); }