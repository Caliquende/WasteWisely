import { useEffect, useMemo, useState, type ChangeEvent, type ReactNode } from 'react'
import { createDemoOrder, getMarketplaceData } from './api'
import { copy, type Copy, type Lang } from './i18n'
import type { Campaign, MarketplaceData, Product, Provider, Seller } from './data'
import './App.css'

type Page = 'musteri' | 'admin' | 'satici1' | 'satici2' | 'marketing1' | 'marketing2' | 'finans1' | 'finans2' | 'destek1' | 'destek2'
type SortMode = 'priority' | 'priceAsc' | 'rating'
type LogoSlot = 'admin' | 'marketing'
type CartLine = Product & { quantity: number }

const routePaths: Record<Page, string> = {
  musteri: '/musteri',
  admin: '/admin',
  satici1: '/satici1',
  satici2: '/satici2',
  marketing1: '/marketing1',
  marketing2: '/marketing2',
  finans1: '/finans1',
  finans2: '/finans2',
  destek1: '/destek1',
  destek2: '/destek2',
}

const pages = Object.keys(routePaths) as Page[]

function pageFromPath(pathname: string): Page {
  const normalizedPath = pathname === '/' ? '/musteri' : pathname
  return pages.find((page) => routePaths[page] === normalizedPath) ?? 'musteri'
}

function productSlugFromPath(pathname: string) {
  const normalizedPath = pathname.replace(/\/+$/, '') || '/'
  const knownPaths = ['/', ...Object.values(routePaths)]
  if (knownPaths.includes(normalizedPath)) return null

  return decodeURIComponent(normalizedPath.slice(1))
}

