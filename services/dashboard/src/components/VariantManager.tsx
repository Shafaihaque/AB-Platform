import { useState, useEffect } from "react";
import type { Variant } from "../types";

interface Props {
  experimentId: string;
  experimentStatus: string;
  onUpdate: () => void;
}

export default function VariantManager({ experimentId, experimentStatus, onUpdate }: Props) {
  const [variants, setVariants] = useState<Variant[]>([]);
  const [name, setName] = useState("");
  const [weight, setWeight] = useState("50");
  const [adding, setAdding] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const fetchVariants = () => {
    fetch(`/api/experiments/${experimentId}/variants`)
      .then((res) => res.json())
      .then((data) => setVariants(data));
  };

  useEffect(() => {
    fetchVariants();
  }, [experimentId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);
    await fetch(`/api/experiments/${experimentId}/variants`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, traffic_weight: parseInt(weight) }),
    });
    setName("");
    setWeight("50");
    setShowForm(false);
    setAdding(false);
    fetchVariants();
    onUpdate();
  };

  const isDraft = experimentStatus === "draft";

  return (
    <div className="mt-4 border-t border-gray-100 pt-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-gray-700">Variants</span>
        {isDraft && (
          <button
            onClick={() => setShowForm((v) => !v)}
            className="text-xs font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            {showForm ? "Cancel" : "+ Add Variant"}
          </button>
        )}
      </div>

      <div className="space-y-2 mb-3">
        {variants.map((v) => (
          <div key={v.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
            <span className="text-sm font-medium text-gray-800">{v.name}</span>
            <span className="text-xs text-gray-400">{v.traffic_weight}% traffic</span>
          </div>
        ))}
        {variants.length === 0 && (
          <p className="text-xs text-gray-400">No variants yet.</p>
        )}
      </div>

      {!isDraft && (
        <p className="text-xs text-gray-400">Variants can only be added when the experiment is in draft.</p>
      )}

      {isDraft && showForm && (
        <form onSubmit={handleAdd} className="bg-gray-50 rounded-lg p-3 border border-gray-200 space-y-2">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. control"
              required
              className="block w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Traffic weight (%)</label>
            <input
              type="number"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              min="1"
              max="100"
              required
              className="block w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            disabled={adding}
            className="w-full text-xs font-medium bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            {adding ? "Adding…" : "Add Variant"}
          </button>
        </form>
      )}
    </div>
  );
}
