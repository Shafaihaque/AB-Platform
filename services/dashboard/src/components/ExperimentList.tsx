import { useState, useEffect } from "react";
import type { Experiment } from "../types";

const STATUS_STYLES: Record<string, string> = {
  running: "bg-green-100 text-green-800",
  draft: "bg-gray-100 text-gray-600",
  stopped: "bg-red-100 text-red-700",
};

interface Props {
  refreshKey: number;
  onSelect: (experiment: Experiment) => void;
}


export default function ExperimentList({ refreshKey, onSelect }: Props) {
  const [experiments, setExperiments] = useState<Experiment[]>([]);


 useEffect(() => {
    fetch("/api/experiments")
      .then((res) => res.json())
      .then((data) => setExperiments(data));
  }, [refreshKey]);

  useEffect(() => {
    fetch("/api/experiments")
      .then((res) => res.json())
      .then((data) => setExperiments(data));
  }, []);

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Experiments</h2>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 divide-y divide-gray-100">
        {experiments.map((experiment) => (
          <div key={experiment.id}   onClick={() => onSelect(experiment)} className="flex items-center justify-between px-6 py-4">
            <div>
              <p className="font-medium text-gray-900">{experiment.name}</p>
              {experiment.description && (
                <p className="text-sm text-gray-500 mt-0.5">{experiment.description}</p>
              )}
            </div>
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_STYLES[experiment.status] ?? "bg-gray-100 text-gray-600"}`}>
              {experiment.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
