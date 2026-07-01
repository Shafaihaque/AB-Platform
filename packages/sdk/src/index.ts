export class ABPlatform {
  private apiUrl: string
  private ingestUrl: string

  constructor(apiUrl: string, ingestUrl: string) {
    this.apiUrl = apiUrl
    this.ingestUrl = ingestUrl
  }

  async assign(experimentId: string, userId: string): Promise<string | null> {
    try {
      const res = await fetch(`${this.apiUrl}/assign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ experiment_id: experimentId, user_id: userId }),
      })
      const data = await res.json()
      return data.variant_name ?? null
    } catch {
      return null
    }
  }

  async track(experimentId: string, variantId: string, userId: string, eventType: "exposure" | "conversion"): Promise<void> {
    try {
      await fetch(`${this.apiUrl}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          experiment_id: experimentId,
          variant_id: variantId,
          user_id: userId,
          event_type: eventType,
        }),
      })
    } catch {
      // silent
    }
  }
}
