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
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold text-gray-900">AB Platform</h1>
      <ExperimentCreate onCreated={() => setRefreshKey(k => k + 1)} />
      <ExperimentList refreshKey={refreshKey} onSelect={setSelected} />
      {selected && <ExperimentResults experimentId={selected.id} experimentName={selected.name} />}
    </div>
  )
}

export default App