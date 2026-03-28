/**
 * Low-Stock Urgency Widget
 *
 * Injects "Only X left!" badges on Shopify product pages.
 * Deployed by Marcus (Chief of Staff agent) via the storefront script injection API.
 *
 * Usage: <script src="https://your-app.com/low-stock-widget.js"></script>
 */
(function () {
  'use strict'

  var THRESHOLD = 10
  var BADGE_STYLE =
    'display:inline-block;background:#FF4444;color:#fff;font-size:12px;font-weight:600;' +
    'padding:4px 10px;border-radius:4px;margin-top:8px;animation:pulse 2s infinite'

  var KEYFRAMES = '@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.7}}'

  // Inject animation keyframes
  var style = document.createElement('style')
  style.textContent = KEYFRAMES
  document.head.appendChild(style)

  function getProductJson() {
    // Shopify exposes product data on product pages
    if (window.ShopifyAnalytics && window.ShopifyAnalytics.meta && window.ShopifyAnalytics.meta.product) {
      return window.ShopifyAnalytics.meta.product
    }
    // Fallback: look for product JSON in script tag
    var scripts = document.querySelectorAll('script[type="application/json"][data-product-json]')
    for (var i = 0; i < scripts.length; i++) {
      try { return JSON.parse(scripts[i].textContent) } catch (e) { /* skip */ }
    }
    return null
  }

  function init() {
    var product = getProductJson()
    if (!product || !product.variants) return

    // Check each variant's inventory
    var lowStockVariants = []
    for (var i = 0; i < product.variants.length; i++) {
      var v = product.variants[i]
      if (v.inventory_quantity > 0 && v.inventory_quantity <= THRESHOLD) {
        lowStockVariants.push(v)
      }
    }

    if (lowStockVariants.length === 0) return

    // Find the lowest stock count
    var minStock = Infinity
    for (var j = 0; j < lowStockVariants.length; j++) {
      if (lowStockVariants[j].inventory_quantity < minStock) {
        minStock = lowStockVariants[j].inventory_quantity
      }
    }

    // Find the add-to-cart form or product title to inject badge
    var targets = [
      document.querySelector('.product-form__submit, [data-add-to-cart], .add-to-cart'),
      document.querySelector('.product__title, .product-single__title, h1.title'),
      document.querySelector('h1'),
    ]

    var target = null
    for (var k = 0; k < targets.length; k++) {
      if (targets[k]) { target = targets[k]; break }
    }
    if (!target) return

    var badge = document.createElement('div')
    badge.style.cssText = BADGE_STYLE
    badge.textContent = minStock === 1
      ? 'Only 1 left in stock!'
      : 'Only ' + minStock + ' left in stock!'

    target.parentNode.insertBefore(badge, target.nextSibling)
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }
})()
