import { fallbackData, type MarketplaceData } from './data'

export async function getMarketplaceData(): Promise<MarketplaceData> {
  try {
    const response = await fetch('/api/marketplace')

    if (!response.ok) {
      return fallbackData
    }

    return await response.json()
  } catch {
    return fallbackData
  }
}

export async function createDemoOrder(items: Array<{ id: string; price: number; quantity: number }>) {
  const response = await fetch('/api/orders/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items, paymentProvider: 'Iyzico Sandbox' }),
  })

  if (!response.ok) {
    throw new Error('Demo order could not be created')
  }

  return response.json()
}
