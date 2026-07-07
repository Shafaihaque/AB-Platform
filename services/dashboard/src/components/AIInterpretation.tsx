import { useState } from 'react';

interface Props {
  experimentId: string;
}

export default function AIInterpretation({ experimentId }: Props) {
  const [interpretation, setInterpretation] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchInterpretation = async () => {
    setLoading(true);
    setInterpretation(null);
    setError(null);
    try {
      const response = await fetch(`/api/results/${experimentId}/interpret`);
      if (!response.ok) {
        throw new Error('Failed to fetch AI interpretation');
      }
      const data = await response.json();
      setInterpretation(data.interpretation);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-4 border-t border-gray-100 pt-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
          <span className="text-sm font-semibold text-gray-700">AI Analysis</span>
        </div>
        <button
          onClick={fetchInterpretation}
          disabled={loading}
          className="text-xs font-medium bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
        >
          {loading ? 'Analyzing…' : 'Analyze with AI'}
        </button>
      </div>

      {!interpretation && !error && !loading && (
        <p className="text-xs text-gray-400">Click to get a plain-English summary and ship recommendation.</p>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}

      {interpretation && (
        <div className="bg-indigo-50 rounded-lg px-4 py-3">
          <p className="text-sm text-gray-700 leading-relaxed">{interpretation}</p>
          <p className="text-xs text-indigo-400 mt-2">Powered by Claude</p>
        </div>
      )}
    </div>
  );
}
