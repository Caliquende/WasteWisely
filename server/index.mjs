import cors from 'cors'
import express from 'express'

const app = express()
const port = process.env.PORT || 4000

app.use(cors())
app.use(express.json({ limit: '2mb' }))

const productImages = [
  '/demo-products/lilabook-pro.png',
  '/demo-products/aerorun-shoes.png',
  '/demo-products/pulse-watch.png',
  '/demo-products/studio-headphones.png',
  '/demo-products/nextplay-code.png',
  '/demo-products/home-office-set.png',
  '/demo-products/smart-tv.png',
  '/demo-products/coffee-maker.png',
  '/demo-products/skin-care.png',
  '/demo-products/ebook-bundle.png',
  '/demo-products/travel-bag.png',
  '/demo-products/kids-tablet.png',
]

const data = {
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
      image: productImages[0],
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
      image: productImages[1],
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
      image: productImages[2],
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
      image: productImages[3],
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
      image: productImages[4],
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
      image: productImages[5],
      tags: ['kampanya', 'kargo'],
    },
    {
      id: 'p-1007',
      title: 'LumaVision 55 Smart TV',
      seller: 'MarketPlus Official',
      category: 'Elektronik / Televizyon / Smart TV / 55 Inc',
      price: 28999,
      oldPrice: 32999,
      rating: 4.6,
      stock: 24,
      badge: 'Markanin urunu',
      type: 'physical',
      image: productImages[6],
      tags: ['marka-oncelikli', 'kurulum'],
    },
    {
      id: 'p-1008',
      title: 'Barista Mini Kahve Makinesi',
      seller: 'KitchenPro',
      category: 'Ev / Mutfak / Kahve / Espresso',
      price: 5499,
      oldPrice: 6899,
      rating: 4.5,
      stock: 73,
      badge: 'Kuponlu urun',
      type: 'physical',
      image: productImages[7],
      tags: ['kuponlu', 'kampanya'],
    },
    {
      id: 'p-1009',
      title: 'Lila Glow Cilt Bakim Seti',
      seller: 'BeautyLab',
      category: 'Kozmetik / Cilt Bakimi / Set / Nemlendirme',
      price: 1299,
      oldPrice: 1799,
      rating: 4.3,
      stock: 155,
      badge: 'Cok satan',
      type: 'physical',
      image: productImages[8],
      tags: ['favori', 'yorumlu'],
    },
    {
      id: 'p-1010',
      title: 'Growth Pro Ebook Paketi',
      seller: 'DigiKey Store',
      category: 'Dijital / Kitap / Egitim / Paket',
      price: 349,
      oldPrice: 499,
      rating: 4.8,
      stock: 900,
      badge: 'Dijital teslim',
      type: 'digital',
      image: productImages[9],
      tags: ['dijital', 'aninda-teslim'],
    },
    {
      id: 'p-1011',
      title: 'Urban Travel Kabin Boy Valiz',
      seller: 'UrbanStep',
      category: 'Moda / Aksesuar / Valiz / Kabin',
      price: 3199,
      oldPrice: 3999,
      rating: 4.4,
      stock: 48,
      badge: 'Hizli kargo',
      type: 'physical',
      image: productImages[10],
      tags: ['hizli-kargo', 'stokta'],
    },
    {
      id: 'p-1012',
      title: 'Kids Learn Tablet Mini',
      seller: 'EduToys',
      category: 'Elektronik / Tablet / Cocuk / Egitim',
      price: 4599,
      oldPrice: 5299,
      rating: 4.2,
      stock: 82,
      badge: 'Aile secimi',
      type: 'physical',
      image: productImages[11],
      tags: ['kampanya', 'yorumlu'],
    },
  ],
  sellers: [
    { id: 's-1', name: 'MarketPlus Official', badge: 'Kendi marka', score: 98, payout: 842000, sla: '99.94%' },
    { id: 's-2', name: 'Nova Teknoloji', badge: 'Kurumsal', score: 94, payout: 412500, sla: '99.81%' },
    { id: 's-3', name: 'UrbanStep', badge: 'Onayli', score: 91, payout: 188300, sla: '99.62%' },
  ],
  orders: [
    { id: 'MP-84021', customer: 'Selin A.', total: 49498, status: 'Odeme onaylandi', sellerCount: 2, channel: 'Web' },
    { id: 'MP-84022', customer: 'Can K.', total: 799, status: 'Dijital teslim edildi', sellerCount: 1, channel: 'Web' },
    { id: 'MP-84023', customer: 'Merve D.', total: 5898, status: 'Iade incelemede', sellerCount: 2, channel: 'Destek' },
  ],
  campaigns: [
    { id: 'c-1', name: 'Mor Cuma teknoloji vitrini', owner: 'Marketing', status: 'Aktif', budget: 280000, conversion: '7.8%' },
    { id: 'c-2', name: 'Kurumsal satici rozeti', owner: 'Admin', status: 'Taslak', budget: 0, conversion: '-' },
    { id: 'c-3', name: 'Dijital urun aninda teslim', owner: 'Satici', status: 'Aktif', budget: 45000, conversion: '5.2%' },
  ],
  providers: [
    { id: 'pay-1', name: 'Iyzico Sandbox', type: 'Odeme', status: 'Sandbox', health: 'Hazir' },
    { id: 'ship-1', name: 'Kargo adapter', type: 'Kargo', status: 'Mock', health: 'Baglanti bekliyor' },
    { id: 'invoice-1', name: 'E-fatura adapter', type: 'Fatura', status: 'Mock', health: 'Saglayici secilecek' },
    { id: 'notify-1', name: 'SMS / E-posta', type: 'Bildirim', status: 'Sandbox', health: 'Hazir' },
  ],
  audit: [
    { id: 'a-1', actor: 'Admin', action: 'Odeme saglayici sirasi guncellendi', time: '09:24' },
    { id: 'a-2', actor: 'Marketing', action: 'Mor Cuma banneri yayinlandi', time: '10:12' },
    { id: 'a-3', actor: 'Destek', action: 'MP-84023 iade incelemesi baslatildi', time: '11:03' },
  ],
}

app.get('/api/health', (_request, response) => {
  response.json({ ok: true, service: 'new-marketplace-demo-api' })
})

app.get('/api/marketplace', (_request, response) => {
  response.json(data)
})

app.post('/api/orders/checkout', (request, response) => {
  const { items = [], paymentProvider = 'Iyzico Sandbox' } = request.body
  const total = items.reduce((sum, item) => sum + Number(item.price || 0) * Number(item.quantity || 1), 0)

  response.status(201).json({
    id: `MP-${Math.floor(90000 + Math.random() * 9999)}`,
    status: 'Demo siparis olusturuldu',
    paymentProvider,
    total,
    mode: 'sandbox',
  })
})

app.listen(port, () => {
  console.log(`new-marketplace demo API listening on http://localhost:${port}`)
})
