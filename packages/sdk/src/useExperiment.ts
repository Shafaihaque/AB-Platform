import {useState, useEffect} from "react";
import { ABPlatform } from '.'

const ab = new ABPlatform("http://localhost:8001", "http://localhost:8081")


function useExperiment(experimentId: string, userId: string) {
  const [variant, setVariant] = useState<string | null>(null)
  useEffect(() => {
    async function fetchVariant() {
      try {
        const res = await ab.assign(experimentId, userId)
        setVariant(res)
      } catch {
        setVariant(null)
      }
    }
    fetchVariant()
  }, [experimentId, userId])

  return variant
}

export default useExperiment