function slugifyProductTitle(title: string) {
  return title
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('en-US')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function productPath(product: Product) {
  return `/${slugifyProductTitle(product.title)}`
}

function App() {
  const [pathName, setPathName] = useState(() => window.location.pathname)
  const [lang, setLang] = useState<Lang>('en')
  const [data, setData] = useState<MarketplaceData | null>(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('Tumu')
  const [sortMode, setSortMode] = useState<SortMode>('priority')
  const [cart, setCart] = useState<CartLine[]>([])
  const [favorites, setFavorites] = useState<string[]>(['p-1003'])
  const [compare, setCompare] = useState<string[]>([])
  const [checkoutStatus, setCheckoutStatus] = useState<string>(copy.en.store.checkoutWaiting)
  const [adminLogo, setAdminLogo] = useState(() => localStorage.getItem('adminLogo') || '')
  const [marketingLogo, setMarketingLogo] = useState(() => localStorage.getItem('marketingLogo') || '')
  const [logoError, setLogoError] = useState('')

  const t = copy[lang]
  const page = useMemo(() => pageFromPath(pathName), [pathName])
  const productSlug = productSlugFromPath(pathName)
  const activePage = t.pages[page]
  const money = useMemo(
    () =>
      new Intl.NumberFormat(lang === 'tr' ? 'tr-TR' : 'en-US', {
        style: 'currency',
        currency: 'TRY',
        maximumFractionDigits: 0,
      }),
    [lang],
  )

  useEffect(() => {
    getMarketplaceData().then(setData)
  }, [])

  useEffect(() => {
    const handlePopState = () => setPathName(window.location.pathname)
    window.addEventListener('popstate', handlePopState)

    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const products = useMemo(() => data?.products ?? [], [data])
  const categoryOptions = useMemo(() => {
    const roots = products.map((product) => product.category.split('/')[0].trim())
    return ['Tumu', ...Array.from(new Set(roots))]
  }, [products])

  const visibleProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase(lang === 'tr' ? 'tr-TR' : 'en-US')

    return products
      .filter((product) => {
        const categoryMatch = category === 'Tumu' || product.category.startsWith(category)
        const queryMatch =
          !normalizedQuery ||
          `${product.title} ${product.seller} ${product.category} ${product.tags.join(' ')}`
            .toLocaleLowerCase(lang === 'tr' ? 'tr-TR' : 'en-US')
            .includes(normalizedQuery)

        return categoryMatch && queryMatch
      })
      .sort((first, second) => {
        if (sortMode === 'priceAsc') return first.price - second.price
        if (sortMode === 'rating') return second.rating - first.rating

        const firstPriority = first.tags.includes('marka-oncelikli') ? 1 : 0
        const secondPriority = second.tags.includes('marka-oncelikli') ? 1 : 0
        return secondPriority - firstPriority || second.rating - first.rating
      })
  }, [category, lang, products, query, sortMode])

  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
  const selectedCompare = products.filter((product) => compare.includes(product.id))
  const isCustomerPage = page === 'musteri'
  const productPageProduct = productSlug ? products.find((product) => slugifyProductTitle(product.title) === productSlug) : null
  const isProductRoute = Boolean(productSlug)
  const pageTitle = productPageProduct?.title ?? (isProductRoute ? t.detail.productNotFound : activePage.title)

  function navigateTo(path: string) {
    window.history.pushState({}, '', path)
    setPathName(window.location.pathname)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function openProduct(product: Product) {
    navigateTo(productPath(product))
  }

  function openStorefront() {
    navigateTo('/')
  }

  function selectCategory(nextCategory: string) {
    setCategory(nextCategory)
    if (isProductRoute) {
      openStorefront()
    }
  }

  function addToCart(product: Product) {
    setCart((current) => {
      const existing = current.find((item) => item.id === product.id)
      if (existing) {
        return current.map((item) => (item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item))
      }
      return [...current, { ...product, quantity: 1 }]
    })
    setCheckoutStatus(`${product.title} ${t.store.addedToCart}`)
  }

  function toggleFavorite(id: string) {
    setFavorites((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]))
  }

  function toggleCompare(id: string) {
    setCompare((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id)
      return [...current.slice(-2), id]
    })
  }

  async function checkout() {
    if (cart.length === 0) {
      setCheckoutStatus(t.store.cartEmptyStatus)
      return
    }

    setCheckoutStatus(t.store.checkoutProcessing)

    try {
      const order = await createDemoOrder(cart.map((item) => ({ id: item.id, price: item.price, quantity: item.quantity })))
      setCheckoutStatus(`${order.id} - ${displayPhrase(order.status, t)}`)
      setCart([])
    } catch {
      setCheckoutStatus(t.store.checkoutLocalDone)
      setCart([])
    }
  }

  function handleLogoUpload(slot: LogoSlot, event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    setLogoError('')

    if (!file) return

    if (file.type !== 'image/png') {
      setLogoError(t.dashboard.pngOnly)
      event.target.value = ''
      return
    }

    if (file.size > 512 * 1024) {
      setLogoError(t.dashboard.pngSize)
      event.target.value = ''
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      const value = String(reader.result)
      if (slot === 'admin') {
        setAdminLogo(value)
        localStorage.setItem('adminLogo', value)
      } else {
        setMarketingLogo(value)
        localStorage.setItem('marketingLogo', value)
      }
    }
    reader.readAsDataURL(file)
  }

  function removeLogo(slot: LogoSlot) {
    if (slot === 'admin') {
      setAdminLogo('')
      localStorage.removeItem('adminLogo')
    } else {
      setMarketingLogo('')
      localStorage.removeItem('marketingLogo')
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label={isCustomerPage ? t.categoriesTitle : activePage.group}>
        <div className="brand-lockup">
          <div className="brand-mark">NM</div>
          <div>
            <strong>New Marketplace</strong>
            <span>{isCustomerPage ? t.brandSubtitle : t.panelSubtitle}</span>
          </div>
        </div>

        <LanguageToggle lang={lang} setLang={setLang} />

        {isCustomerPage ? (
          <nav className="nav-list category-nav">
            {categoryOptions.map((item) => (
              <button
                key={item}
                className={category === item ? 'active' : ''}
                onClick={() => selectCategory(item)}
                type="button"
              >
                <span className="nav-dot" aria-hidden="true" />
                {formatCategoryRoot(item, t)}
              </button>
            ))}
          </nav>
        ) : (
          <div className="panel-url-box">
            <span>{routePaths[page]}</span>
            <strong>{activePage.title}</strong>
            <p>{t.directUrlOnly}</p>
          </div>
        )}

        <div className="handoff-box">
          <span>{t.handoffTitle}</span>
          <strong>{t.handoffStrong}</strong>
          <p>{t.handoffBody}</p>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">
              {activePage.group} {t.useCaseLabel}
            </span>
            <h1>{pageTitle}</h1>
          </div>
          <div className="topbar-actions">
            <div className="signal">
              <span>{t.api}</span>
              <strong>{data ? t.ready : t.loading}</strong>
            </div>
            <div className="signal">
              <span>{t.cart}</span>
              <strong>
                {cart.length} {t.itemCount}
              </strong>
            </div>
          </div>
        </header>

        {page === 'musteri' && productSlug && (
          <ProductRoute
            product={productPageProduct}
            products={products}
            favorites={favorites}
            compare={compare}
            money={money}
            t={t}
            onAddToCart={addToCart}
            onFavorite={toggleFavorite}
            onCompare={toggleCompare}
            onOpenProduct={openProduct}
            onBack={openStorefront}
          />
        )}

        {page === 'musteri' && !productSlug && (
          <Storefront
            products={visibleProducts}
            categories={categoryOptions}
            category={category}
            query={query}
            sortMode={sortMode}
            cart={cart}
            cartTotal={cartTotal}
            favorites={favorites}
            compare={compare}
            selectedCompare={selectedCompare}
            checkoutStatus={checkoutStatus}
            money={money}
            t={t}
            onCategoryChange={selectCategory}
            onQueryChange={setQuery}
            onSortChange={setSortMode}
            onAddToCart={addToCart}
            onFavorite={toggleFavorite}
            onCompare={toggleCompare}
            onOpenProduct={openProduct}
            onCheckout={checkout}
          />
        )}

        {page === 'admin' && data && (
          <AdminDashboard data={data} logo={adminLogo} logoError={logoError} t={t} onLogoUpload={(event) => handleLogoUpload('admin', event)} onRemoveLogo={() => removeLogo('admin')} />
        )}
        {page === 'satici1' && data && <SellerDashboard products={products} sellers={data.sellers} variant="catalog" money={money} t={t} />}
        {page === 'satici2' && data && <SellerDashboard products={products} sellers={data.sellers} variant="performance" money={money} t={t} />}
        {page === 'marketing1' && data && (
          <MarketingDashboard
            campaigns={data.campaigns}
            logo={marketingLogo}
            logoError={logoError}
            t={t}
            money={money}
            onLogoUpload={(event) => handleLogoUpload('marketing', event)}
            onRemoveLogo={() => removeLogo('marketing')}
            variant="campaign"
          />
        )}
        {page === 'marketing2' && data && (
          <MarketingDashboard
            campaigns={data.campaigns}
            logo={marketingLogo}
            logoError={logoError}
            t={t}
            money={money}
            onLogoUpload={(event) => handleLogoUpload('marketing', event)}
            onRemoveLogo={() => removeLogo('marketing')}
            variant="seo"
          />
        )}
        {page === 'finans1' && data && <FinanceDashboard data={data} variant="payments" money={money} t={t} />}
        {page === 'finans2' && data && <FinanceDashboard data={data} variant="payouts" money={money} t={t} />}
        {page === 'destek1' && data && <SupportDashboard data={data} variant="orders" t={t} />}
        {page === 'destek2' && data && <SupportDashboard data={data} variant="live" t={t} />}
      </section>
    </main>
  )
}

function LanguageToggle({ lang, setLang }: { lang: Lang; setLang: (lang: Lang) => void }) {
  return (
    <div className="language-toggle" aria-label="Language switcher">
      <button className={lang === 'en' ? 'active' : ''} type="button" onClick={() => setLang('en')}>
        EN
      </button>
      <button className={lang === 'tr' ? 'active' : ''} type="button" onClick={() => setLang('tr')}>
        TR
      </button>
    </div>
  )
}

function Storefront(props: {
  products: Product[]
  categories: string[]
  category: string
  query: string
  sortMode: SortMode
  cart: CartLine[]
  cartTotal: number
  favorites: string[]
  compare: string[]
  selectedCompare: Product[]
  checkoutStatus: string
  money: Intl.NumberFormat
  t: Copy
  onCategoryChange: (value: string) => void
  onQueryChange: (value: string) => void
  onSortChange: (value: SortMode) => void
  onAddToCart: (product: Product) => void
  onFavorite: (id: string) => void
  onCompare: (id: string) => void
  onOpenProduct: (product: Product) => void
  onCheckout: () => void
}) {
  const slides = useMemo(() => {
    return props.products.slice(0, 4).map((product, index) => ({
      id: product.id,
      eyebrow: index === 0 ? props.t.hero.eyebrow : product.type === 'digital' ? props.t.hero.digitalSlideTitle : props.t.hero.defaultSlideTitle,
      title: index === 0 ? props.t.hero.mainTitle : product.type === 'digital' ? props.t.hero.digitalSlideTitle : `${product.seller} deals`,
      description: index === 0 ? props.t.hero.mainDescription : `${product.title}: ${props.t.hero.defaultSlideDescription}`,
      cta: index === 0 ? props.t.hero.primaryCta : props.t.hero.productCta,
      image: product.image,
      product,
    }))
  }, [props.products, props.t])
  const [activeSlide, setActiveSlide] = useState(0)
  const slide = slides[activeSlide] ?? slides[0]
  const campaignTiles = props.products.slice(4, 8)
  const categoryTiles = props.categories.filter((item) => item !== 'Tumu').slice(0, 5)

  useEffect(() => {
    if (slides.length < 2) return

    const timer = window.setInterval(() => {
      setActiveSlide((current) => (current + 1) % slides.length)
    }, 4500)

    return () => window.clearInterval(timer)
  }, [slides.length])

  return (
    <div className="content-grid storefront-grid">
      {slide && (
        <section className="customer-hero full-span" aria-label="Customer campaign slider">
          <div className="hero-copy">
            <span className="eyebrow">{slide.eyebrow}</span>
            <h2>{slide.title}</h2>
            <p>{slide.description}</p>
            <div className="hero-actions">
              <button type="button" onClick={() => props.onAddToCart(slide.product)}>
                {slide.cta}
              </button>
              <button type="button" className="ghost" onClick={() => props.onOpenProduct(slide.product)}>
                {props.t.hero.details}
              </button>
              <button type="button" className="ghost" onClick={() => props.onCompare(slide.product.id)}>
                {props.t.hero.compare}
              </button>
            </div>
          </div>
          <div className="hero-showcase">
            <img src={slide.image} alt={slide.product.title} />
            <div className="hero-price-card">
              <span>{displayBadge(slide.product.badge, props.t)}</span>
              <strong>{props.money.format(slide.product.price)}</strong>
              <small>{slide.product.seller}</small>
            </div>
          </div>
          <div className="slider-dots" aria-label="Slide selector">
            {slides.map((item, index) => (
              <button key={item.id} className={index === activeSlide ? 'active' : ''} type="button" onClick={() => setActiveSlide(index)} aria-label={`Slide ${index + 1}`} />
            ))}
          </div>
        </section>
      )}

      <section className="category-strip full-span" aria-label={props.t.categoriesTitle}>
        {categoryTiles.map((item) => (
          <button key={item} type="button" onClick={() => props.onCategoryChange(item)}>
            <span>{formatCategoryRoot(item, props.t)}</span>
            <strong>{props.t.store.categoryCta}</strong>
          </button>
        ))}
      </section>

      <section className="promo-strip full-span" aria-label="Campaign product tiles">
        {campaignTiles.map((product) => (
          <article className="promo-tile" key={product.id}>
            <img src={product.image} alt={product.title} />
            <div>
              <span>{displayBadge(product.badge, props.t)}</span>
              <strong>{product.title}</strong>
              <button type="button" className="ghost" onClick={() => props.onAddToCart(product)}>
                {props.t.store.addToCart}
              </button>
            </div>
          </article>
        ))}
      </section>

      <section className="toolbar full-span" aria-label="Product controls">
        <label>
          {props.t.store.search}
          <input value={props.query} onChange={(event) => props.onQueryChange(event.target.value)} placeholder={props.t.store.searchPlaceholder} />
        </label>
        <label>
          {props.t.store.category}
          <select value={props.category} onChange={(event) => props.onCategoryChange(event.target.value)}>
            {props.categories.map((option) => (
              <option key={option} value={option}>
                {formatCategoryRoot(option, props.t)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {props.t.store.sort}
          <select value={props.sortMode} onChange={(event) => props.onSortChange(event.target.value as SortMode)}>
            <option value="priority">{props.t.store.priority}</option>
            <option value="priceAsc">{props.t.store.priceAsc}</option>
            <option value="rating">{props.t.store.rating}</option>
          </select>
        </label>
      </section>

      <section className="showcase-band full-span">
        <div>
          <span className="eyebrow">{props.t.store.showcaseEyebrow}</span>
          <h2>{props.t.store.showcaseTitle}</h2>
        </div>
        <div className="showcase-stats">
          <span>
            {props.products.length} {props.t.store.products}
          </span>
          <span>
            {props.favorites.length} {props.favorites.length === 1 ? props.t.store.favorite : props.t.store.favorites}
          </span>
          <span>
            {props.compare.length} {props.compare.length === 1 ? props.t.store.comparison : props.t.store.comparisons}
          </span>
        </div>
      </section>

      <section className="product-grid">
        {props.products.map((product) => (
          <article className="product-card" key={product.id}>
            <button type="button" className="product-media" onClick={() => props.onOpenProduct(product)}>
              <img src={product.image} alt={product.title} />
              <span>{product.type === 'digital' ? props.t.store.digitalDelivery : props.t.store.shipping}</span>
            </button>
            <div className="product-body">
              <div className="product-meta">
                <span>{displayBadge(product.badge, props.t)}</span>
                <strong>{product.rating.toFixed(1)}</strong>
              </div>
              <h3>{product.title}</h3>
              <p>{product.seller}</p>
              <small>{formatCategoryPath(product.category, props.t)}</small>
              <div className="price-row">
                <strong>{props.money.format(product.price)}</strong>
                <span>{props.money.format(product.oldPrice)}</span>
              </div>
              <div className="button-row">
                <button type="button" className="ghost" onClick={() => props.onOpenProduct(product)}>
                  {props.t.store.detail}
                </button>
                <button type="button" onClick={() => props.onAddToCart(product)}>
                  {props.t.store.addToCart}
                </button>
                <button type="button" className={props.favorites.includes(product.id) ? 'ghost selected' : 'ghost'} onClick={() => props.onFavorite(product.id)}>
                  {props.t.store.fav}
                </button>
                <button type="button" className={props.compare.includes(product.id) ? 'ghost selected' : 'ghost'} onClick={() => props.onCompare(product.id)}>
                  {props.t.store.cmp}
                </button>
              </div>
            </div>
          </article>
        ))}
      </section>

      <aside className="cart-panel">
        <h2>{props.t.store.cartTitle}</h2>
        <div className="cart-list">
          {props.cart.length === 0 && <p>{props.t.store.emptyCart}</p>}
          {props.cart.map((item) => (
            <div className="cart-line" key={item.id}>
              <span>{item.quantity}x</span>
              <strong>{item.title}</strong>
              <em>{props.money.format(item.price * item.quantity)}</em>
            </div>
          ))}
        </div>
        <div className="cart-total">
          <span>{props.t.store.total}</span>
          <strong>{props.money.format(props.cartTotal)}</strong>
        </div>
        <button type="button" className="primary-action" onClick={props.onCheckout}>
          {props.t.store.sandboxCheckout}
        </button>
        <p className="status-line">{props.checkoutStatus}</p>

        <div className="compare-box">
          <h3>{props.t.store.compareTitle}</h3>
          {props.selectedCompare.length === 0 && <p>{props.t.store.compareEmpty}</p>}
          {props.selectedCompare.map((product) => (
            <div key={product.id}>
              <span>{product.title}</span>
              <strong>{props.money.format(product.price)}</strong>
            </div>
          ))}
        </div>
      </aside>
    </div>
  )
}

function ProductRoute(props: {
  product: Product | null | undefined
  products: Product[]
  favorites: string[]
  compare: string[]
  money: Intl.NumberFormat
  t: Copy
  onAddToCart: (product: Product) => void
  onFavorite: (id: string) => void
  onCompare: (id: string) => void
  onOpenProduct: (product: Product) => void
  onBack: () => void
}) {
  if (!props.product) {
    return (
      <div className="content-grid">
        <section className="empty-state full-span">
          <span className="eyebrow">{props.t.detail.productNotFound}</span>
          <h2>{props.t.detail.productNotFound}</h2>
          <p>{props.t.detail.productNotFoundBody}</p>
          <button type="button" onClick={props.onBack}>
            {props.t.detail.backToStorefront}
          </button>
        </section>
      </div>
    )
  }

  const relatedProducts = props.products
    .filter((product) => product.id !== props.product?.id && product.category.split('/')[0] === props.product?.category.split('/')[0])
    .slice(0, 3)

  return (
    <div className="content-grid product-page-grid">
      <ProductDetailPanel
        product={props.product}
        isFavorite={props.favorites.includes(props.product.id)}
        isCompared={props.compare.includes(props.product.id)}
        money={props.money}
        t={props.t}
        closeLabel={props.t.detail.backToStorefront}
        onAddToCart={props.onAddToCart}
        onFavorite={props.onFavorite}
        onCompare={props.onCompare}
        onClose={props.onBack}
      />

      {relatedProducts.length > 0 && (
        <section className="related-products full-span">
          <div className="showcase-band">
            <div>
              <span className="eyebrow">{props.t.store.showcaseEyebrow}</span>
              <h2>{props.t.store.showcaseTitle}</h2>
            </div>
          </div>
          <div className="product-grid compact-grid">
            {relatedProducts.map((product) => (
              <article className="product-card" key={product.id}>
                <button type="button" className="product-media" onClick={() => props.onOpenProduct(product)}>
                  <img src={product.image} alt={product.title} />
                  <span>{product.type === 'digital' ? props.t.store.digitalDelivery : props.t.store.shipping}</span>
                </button>
                <div className="product-body">
                  <div className="product-meta">
                    <span>{displayBadge(product.badge, props.t)}</span>
                    <strong>{product.rating.toFixed(1)}</strong>
                  </div>
                  <h3>{product.title}</h3>
                  <p>{product.seller}</p>
                  <div className="price-row">
                    <strong>{props.money.format(product.price)}</strong>
                    <span>{props.money.format(product.oldPrice)}</span>
                  </div>
                  <div className="button-row">
                    <button type="button" className="ghost" onClick={() => props.onOpenProduct(product)}>
                      {props.t.store.detail}
                    </button>
                    <button type="button" onClick={() => props.onAddToCart(product)}>
                      {props.t.store.addToCart}
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

function ProductDetailPanel(props: {
  product: Product
  isFavorite: boolean
  isCompared: boolean
  money: Intl.NumberFormat
  t: Copy
  closeLabel?: string
  onAddToCart: (product: Product) => void
  onFavorite: (id: string) => void
  onCompare: (id: string) => void
  onClose: () => void
}) {
  const description =
    props.product.type === 'digital'
      ? `${props.product.title} ${props.t.detail.digitalDescription}`
      : `${props.product.title} ${props.t.detail.physicalDescription}`
  const specs = [
    [props.t.detail.category, formatCategoryPath(props.product.category, props.t)],
    [props.t.detail.seller, props.product.seller],
    [props.t.detail.stock, `${props.product.stock} ${props.t.detail.unit}`],
    [props.t.detail.deliveryType, props.product.type === 'digital' ? props.t.detail.digitalDelivery : props.t.detail.physicalDelivery],
    [props.t.detail.rating, props.product.rating.toFixed(1)],
  ]

  return (
    <section className="product-detail full-span" aria-label={`${props.product.title} detail`}>
      <div className="detail-media">
        <img src={props.product.image} alt={props.product.title} />
      </div>
      <div className="detail-content">
        <div className="detail-heading">
          <div>
            <span className="eyebrow">{displayBadge(props.product.badge, props.t)}</span>
            <h2>{props.product.title}</h2>
            <p>{description}</p>
          </div>
          <button type="button" className="ghost" onClick={props.onClose}>
            {props.closeLabel ?? props.t.detail.close}
          </button>
        </div>

        <div className="detail-price">
          <strong>{props.money.format(props.product.price)}</strong>
          <span>{props.money.format(props.product.oldPrice)}</span>
        </div>

        <div className="detail-actions">
          <button type="button" onClick={() => props.onAddToCart(props.product)}>
            {props.t.store.addToCart}
          </button>
          <button type="button" className={props.isFavorite ? 'ghost selected' : 'ghost'} onClick={() => props.onFavorite(props.product.id)}>
            {props.t.store.fav}
          </button>
          <button type="button" className={props.isCompared ? 'ghost selected' : 'ghost'} onClick={() => props.onCompare(props.product.id)}>
            {props.t.hero.compare}
          </button>
        </div>

        <div className="detail-grid">
          <DataPanel title={props.t.detail.specs}>
            {specs.map(([label, value]) => (
              <StatusRow key={label} label={label} value={value} />
            ))}
          </DataPanel>
          <DataPanel title={props.t.detail.deliveryReturns}>
            <StatusRow label={props.t.detail.shipping} value={props.product.type === 'digital' ? props.t.detail.noShipping : props.t.detail.shippingMock} />
            <StatusRow label={props.t.detail.return} value={props.product.type === 'digital' ? props.t.detail.digitalReview : props.t.detail.physicalReturn} />
            <StatusRow label={props.t.detail.invoice} value={props.t.detail.invoiceMock} />
          </DataPanel>
          <DataPanel title={props.t.detail.questionsReviews}>
            <StatusRow label={props.t.detail.sellerQuestion} value={props.t.detail.answeredInPanel} />
            <StatusRow label={props.t.detail.reviewScore} value={`${props.product.rating.toFixed(1)} / 5`} />
            <StatusRow label={props.t.detail.moderation} value={props.t.detail.bannedWordFilter} />
          </DataPanel>
        </div>
      </div>
    </section>
  )
}

function AdminDashboard(props: {
  data: MarketplaceData
  logo: string
  logoError: string
  t: Copy
  onLogoUpload: (event: ChangeEvent<HTMLInputElement>) => void
  onRemoveLogo: () => void
}) {
  return (
    <div className="dashboard-stack">
      <LogoManager title={props.t.dashboard.adminLogoTitle} description={props.t.dashboard.adminLogoDescription} logo={props.logo} error={props.logoError} t={props.t} onLogoUpload={props.onLogoUpload} onRemoveLogo={props.onRemoveLogo} />
      <MetricGrid
        metrics={[
          [props.t.dashboard.activeProducts, props.data.products.length.toString()],
          [props.t.dashboard.sellers, props.data.sellers.length.toString()],
          [props.t.dashboard.orders, props.data.orders.length.toString()],
          [props.t.dashboard.providers, props.data.providers.length.toString()],
        ]}
      />
      <section className="panel-grid">
        <DataPanel title={props.t.dashboard.roles}>
          {[props.t.dashboard.allModules, props.t.dashboard.financePerm, props.t.dashboard.supportPerm, props.t.dashboard.marketingPerm].map((item) => (
            <StatusRow key={item} label={item} value={props.t.dashboard.active} />
          ))}
        </DataPanel>
        <DataPanel title={props.t.dashboard.integrations}>
          {props.data.providers.map((provider) => (
            <StatusRow
              key={provider.id}
              label={`${displayProviderType(provider, props.t)} - ${provider.name}`}
              value={`${displayPhrase(provider.status, props.t)} / ${displayPhrase(provider.health, props.t)}`}
            />
          ))}
        </DataPanel>
        <DataPanel title={props.t.dashboard.audit}>
          {props.data.audit.map((event) => (
            <StatusRow key={event.id} label={`${event.time} ${event.actor}`} value={displayPhrase(event.action, props.t)} />
          ))}
        </DataPanel>
      </section>
    </div>
  )
}

function SellerDashboard(props: { products: Product[]; sellers: Seller[]; variant: 'catalog' | 'performance'; money: Intl.NumberFormat; t: Copy }) {
  const isCatalog = props.variant === 'catalog'

  return (
    <div className="dashboard-stack">
      <MetricGrid
        metrics={
          isCatalog
            ? [
                [props.t.dashboard.totalProducts, props.products.length.toString()],
                [props.t.dashboard.stockAlerts, props.products.filter((product) => product.stock < 50).length.toString()],
                [props.t.dashboard.digitalProducts, props.products.filter((product) => product.type === 'digital').length.toString()],
                [props.t.dashboard.pendingVariants, '7'],
              ]
            : [
                [props.t.dashboard.approvedSellers, props.sellers.length.toString()],
                [props.t.dashboard.corporateBadge, props.sellers.filter((seller) => !isApprovedSellerBadge(seller.badge)).length.toString()],
                [props.t.dashboard.campaignParticipation, '3'],
                [props.t.dashboard.avgSla, '99.79%'],
              ]
        }
      />
      <section className="panel-grid">
        {isCatalog ? (
          <>
            <DataPanel title={props.t.dashboard.productStock}>
              {props.products.slice(0, 7).map((product) => (
                <StatusRow key={product.id} label={product.title} value={`${product.stock} / ${props.money.format(product.price)}`} />
              ))}
            </DataPanel>
            <DataPanel title={props.t.dashboard.deliverySplit}>
              <StatusRow label={props.t.dashboard.physicalProducts} value={props.products.filter((product) => product.type === 'physical').length.toString()} />
              <StatusRow label={props.t.dashboard.digitalProducts} value={props.products.filter((product) => product.type === 'digital').length.toString()} />
              <StatusRow label={props.t.dashboard.shippingMock} value={props.t.dashboard.active} />
            </DataPanel>
            <DataPanel title={props.t.dashboard.sellerActions}>
              <StatusRow label={props.t.dashboard.uploadProductVisual} value={props.t.dashboard.ready} />
              <StatusRow label={props.t.dashboard.updatePriceStock} value={props.t.dashboard.ready} />
              <StatusRow label={props.t.dashboard.joinCampaign} value={props.t.dashboard.approvalPending} />
            </DataPanel>
          </>
        ) : (
          <>
            <DataPanel title={props.t.dashboard.sellerPerformance}>
              {props.sellers.map((seller) => (
                <StatusRow key={seller.id} label={`${seller.name} - ${displaySellerBadge(seller.badge, props.t)}`} value={`${seller.score}/100 SLA ${seller.sla}`} />
              ))}
            </DataPanel>
            <DataPanel title={props.t.dashboard.payoutsCommission}>
              {props.sellers.map((seller) => (
                <StatusRow key={seller.id} label={seller.name} value={props.money.format(seller.payout)} />
              ))}
            </DataPanel>
            <DataPanel title={props.t.dashboard.opsHealth}>
              <StatusRow label={props.t.dashboard.slaBreach} value="2" />
              <StatusRow label={props.t.dashboard.returnRate} value="3.4%" />
              <StatusRow label={props.t.dashboard.badgeStatus} value={props.t.dashboard.corporateEligible} />
            </DataPanel>
          </>
        )}
      </section>
    </div>
  )
}

function MarketingDashboard(props: {
  campaigns: Campaign[]
  logo: string
  logoError: string
  t: Copy
  money: Intl.NumberFormat
  onLogoUpload: (event: ChangeEvent<HTMLInputElement>) => void
  onRemoveLogo: () => void
  variant: 'campaign' | 'seo'
}) {
  const [bannedWords, setBannedWords] = useState('fake, abusive, spam')
  const isCampaign = props.variant === 'campaign'

  return (
    <div className="dashboard-stack">
      {isCampaign && <LogoManager title={props.t.dashboard.marketingLogoTitle} description={props.t.dashboard.marketingLogoDescription} logo={props.logo} error={props.logoError} t={props.t} onLogoUpload={props.onLogoUpload} onRemoveLogo={props.onRemoveLogo} />}
      <section className="panel-grid">
        {isCampaign ? (
          <>
            <DataPanel title={props.t.dashboard.campaignManagement}>
              {props.campaigns.map((campaign) => (
                <StatusRow key={campaign.id} label={`${campaign.name} - ${campaign.owner}`} value={`${displayPhrase(campaign.status, props.t)} / ${campaign.conversion}`} />
              ))}
            </DataPanel>
            <DataPanel title={props.t.dashboard.bannersLanding}>
              <StatusRow label={props.t.dashboard.mainSlider} value="4" />
              <StatusRow label={props.t.dashboard.categoryShowcase} value="5" />
              <StatusRow label={props.t.dashboard.landingDraft} value="2" />
            </DataPanel>
            <DataPanel title={props.t.dashboard.campaignBudget}>
              {props.campaigns.map((campaign) => (
                <StatusRow key={campaign.id} label={campaign.name} value={props.money.format(campaign.budget)} />
              ))}
            </DataPanel>
          </>
        ) : (
          <>
            <DataPanel title={props.t.dashboard.seoAnalytics}>
              <StatusRow label="GA4" value={props.t.dashboard.connectedMock} />
              <StatusRow label="Meta Pixel" value={props.t.dashboard.connectedMock} />
              <StatusRow label="Schema" value={props.t.dashboard.productCategoryActive} />
              <StatusRow label="Search Console" value={props.t.dashboard.connectionPending} />
            </DataPanel>
            <DataPanel title={props.t.dashboard.bannedWords}>
              <label className="wide-label">
                {props.t.dashboard.manualModeration}
                <textarea value={bannedWords} onChange={(event) => setBannedWords(event.target.value)} rows={5} />
              </label>
              <p className="status-line">{props.t.dashboard.aiModerationLater}</p>
            </DataPanel>
            <DataPanel title={props.t.dashboard.publishingFlow}>
              <StatusRow label={props.t.dashboard.blogDrafts} value="8" />
              <StatusRow label={props.t.dashboard.categoryTextPending} value="12" />
              <StatusRow label={props.t.dashboard.rollback} value={props.t.dashboard.active} />
            </DataPanel>
          </>
        )}
      </section>
    </div>
  )
}

function FinanceDashboard({ data, variant, money, t }: { data: MarketplaceData; variant: 'payments' | 'payouts'; money: Intl.NumberFormat; t: Copy }) {
  const isPayments = variant === 'payments'

  return (
    <div className="dashboard-stack">
      <MetricGrid
        metrics={
          isPayments
            ? [
                [t.dashboard.refundReview, data.orders.filter((order) => isRefundStatus(order.status)).length.toString()],
                [t.dashboard.paymentProvider, data.providers.filter((provider) => provider.type === 'Odeme').length.toString()],
                [t.dashboard.invoiceAdapter, data.providers.filter((provider) => provider.type === 'Fatura').length.toString()],
                [t.dashboard.chargeback, '4'],
              ]
            : [
                [t.dashboard.totalPayout, money.format(data.sellers.reduce((sum, seller) => sum + seller.payout, 0))],
                [t.dashboard.commissionPool, money.format(148200)],
                [t.dashboard.reconciliationPending, '6'],
                [t.dashboard.corporateBadge, '2'],
              ]
        }
      />
      <section className="panel-grid">
        {isPayments ? (
          <>
            <DataPanel title={t.dashboard.paymentInvoiceProviders}>
              {data.providers
                .filter((provider) => ['Odeme', 'Fatura'].includes(provider.type))
                .map((provider) => (
                  <StatusRow key={provider.id} label={provider.name} value={`${displayPhrase(provider.status, t)} / ${displayPhrase(provider.health, t)}`} />
                ))}
            </DataPanel>
            <DataPanel title={t.dashboard.refundsChargebacks}>
              {data.orders.map((order) => (
                <StatusRow key={order.id} label={`${order.id} - ${order.customer}`} value={displayPhrase(order.status, t)} />
              ))}
            </DataPanel>
          </>
        ) : (
          <>
            <DataPanel title={t.dashboard.sellerPayouts}>
              {data.sellers.map((seller) => (
                <StatusRow key={seller.id} label={seller.name} value={money.format(seller.payout)} />
              ))}
            </DataPanel>
            <DataPanel title={t.dashboard.commissionReconciliation}>
              <StatusRow label={t.dashboard.marketplaceCommission} value="12.5%" />
              <StatusRow label={t.dashboard.badgeDiscount} value="2%" />
              <StatusRow label={t.dashboard.reconciliationExport} value={t.dashboard.csvReady} />
            </DataPanel>
          </>
        )}
      </section>
    </div>
  )
}

function SupportDashboard({ data, variant, t }: { data: MarketplaceData; variant: 'orders' | 'live'; t: Copy }) {
  const isOrders = variant === 'orders'

  return (
    <div className="dashboard-stack">
      <MetricGrid
        metrics={
          isOrders
            ? [
                [t.dashboard.openTickets, '18'],
                [t.dashboard.refundSla, '4h 20m'],
                [t.dashboard.paymentInterventions, '3'],
                [t.dashboard.cancellationPending, '5'],
              ]
            : [
                [t.dashboard.liveSupport, t.dashboard.active],
                [t.dashboard.sellerQuestions, '12'],
                [t.dashboard.slaBreach, '2'],
                [t.dashboard.escalations, '1'],
              ]
        }
      />
      <section className="panel-grid">
        {isOrders ? (
          <>
            <DataPanel title={t.dashboard.orderIntervention}>
              {data.orders.map((order) => (
                <StatusRow key={order.id} label={`${order.id} - ${order.customer}`} value={displayPhrase(order.status, t)} />
              ))}
            </DataPanel>
            <DataPanel title={t.dashboard.cancellationRefundSteps}>
              <StatusRow label={t.dashboard.paymentInterventionAllowed} value={t.dashboard.allowed} />
              <StatusRow label={t.dashboard.shippingRelated} value={t.dashboard.shippingMock} />
              <StatusRow label={t.dashboard.digitalDeliveryClaim} value={t.dashboard.manualReview} />
            </DataPanel>
          </>
        ) : (
          <>
            <DataPanel title={t.dashboard.sellerQuestionFlow}>
              <StatusRow label={t.dashboard.newQuestions} value="12" />
              <StatusRow label={t.dashboard.slaBreach} value="2" />
              <StatusRow label={t.dashboard.adminEscalation} value="1" />
            </DataPanel>
            <DataPanel title={t.dashboard.liveSupportHealth}>
              <StatusRow label={t.dashboard.activeAgents} value="8" />
              <StatusRow label={t.dashboard.avgResponse} value="42s" />
              <StatusRow label={t.dashboard.satisfaction} value="91%" />
            </DataPanel>
          </>
        )}
      </section>
    </div>
  )
}

function LogoManager(props: {
  title: string
  description: string
  logo: string
  error: string
  t: Copy
  onLogoUpload: (event: ChangeEvent<HTMLInputElement>) => void
  onRemoveLogo: () => void
}) {
  return (
    <section className="logo-manager">
      <div className="logo-preview">{props.logo ? <img src={props.logo} alt={`${props.title} preview`} /> : <span>PNG</span>}</div>
      <div>
        <span className="eyebrow">{props.t.dashboard.brandAsset}</span>
        <h2>{props.title}</h2>
        <p>{props.description}</p>
        {props.error && <p className="error-line">{props.error}</p>}
      </div>
      <div className="logo-actions">
        <label className="file-button">
          {props.t.dashboard.uploadPng}
          <input accept="image/png" type="file" onChange={props.onLogoUpload} />
        </label>
        <button type="button" className="ghost" onClick={props.onRemoveLogo}>
          {props.t.dashboard.remove}
        </button>
      </div>
    </section>
  )
}

function MetricGrid({ metrics }: { metrics: Array<[string, string]> }) {
  return (
    <section className="metric-grid">
      {metrics.map(([label, value]) => (
        <article className="metric-card" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </article>
      ))}
    </section>
  )
}

function DataPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="data-panel">
      <h2>{title}</h2>
      <div className="panel-list">{children}</div>
    </article>
  )
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="status-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function formatCategoryRoot(root: string, t: Copy) {
  return t.categoryNames[root as keyof typeof t.categoryNames] ?? root
}

function formatCategoryPath(path: string, t: Copy) {
  return path
    .split('/')
    .map((part) => part.trim())
    .map((part, index) => (index === 0 ? formatCategoryRoot(part, t) : part))
    .join(' / ')
}

function isTurkish(t: Copy) {
  return t === copy.tr
}

function localizePair(pair: [string, string], t: Copy) {
  return isTurkish(t) ? pair[1] : pair[0]
}

function displayBadge(badge: string, t: Copy) {
  const badgeMap: Record<string, [string, string]> = {
    'Kurumsal satici': ['Corporate seller', 'Kurumsal satıcı'],
    'Avantajli fiyat': ['Best value', 'Avantajlı fiyat'],
    'Markanin urunu': ['Brand-owned product', 'Markanın ürünü'],
    'Ayni gun kargo': ['Same-day shipping', 'Aynı gün kargo'],
    'Dijital teslim': ['Digital delivery', 'Dijital teslim'],
    'Set urun': ['Bundle product', 'Set ürün'],
    'Kuponlu urun': ['Coupon product', 'Kuponlu ürün'],
    'Cok satan': ['Best seller', 'Çok satan'],
    'Hizli kargo': ['Fast shipping', 'Hızlı kargo'],
    'Aile secimi': ['Family choice', 'Aile seçimi'],
  }
  return localizePair(badgeMap[badge] ?? [badge, badge], t)
}

function displaySellerBadge(badge: string, t: Copy) {
  const badgeMap: Record<string, [string, string]> = {
    'Kendi marka': ['Brand-owned seller', 'Kendi marka'],
    Kurumsal: ['Corporate', 'Kurumsal'],
    Onayli: ['Approved', 'Onaylı'],
  }
  return localizePair(badgeMap[badge] ?? [badge, badge], t)
}

function displayPhrase(value: string, t: Copy) {
  const phraseMap: Record<string, [string, string]> = {
    Aktif: ['Active', 'Aktif'],
    Taslak: ['Draft', 'Taslak'],
    Sandbox: ['Sandbox', 'Sandbox'],
    Mock: ['Mock', 'Mock'],
    Hazir: ['Ready', 'Hazır'],
    'Baglanti bekliyor': ['Connection pending', 'Bağlantı bekliyor'],
    'Saglayici secilecek': ['Provider to be selected', 'Sağlayıcı seçilecek'],
    'Odeme onaylandi': ['Payment approved', 'Ödeme onaylandı'],
    'Dijital teslim edildi': ['Digital delivery completed', 'Dijital teslim edildi'],
    'Iade incelemede': ['Refund under review', 'İade incelemede'],
    'Demo siparis olusturuldu': ['Demo order created', 'Demo sipariş oluşturuldu'],
    'Odeme saglayici sirasi guncellendi': ['Payment provider priority updated', 'Ödeme sağlayıcı sırası güncellendi'],
    'Mor Cuma banneri yayinlandi': ['Purple Friday banner published', 'Mor Cuma bannerı yayınlandı'],
    'MP-84023 iade incelemesi baslatildi': ['MP-84023 refund review started', 'MP-84023 iade incelemesi başlatıldı'],
  }
  return localizePair(phraseMap[value] ?? [value, value], t)
}

function isApprovedSellerBadge(badge: string) {
  return badge === 'Onayli' || badge === 'Approved'
}

function isRefundStatus(status: string) {
  return ['Iade incelemede', 'Refund under review'].includes(status)
}

function displayProviderType(provider: Provider, t: Copy) {
  const typeMap: Record<string, [string, string]> = {
    Odeme: ['Payment', 'Ödeme'],
    Kargo: ['Shipping', 'Kargo'],
    Fatura: ['Invoice', 'Fatura'],
    Bildirim: ['Notification', 'Bildirim'],
  }
  return localizePair(typeMap[provider.type] ?? [provider.type, provider.type], t)
}

export default App
