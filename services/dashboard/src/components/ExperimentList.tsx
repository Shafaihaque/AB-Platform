import { useState, useEffect } from "react";
import type { Experiment } from "../types";

const STATUS_STYLES: Record<string, string> = {
  running: "bg-green-100 text-green-700",
  draft: "bg-gray-100 text-gray-500",
  stopped: "bg-red-100 text-red-600",
  paused: "bg-yellow-100 text-yellow-700",
};

interface Props {
  refreshKey: number;
  selectedId: string | null;
  onSelect: (experiment: Experiment) => void;
}

export default function ExperimentList({ refreshKey, selectedId, onSelect }: Props) {
  const [experiments, setExperiments] = useState<Experiment[]>([]);

  useEffect(() => {
    fetch("/api/experiments")
      .then((res) => res.json())
      .then((data) => setExperiments(data));
  }, [refreshKey]);

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Experiments</h2>
        <span className="text-xs text-gray-400">{experiments.length} total</span>
      </div>

      {experiments.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 p-6 text-center">
          <p className="text-sm text-gray-400">No experiments yet</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {experiments.map((experiment) => (
            <div
              key={experiment.id}
              onClick={() => onSelect(experiment)}
              className={`flex items-start justify-between px-4 py-3.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 ${
                selectedId === experiment.id
                  ? "bg-indigo-50 border-l-[3px] border-l-indigo-500"
                  : "hover:bg-gray-50"
              }`}
            >
              <div className="min-w-0 pr-3">
                <p className="text-sm font-medium text-gray-900 truncate">{experiment.name}</p>
                {experiment.description && (
                  <p className="text-xs text-gray-400 mt-0.5 truncate">{experiment.description}</p>
                )}
              </div>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 mt-0.5 ${STATUS_STYLES[experiment.status] ?? "bg-gray-100 text-gray-500"}`}>
                {experiment.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
