export type ProductType = 'physical' | 'digital'

export type Product = {
  id: string
  title: string
  seller: string
  category: string
  price: number
  oldPrice: number
  rating: number
  stock: number
  badge: string
  type: ProductType
  image: string
  tags: string[]
}

export type Seller = {
  id: string
  name: string
  badge: string
  score: number
  payout: number
  sla: string
}

export type Order = {
  id: string
  customer: string
  total: number
  status: string
  sellerCount: number
  channel: string
}

export type Campaign = {
  id: string
  name: string
  owner: string
  status: string
  budget: number
  conversion: string
}

export type Provider = {
  id: string
  name: string
  type: string
  status: string
  health: string
}

export type AuditEvent = {
  id: string
  actor: string
  action: string
  time: string
}

export type MarketplaceData = {
  products: Product[]
  sellers: Seller[]
  orders: Order[]
  campaigns: Campaign[]
  providers: Provider[]
  audit: AuditEvent[]
}

export const fallbackData: MarketplaceData = {
  products: [
    {
      id: 'p-1001',
      title: 'LilaBook Pro 14',
      seller: 'Nova Teknoloji',
      category: 'Elektronik / Bilgisayar / Dizustu / Pro',
      price: 42999,
      oldPrice: 46999,
      rating: 4.8,
      stock: 42,
      badge: 'Kurumsal satici',
      type: 'physical',
      image: '/demo-products/lilabook-pro.png',
      tags: ['marka-oncelikli', 'hizli-kargo', 'taksit'],
    },
    {
      id: 'p-1002',
      title: 'AeroRun Mor Spor Ayakkabi',
      seller: 'UrbanStep',
      category: 'Moda / Ayakkabi / Kadin / Spor',
      price: 2399,
      oldPrice: 3199,
      rating: 4.6,
      stock: 128,
      badge: 'Avantajli fiyat',
      type: 'physical',
      image: '/demo-products/aerorun-shoes.png',
      tags: ['kuponlu', 'favori'],
    },
    {
      id: 'p-1003',
      title: 'Pulse Akilli Saat S9',
      seller: 'MarketPlus Official',
      category: 'Elektronik / Giyilebilir / Saat / Akilli',
      price: 6499,
      oldPrice: 7299,
      rating: 4.9,
      stock: 61,
      badge: 'Markanin urunu',
      type: 'physical',
      image: '/demo-products/pulse-watch.png',
      tags: ['marka-oncelikli', 'stokta'],
    },
    {
      id: 'p-1004',
      title: 'Studio X Kablosuz Kulaklik',
      seller: 'SoundLab',
      category: 'Elektronik / Ses / Kulaklik / Bluetooth',
      price: 1899,
      oldPrice: 2499,
      rating: 4.5,
      stock: 214,
      badge: 'Ayni gun kargo',
      type: 'physical',
      image: '/demo-products/studio-headphones.png',
      tags: ['hizli-kargo', 'yorumlu'],
    },
    {
      id: 'p-1005',
      title: 'NextPlay Dijital Oyun Kodu',
      seller: 'DigiKey Store',
      category: 'Dijital / Oyun / Kod / PC',
      price: 799,
      oldPrice: 999,
      rating: 4.7,
      stock: 500,
      badge: 'Dijital teslim',
      type: 'digital',
      image: '/demo-products/nextplay-code.png',
      tags: ['dijital', 'aninda-teslim'],
    },
    {
      id: 'p-1006',
      title: 'Ev Ofis Baslangic Seti',
      seller: 'HomeDesk',
      category: 'Ev / Ofis / Set / Ergonomi',
      price: 3499,
      oldPrice: 4299,
      rating: 4.4,
      stock: 36,
      badge: 'Set urun',
      type: 'physical',
      image: '/demo-products/home-office-set.png',
      tags: ['kampanya', 'kargo'],
    },
  ],
  sellers: [],
  orders: [],
  campaigns: [],
  providers: [],
  audit: [],
}
