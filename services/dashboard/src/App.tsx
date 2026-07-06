import { useState } from 'react'
import './App.css'
import ExperimentList from './components/ExperimentList'
import ExperimentResults from './components/ExperimentResults'
import ExperimentCreate from './components/ExperimentCreate'
import type { Experiment } from './types'

function App() {
  const [selected, setSelected] = useState<Experiment | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center gap-3">
        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900 leading-none">AB Platform</h1>
          <p className="text-xs text-gray-400 mt-0.5">Self-serve experimentation</p>
        </div>
      </header>

      <main className="px-8 py-8">
        <div className="grid grid-cols-3 gap-8 max-w-7xl mx-auto">
          <div className="col-span-1 flex flex-col gap-6">
            <ExperimentCreate onCreated={() => setRefreshKey(k => k + 1)} />
            <ExperimentList refreshKey={refreshKey} selectedId={selected?.id ?? null} onSelect={setSelected} />
          </div>
          <div className="col-span-2">
            {selected
              ? <ExperimentResults experimentId={selected.id} experimentName={selected.name} />
              : (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm h-64 flex flex-col items-center justify-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center">
                    <svg className="w-6 h-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                    </svg>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-gray-700">No experiment selected</p>
                    <p className="text-xs text-gray-400 mt-0.5">Click an experiment on the left to view results</p>
                  </div>
                </div>
              )
            }
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
