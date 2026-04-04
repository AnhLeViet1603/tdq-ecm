/**
 * ShopVN — SPA Frontend
 * Vanilla JS · Fetch API · LocalStorage JWT
 */

'use strict';

// ════════════════════════════════════════════════════════════
//  CONFIG
// ════════════════════════════════════════════════════════════
const API = {
  auth:      '/api/auth',
  products:  '/api/products',
  inventory: '/api/inventory',
  cart:      '/api/cart',
  orders:    '/api/orders',
  payments:  '/api/payments',
  promotions:'/api/promotions',
  reviews:   '/api/reviews',
  shipping:  '/api/shipping',
};

// ════════════════════════════════════════════════════════════
//  STATE
// ════════════════════════════════════════════════════════════
const State = {
  user:         null,
  accessToken:  localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  currentPage:  'home',
  cartCount:    0,
  products:     { data: [], page: 1, total: 0 },
};

// ════════════════════════════════════════════════════════════
//  UTILS
// ════════════════════════════════════════════════════════════
const fmt = {
  vnd:  (n) => Number(n).toLocaleString('vi-VN') + '₫',
  date: (d) => new Date(d).toLocaleDateString('vi-VN', { day:'2-digit', month:'2-digit', year:'numeric' }),
  initials: (name) => (name||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase(),
};

function qs(selector, root = document) { return root.querySelector(selector); }
function qsa(selector, root = document) { return [...root.querySelectorAll(selector)]; }

// ════════════════════════════════════════════════════════════
//  API LAYER
// ════════════════════════════════════════════════════════════
async function apiFetch(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (State.accessToken) headers['Authorization'] = `Bearer ${State.accessToken}`;

  const resp = await fetch(url, { ...options, headers });

  // Try auto-refresh on 401
  if (resp.status === 401 && State.refreshToken) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${State.accessToken}`;
      return fetch(url, { ...options, headers });
    } else {
      logout();
      throw new Error('Session expired');
    }
  }
  return resp;
}

async function tryRefreshToken() {
  try {
    const resp = await fetch(`${API.auth}/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: State.refreshToken }),
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    State.accessToken = data.access;
    localStorage.setItem('access_token', data.access);
    return true;
  } catch { return false; }
}

async function apiGet(url) {
  const resp = await apiFetch(url);
  if (!resp.ok) throw new Error(`GET ${url} → ${resp.status}`);
  return resp.json();
}

async function apiPost(url, body) {
  const resp = await apiFetch(url, { method: 'POST', body: JSON.stringify(body) });
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

async function apiPut(url, body) {
  const resp = await apiFetch(url, { method: 'PATCH', body: JSON.stringify(body) });
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

async function apiDelete(url) {
  const resp = await apiFetch(url, { method: 'DELETE' });
  if (resp.status !== 204 && !resp.ok) throw new Error(`DELETE ${url} → ${resp.status}`);
  return true;
}

// ════════════════════════════════════════════════════════════
//  TOAST
// ════════════════════════════════════════════════════════════
function toast(msg, type = 'info', duration = 3500) {
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]||'ℹ️'}</span><span>${msg}</span>`;
  qs('#toast-container').appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ════════════════════════════════════════════════════════════
//  AUTH
// ════════════════════════════════════════════════════════════
function setTokens(access, refresh) {
  State.accessToken  = access;
  State.refreshToken = refresh;
  localStorage.setItem('access_token',  access);
  localStorage.setItem('refresh_token', refresh);
}

function logout() {
  if (State.refreshToken) {
    apiPost(`${API.auth}/logout/`, { refresh: State.refreshToken }).catch(()=>{});
  }
  State.accessToken  = null;
  State.refreshToken = null;
  State.user         = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  showAuth();
}

function showAuth() {
  qs('#auth').classList.remove('hidden');
  qs('#app').classList.add('hidden');
}

function showApp() {
  qs('#auth').classList.add('hidden');
  qs('#app').classList.remove('hidden');
}

// Tab switching
qsa('.auth-tabs .tab').forEach(btn => {
  btn.addEventListener('click', () => {
    qsa('.auth-tabs .tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.dataset.tab;
    qs('#login-form').classList.toggle('hidden',    tab !== 'login');
    qs('#register-form').classList.toggle('hidden', tab !== 'register');
    qs('#login-error').classList.add('hidden');
    qs('#reg-error').classList.add('hidden');
  });
});

// Login
qs('#login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const errEl  = qs('#login-error');
  const btnTxt = qs('#login-btn-text');
  errEl.classList.add('hidden');
  btnTxt.textContent = 'Đang đăng nhập…';

  try {
    const data = await apiPost(`${API.auth}/login/`, {
      email:    qs('#login-email').value.trim(),
      password: qs('#login-password').value,
    });
    setTokens(data.access, data.refresh);
    await initApp();
  } catch (err) {
    errEl.textContent = err?.detail || 'Email hoặc mật khẩu không đúng';
    errEl.classList.remove('hidden');
  } finally {
    btnTxt.textContent = 'Đăng nhập';
  }
});

// Register
qs('#register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const errEl  = qs('#reg-error');
  const btnTxt = qs('#reg-btn-text');
  errEl.classList.add('hidden');

  const password = qs('#reg-password').value;
  const confirm  = qs('#reg-confirm').value;
  if (password !== confirm) {
    errEl.textContent = 'Mật khẩu xác nhận không khớp';
    errEl.classList.remove('hidden');
    return;
  }

  btnTxt.textContent = 'Đang tạo tài khoản…';
  try {
    await apiPost(`${API.auth}/register/`, {
      full_name:        qs('#reg-name').value.trim(),
      email:            qs('#reg-email').value.trim(),
      password,
      password_confirm: confirm,
    });
    toast('Đăng ký thành công! Hãy đăng nhập.', 'success');
    qs('#tab-login').click();
    qs('#login-email').value = qs('#reg-email').value;
  } catch (err) {
    const msg = err?.email?.[0] || err?.password?.[0] || err?.detail || 'Đăng ký thất bại';
    errEl.textContent = msg;
    errEl.classList.remove('hidden');
  } finally {
    btnTxt.textContent = 'Tạo tài khoản';
  }
});

// Logout
qs('#logout-btn').addEventListener('click', () => {
  if (confirm('Bạn có chắc muốn đăng xuất?')) logout();
});

// ════════════════════════════════════════════════════════════
//  NAVIGATION (SPA)
// ════════════════════════════════════════════════════════════
const PAGE_TITLES = {
  home:       'Tổng quan',
  products:   'Sản phẩm',
  cart:       'Giỏ hàng',
  orders:     'Đơn hàng',
  promotions: 'Khuyến mãi',
  profile:    'Hồ sơ cá nhân',
  'manage-categories': 'Quản lý Danh mục',
  'manage-products':   'Quản lý Sản phẩm',
  'product-detail':    'Chi tiết sản phẩm',
  'checkout':          'Thanh toán',
};

function navigateTo(page) {
  if (!PAGE_TITLES[page]) return;

  // Hide all pages
  qsa('.page').forEach(p => p.classList.remove('active'));
  qs(`#page-${page}`)?.classList.add('active');

  // Update nav
  qsa('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.page === page);
  });

  // Update title
  qs('#page-title').textContent = PAGE_TITLES[page];
  document.title = `${PAGE_TITLES[page]} — ShopVN`;
  State.currentPage = page;

  // Load page data
  const loaders = {
    home:       loadHome,
    products:   loadProducts,
    cart:       loadCart,
    orders:     loadOrders,
    promotions: () => {},
    profile:    loadProfile,
    'manage-categories': loadManageCategories,
    'manage-products':   loadManageProducts,
    'product-detail':    loadProductDetailPage,
    'checkout':          loadCheckoutPage,
  };
  loaders[page]?.();
}

function navigateToProductDetail(id) {
  State.currentProductId = id;
  navigateTo('product-detail');
}

// Delegate all [data-page] clicks
document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-page]');
  if (!el) return;
  e.preventDefault();
  navigateTo(el.dataset.page);
});

// ════════════════════════════════════════════════════════════
//  INIT APP
// ════════════════════════════════════════════════════════════
async function initApp() {
  try {
    const me = await apiGet(`${API.auth}/me/`);
    State.user = me.data || me;
    updateUserUI();
    showApp();
    navigateTo('home');
  } catch (err) {
    logout();
  }
}

function updateUserUI() {
  const u = State.user;
  if (!u) return;
  const initials = fmt.initials(u.full_name);
  const roles = (u.roles || []).map(r => r.name || r);
  const isAdminOrStaff = roles.includes('admin') || roles.includes('staff');
  const roleName = isAdminOrStaff ? (roles.includes('admin') ? 'Quản trị viên' : 'Nhân viên') : 'Khách hàng';

  // Toggle Admin Menu
  const adminNav = qs('#nav-group-admin');
  if (adminNav) {
    if (isAdminOrStaff) adminNav.classList.remove('hidden');
    else adminNav.classList.add('hidden');
  }

  qsa('#user-avatar, #user-avatar-sm, #profile-avatar').forEach(el => el.textContent = initials);
  qs('#user-name').textContent    = u.full_name || u.email;
  qs('#user-name-sm').textContent = u.full_name || u.email;
  qs('#user-role').textContent    = roleName;
  qs('#profile-name').textContent  = u.full_name;
  qs('#profile-email').textContent = u.email;
  qs('#prof-name').value  = u.full_name || '';
  qs('#prof-phone').value = u.phone || '';

  const rolesEl = qs('#profile-roles');
  if (rolesEl) {
    rolesEl.innerHTML = (u.roles || []).map(r =>
      `<span class="role-badge">${r.name || r}</span>`
    ).join('') || '<span class="role-badge">customer</span>';
  }
}

// ════════════════════════════════════════════════════════════
//  HOME PAGE
// ════════════════════════════════════════════════════════════
async function loadHome() {
  loadFeaturedProducts();
  loadRecentOrders();
  loadStats();
}

async function loadStats() {
  // Products count
  apiGet(`${API.products}/?page_size=1`).then(d => {
    qs('#stat-products').textContent = d.count ?? '—';
  }).catch(()=>{});

  // Orders count
  apiGet(`${API.orders}/?page_size=1`).then(d => {
    qs('#stat-orders').textContent = d.count ?? '—';
  }).catch(()=>{});

  // Cart items
  apiGet(`${API.cart}/me/`).then(d => {
    const items = d.data?.items || d.items || [];
    const count = items.reduce((s, i) => s + i.quantity, 0);
    qs('#stat-cart-count').textContent = count;
    updateCartBadge(count);
  }).catch(()=>{});

  // Promotions — we just show a placeholder from the public API
  qs('#stat-coupons').textContent = 'Active';
}

async function loadFeaturedProducts() {
  const grid = qs('#featured-products');
  try {
    const data = await apiGet(`${API.products}/?page_size=4`);
    const items = data.results || [];
    grid.innerHTML = items.length
      ? items.map(renderProductCard).join('')
      : '<p class="text-secondary">Chưa có sản phẩm nào.</p>';
  } catch {
    grid.innerHTML = '<p class="text-secondary">Không thể tải sản phẩm.</p>';
  }
}

async function loadRecentOrders() {
  const tbody = qs('#recent-orders-body');
  try {
    const data = await apiGet(`${API.orders}/?page_size=5`);
    const orders = data.results || [];
    if (!orders.length) {
      tbody.innerHTML = '<tr><td colspan="4" class="loading-cell">Chưa có đơn hàng nào</td></tr>';
      return;
    }
    tbody.innerHTML = orders.map(o => `
      <tr>
        <td><code style="color:var(--primary-h);font-size:.8rem">${o.order_number}</code></td>
        <td>${renderStatus(o.status)}</td>
        <td style="font-weight:600">${fmt.vnd(o.total_amount)}</td>
        <td style="color:var(--text-2)">${fmt.date(o.created_at)}</td>
      </tr>
    `).join('');
  } catch {
    tbody.innerHTML = '<tr><td colspan="4" class="loading-cell">Không thể tải đơn hàng</td></tr>';
  }
}

// ════════════════════════════════════════════════════════════
//  PRODUCTS PAGE
// ════════════════════════════════════════════════════════════
let productSearchTimer = null;

async function loadProducts(page = 1) {
  const grid   = qs('#products-grid');
  const search = qs('#product-search').value.trim();
  const cat    = qs('#category-filter').value;

  grid.innerHTML = Array(6).fill('<div class="skeleton-card"></div>').join('');

  let url = `${API.products}/?page=${page}&page_size=12`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (cat)    url += `&category=${encodeURIComponent(cat)}`;

  try {
    const data = await apiGet(url);
    const items = data.results || [];
    State.products = { data: items, page, total: data.count || 0 };

    grid.innerHTML = items.length
      ? items.map(renderProductCard).join('')
      : '<div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-2)">Không tìm thấy sản phẩm nào</div>';

    renderPagination(data.count, page, 12);
  } catch {
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-2)">Không thể tải sản phẩm</div>';
  }
}

async function loadCategories() {
  try {
    const data = await apiGet(`${API.products}/categories/?page_size=100`);
    const cats = data.results || [];
    const select = qs('#category-filter');
    cats.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.slug; opt.textContent = c.name;
      select.appendChild(opt);
    });
  } catch {}
}

function renderProductCard(p) {
  const img = p.images?.[0]
    ? `<img src="${p.images[0]}" alt="${p.name}" loading="lazy" />`
    : '🛍️';
  const comparePrice = p.compare_price && p.compare_price > p.base_price
    ? `<span class="product-compare">${fmt.vnd(p.compare_price)}</span>` : '';
  return `
    <div class="product-card" data-product-id="${p.id}">
      <div class="product-img">${img}</div>
      <div class="product-body">
        <div class="product-name">${p.name}</div>
        <div class="product-sku">SKU: ${p.sku}</div>
        <div style="margin-top:auto">
          ${comparePrice}
          <div class="product-price">${fmt.vnd(p.base_price)}</div>
        </div>
      </div>
      <div class="product-footer">
        <button class="add-to-cart" data-product-id="${p.id}">+ Thêm vào giỏ</button>
      </div>
    </div>
  `;
}

function renderPagination(total, current, pageSize) {
  const container = qs('#products-pagination');
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) { container.innerHTML = ''; return; }

  let btns = '';
  btns += `<button class="page-btn" onclick="loadProducts(${current-1})" ${current===1?'disabled':''}>←</button>`;
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || Math.abs(i - current) <= 2) {
      btns += `<button class="page-btn ${i===current?'active':''}" onclick="loadProducts(${i})">${i}</button>`;
    } else if (Math.abs(i - current) === 3) {
      btns += `<span style="color:var(--text-3);padding:0 .25rem">…</span>`;
    }
  }
  btns += `<button class="page-btn" onclick="loadProducts(${current+1})" ${current===totalPages?'disabled':''}>→</button>`;
  container.innerHTML = btns;
}

// Product search with debounce
qs('#product-search').addEventListener('input', () => {
  clearTimeout(productSearchTimer);
  productSearchTimer = setTimeout(() => loadProducts(1), 400);
});
qs('#category-filter').addEventListener('change', () => loadProducts(1));

// Global search
qs('#global-search').addEventListener('input', (e) => {
  if (State.currentPage !== 'products') navigateTo('products');
  qs('#product-search').value = e.target.value;
  clearTimeout(productSearchTimer);
  productSearchTimer = setTimeout(() => loadProducts(1), 400);
});

// ════════════════════════════════════════════════════════════
//  PRODUCT MODAL
// ════════════════════════════════════════════════════════════
document.addEventListener('click', async (e) => {
  // Directly navigate to standard product detail page on card click (not on add-to-cart button)
  const card = e.target.closest('.product-card');
  const addBtn = e.target.closest('.add-to-cart');

  if (addBtn) {
    e.stopPropagation();
    const pid = addBtn.dataset.productId;
    if (pid) await addToCart(pid, 1, addBtn);
    return;
  }

  if (card && !addBtn) {
    const pid = card.dataset.productId;
    if (pid) navigateToProductDetail(pid);
  }
});

async function openProductModal(productId) {
  const modal = qs('#product-modal');
  const body  = qs('#modal-body');

  body.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-2)">Đang tải…</div>';
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';

  try {
    const resp = await apiGet(`${API.products}/${productId}/`);
    const p = resp.data || resp;
    const img = p.images?.[0]
      ? `<img src="${p.images[0]}" alt="${p.name}" style="width:100%;height:100%;object-fit:cover" />`
      : '🛍️';
    const attrs = (p.attributes || []).map(a =>
      `<span style="background:var(--bg-3);padding:.2rem .6rem;border-radius:99px;font-size:.75rem;margin-right:.35rem;margin-bottom:.35rem;display:inline-block">${a.attribute_name}: ${a.value}</span>`
    ).join('');

    body.innerHTML = `
      <div class="modal-img">${img}</div>
      <h2 class="modal-title" id="modal-title">${p.name}</h2>
      <p class="modal-sku">SKU: ${p.sku} ${p.category_name ? `· ${p.category_name}` : ''}</p>
      <div class="modal-price">${fmt.vnd(p.base_price)}</div>
      ${attrs ? `<div style="margin-bottom:1rem">${attrs}</div>` : ''}
      <p class="modal-desc">${p.description || 'Chưa có mô tả sản phẩm.'}</p>
      <div class="qty-row">
        <span style="font-size:.875rem;font-weight:600">Số lượng:</span>
        <div class="qty-control">
          <button class="qty-btn" id="modal-qty-minus">−</button>
          <span class="qty-value" id="modal-qty">1</span>
          <button class="qty-btn" id="modal-qty-plus">+</button>
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn-primary" id="modal-add-cart" data-product-id="${p.id}" style="flex:1">
          🛒 Thêm vào giỏ hàng
        </button>
        <button class="btn-outline" onclick="closeModal()">Đóng</button>
      </div>
    `;

    // Qty controls
    qs('#modal-qty-minus').onclick = () => {
      const el = qs('#modal-qty');
      el.textContent = Math.max(1, +el.textContent - 1);
    };
    qs('#modal-qty-plus').onclick = () => {
      const el = qs('#modal-qty');
      el.textContent = +el.textContent + 1;
    };
    qs('#modal-add-cart').onclick = async (ev) => {
      const qty = +qs('#modal-qty').textContent;
      await addToCart(p.id, qty, ev.currentTarget);
      closeModal();
    };
  } catch {
    body.innerHTML = '<p style="color:var(--danger);text-align:center;padding:2rem">Không thể tải thông tin sản phẩm</p>';
  }
}

function closeModal() {
  qs('#product-modal').classList.add('hidden');
  document.body.style.overflow = '';
}

qs('#modal-close').addEventListener('click', closeModal);
qs('#modal-backdrop').addEventListener('click', closeModal);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ════════════════════════════════════════════════════════════
//  CART
// ════════════════════════════════════════════════════════════
async function addToCart(productId, quantity = 1, btn = null) {
  if (btn) { btn.disabled = true; btn.textContent = '…'; }
  try {
    // Get product info first (denormalised snapshot for cart)
    const resp = await apiGet(`${API.products}/${productId}/`);
    const p = resp.data || resp;

    await apiPost(`${API.cart}/add/`, {
      product_id:    p.id,
      product_sku:   p.sku || '',
      product_name:  p.name,
      product_image: p.images?.[0] || '',
      unit_price:    p.base_price,
      quantity,
    });

    toast(`Đã thêm "${p.name}" vào giỏ hàng`, 'success');
    loadCartBadge();
  } catch (err) {
    toast(err?.detail || 'Không thể thêm vào giỏ hàng', 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '+ Thêm vào giỏ'; }
  }
}

async function loadCartBadge() {
  try {
    const data = await apiGet(`${API.cart}/me/`);
    const items = data.data?.items || data.items || [];
    const count = items.reduce((s, i) => s + i.quantity, 0);
    updateCartBadge(count);
  } catch {}
}

function updateCartBadge(count) {
  const badge = qs('#cart-badge');
  badge.textContent = count > 0 ? count : '';
  State.cartCount = count;
}

async function loadCart() {
  const list  = qs('#cart-items-list');
  const sumWrap = qs('#cart-summary-wrap');

  list.innerHTML = '<div class="loading-cell" style="padding:2rem;text-align:center">Đang tải giỏ hàng…</div>';

  try {
    const data = await apiGet(`${API.cart}/me/`);
    const cart  = data.data || data;
    const items = cart.items || [];

    if (!items.length) {
      list.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">🛒</span>
          <h3>Giỏ hàng đang trống</h3>
          <p>Thêm sản phẩm vào giỏ để bắt đầu mua sắm</p>
          <button class="btn-primary" data-page="products">Khám phá sản phẩm</button>
        </div>`;
      sumWrap.style.display = 'none';
      updateCartBadge(0);
      return;
    }

    list.innerHTML = items.map(item => {
      const img = item.product_image
        ? `<img src="${item.product_image}" alt="${item.product_name}" style="width:100%;height:100%;object-fit:cover" />`
        : '📦';
      return `
        <div class="cart-item" data-item-id="${item.id}">
          <div class="cart-item-img">${img}</div>
          <div class="cart-item-info">
            <div class="cart-item-name" style="cursor:pointer" onclick="navigateToProductDetail('${item.product_id}')">${item.product_name}</div>
            <div class="cart-item-price">${fmt.vnd(item.unit_price)} / sản phẩm</div>
          </div>
          <div class="qty-control">
            <button class="qty-btn" onclick="updateCartItemQty('${item.id}', ${item.quantity - 1})">−</button>
            <span class="qty-value">${item.quantity}</span>
            <button class="qty-btn" onclick="updateCartItemQty('${item.id}', ${item.quantity + 1})">+</button>
            <button class="btn-ghost" style="color:var(--danger);margin-left:auto;padding:4px" onclick="removeCartItem('${item.id}')" title="Xóa">🗑</button>
          </div>
          <div class="cart-item-subtotal">${fmt.vnd(item.unit_price * item.quantity)}<br>
          </div>
        </div>
      `;
    }).join('');

    const total = items.reduce((s, i) => s + parseFloat(i.unit_price) * i.quantity, 0);
    qs('#cart-subtotal').textContent = fmt.vnd(total);
    qs('#cart-total').textContent    = fmt.vnd(total);
    sumWrap.style.display = 'block';
    updateCartBadge(items.reduce((s,i)=>s+i.quantity, 0));
  } catch {
    list.innerHTML = '<div class="loading-cell">Không thể tải giỏ hàng</div>';
  }
}

async function removeCartItem(itemId) {
  try {
    await apiDelete(`${API.cart}/remove/${itemId}/`);
    toast('Đã xóa sản phẩm khỏi giỏ hàng', 'success');
    loadCart();
  } catch {
    toast('Không thể xóa sản phẩm', 'error');
  }
}

async function updateCartItemQty(itemId, newQty) {
  if (newQty <= 0) {
     return removeCartItem(itemId);
  }
  try {
    await apiFetch(`${API.cart}/update/${itemId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity: newQty })
    });
    loadCart();
  } catch (err) {
    toast('Lỗi cập nhật số lượng', 'error');
  }
}

qs('#apply-coupon').addEventListener('click', async () => {
  const code = qs('#coupon-input').value.trim().toUpperCase();
  if (!code) return;
  try {
    const data = await apiPost(`${API.promotions}/coupons/validate/`, { code });
    toast(`Mã "${code}" hợp lệ!`, 'success');
  } catch (err) {
    toast(err?.message || `Mã "${code}" không hợp lệ`, 'error');
  }
});

qs('#checkout-btn').addEventListener('click', () => {
  navigateTo('checkout');
});

// ════════════════════════════════════════════════════════════
//  ORDERS PAGE
// ════════════════════════════════════════════════════════════
async function loadOrders() {
  const tbody = qs('#orders-body');
  tbody.innerHTML = '<tr><td colspan="6" class="loading-cell">Đang tải đơn hàng…</td></tr>';

  try {
    const data = await apiGet(`${API.orders}/?page_size=20`);
    const orders = data.results || [];

    if (!orders.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="loading-cell">Chưa có đơn hàng nào</td></tr>';
      return;
    }

    tbody.innerHTML = orders.map(o => `
      <tr>
        <td><code style="color:var(--primary-h);font-size:.8rem">${o.order_number}</code></td>
        <td>${renderStatus(o.status)}</td>
        <td style="color:var(--text-2)">${o.items?.length ?? '—'} sp</td>
        <td style="font-weight:600">${fmt.vnd(o.total_amount)}</td>
        <td style="color:var(--text-2)">${fmt.date(o.created_at)}</td>
        <td>
          <button class="btn-ghost" onclick="viewOrder('${o.id}')">Chi tiết →</button>
        </td>
      </tr>
    `).join('');
  } catch {
    tbody.innerHTML = '<tr><td colspan="6" class="loading-cell">Không thể tải đơn hàng</td></tr>';
  }
}

function viewOrder(id) {
  toast(`Chi tiết đơn hàng #${id.slice(0,8)} đang được xây dựng`, 'info');
}

// ════════════════════════════════════════════════════════════
//  PROMOTIONS PAGE
// ════════════════════════════════════════════════════════════
qs('#check-coupon-btn').addEventListener('click', async () => {
  const code = qs('#check-coupon-input').value.trim().toUpperCase();
  const resultEl = qs('#coupon-result');
  if (!code) { resultEl.innerHTML = ''; return; }

  resultEl.innerHTML = '<p style="color:var(--text-3);margin-top:.75rem">Đang kiểm tra…</p>';
  try {
    const data = await apiPost(`${API.promotions}/coupons/validate/`, { code });
    const c = data.data;
    const discount = c.discount;
    let discountText = '';
    if (c.coupon_type === 'percentage') discountText = `Giảm ${discount?.value}%`;
    else if (c.coupon_type === 'fixed')  discountText = `Giảm ${fmt.vnd(discount?.value)}`;
    else discountText = 'Miễn phí vận chuyển';

    resultEl.innerHTML = `
      <div class="coupon-valid" style="margin-top:.75rem">
        <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem">
          <span style="font-size:1.5rem">🎉</span>
          <div>
            <div style="font-weight:700;font-size:1rem">${c.code}</div>
            <div style="color:var(--success);font-weight:600">${discountText}</div>
          </div>
        </div>
        <div style="font-size:.825rem;color:var(--text-2)">${c.name}</div>
        ${c.expires_at ? `<div style="font-size:.775rem;color:var(--text-3);margin-top:.25rem">Hết hạn: ${fmt.date(c.expires_at)}</div>` : ''}
      </div>
    `;
  } catch (err) {
    resultEl.innerHTML = `
      <div class="coupon-invalid" style="margin-top:.75rem">
        <span style="font-size:1.2rem">❌</span>
        <span style="margin-left:.5rem">${err?.message || 'Mã khuyến mãi không hợp lệ hoặc đã hết hạn'}</span>
      </div>
    `;
  }
});

// ════════════════════════════════════════════════════════════
//  PROFILE PAGE
// ════════════════════════════════════════════════════════════
async function loadProfile() {
  try {
    const me = await apiGet(`${API.auth}/me/`);
    State.user = me.data || me;
    updateUserUI();
  } catch {}
}

qs('#profile-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = qs('#profile-form button[type="submit"]');
  btn.disabled = true; btn.textContent = 'Đang lưu…';
  try {
    const data = await apiPut(`${API.auth}/me/`, {
      full_name: qs('#prof-name').value.trim(),
      phone:     qs('#prof-phone').value.trim(),
    });
    State.user = data.data || data;
    updateUserUI();
    toast('Cập nhật thông tin thành công!', 'success');
  } catch {
    toast('Không thể cập nhật thông tin', 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Lưu thay đổi';
  }
});

qs('#password-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = qs('#password-form button[type="submit"]');
  btn.disabled = true; btn.textContent = 'Đang đổi…';
  try {
    await apiPut(`${API.auth}/change-password/`, {
      old_password: qs('#old-password').value,
      new_password: qs('#new-password').value,
    });
    toast('Đổi mật khẩu thành công!', 'success');
    qs('#password-form').reset();
  } catch (err) {
    toast(err?.old_password?.[0] || err?.detail || 'Đổi mật khẩu thất bại', 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Đổi mật khẩu';
  }
});

// ════════════════════════════════════════════════════════════
//  HELPERS
// ════════════════════════════════════════════════════════════
function renderStatus(status) {
  const labels = {
    pending:    'Chờ xác nhận',
    confirmed:  'Đã xác nhận',
    processing: 'Đang xử lý',
    shipped:    'Đang giao',
    delivered:  'Đã giao',
    cancelled:  'Đã hủy',
    refunded:   'Hoàn tiền',
  };
  return `<span class="status status-${status}">${labels[status] || status}</span>`;
}

// ════════════════════════════════════════════════════════════
//  MANAGE CATEGORIES
// ════════════════════════════════════════════════════════════
let categoriesData = [];

async function loadManageCategories() {
  const tbody = qs('#manage-categories-body');
  const search = qs('#manage-category-search').value.trim();
  
  tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">Đang tải…</td></tr>';
  
  let url = `${API.products}/categories/?page_size=100`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  
  try {
    const data = await apiGet(url);
    categoriesData = data.results || [];
    
    // Update parent select options early
    const select = qs('#cat-parent');
    select.innerHTML = '<option value="">-- Không có --</option>' + categoriesData.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    if (!categoriesData.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-3)">Không tìm thấy danh mục nào.</td></tr>`;
      return;
    }

    tbody.innerHTML = categoriesData.map(c => `
      <tr>
        <td><code style="color:var(--text-2);font-size:.8rem;">${c.id.slice(0,6)}…</code></td>
        <td>${c.image ? `<img src="${c.image}" style="width:32px;height:32px;border-radius:4px;object-fit:cover" />` : '📁'}</td>
        <td style="font-weight:600">${c.name}</td>
        <td><code style="background:var(--bg-1);padding:2px 6px;border-radius:4px;">${c.slug}</code></td>
        <td>${c.sort_order}</td>
        <td>${c.is_active ? '<span class="status status-delivered">Bật</span>' : '<span class="status status-cancelled">Tắt</span>'}</td>
        <td>
          <button class="btn-ghost" style="padding:4px 8px;font-size:0.875rem" onclick="openCategoryModal('${c.id}')">Sửa</button>
          <button class="btn-ghost" style="padding:4px 8px;font-size:0.875rem;color:var(--danger)" onclick="deleteCategory('${c.id}')">Xóa</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="7" class="loading-cell" style="color:var(--danger)">Lỗi tải danh mục.</td></tr>';
  }
}

qs('#manage-category-search').addEventListener('input', () => {
  clearTimeout(productSearchTimer);
  productSearchTimer = setTimeout(() => loadManageCategories(), 400);
});

qs('#btn-create-category').addEventListener('click', () => openCategoryModal());

function openCategoryModal(catId = null) {
  const modal = qs('#category-modal');
  const cat   = categoriesData.find(c => c.id === catId);
  
  qs('#category-modal-title').textContent = cat ? 'Sửa danh mục' : 'Thêm danh mục';
  qs('#cat-id').value       = cat?.id || '';
  qs('#cat-name').value     = cat?.name || '';
  qs('#cat-slug').value     = cat?.slug || '';
  qs('#cat-image').value    = cat?.image || '';
  qs('#cat-parent').value   = cat?.parent || '';
  qs('#cat-sort').value     = cat?.sort_order || 0;
  qs('#cat-desc').value     = cat?.description || '';
  qs('#cat-active').checked = cat ? cat.is_active : true;
  
  modal.classList.remove('hidden');
}

qs('#category-modal-close').addEventListener('click', closeCategoryModal);
qs('#category-modal-cancel').addEventListener('click', closeCategoryModal);
qs('#category-modal-backdrop').addEventListener('click', closeCategoryModal);

function closeCategoryModal() {
  qs('#category-modal').classList.add('hidden');
}

qs('#category-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = qs('#cat-id').value;
  const payload = {
    name: qs('#cat-name').value.trim(),
    slug: qs('#cat-slug').value.trim(),
    image: qs('#cat-image').value.trim(),
    parent: qs('#cat-parent').value || null,
    sort_order: parseInt(qs('#cat-sort').value) || 0,
    description: qs('#cat-desc').value.trim(),
    is_active: qs('#cat-active').checked
  };

  const btn = e.target.querySelector('button[type="submit"]');
  btn.disabled = true; btn.textContent = 'Đang lưu…';

  try {
    if (id) {
      await apiPut(`${API.products}/categories/${id}/`, payload);
      toast('Sửa danh mục thành công', 'success');
    } else {
      await apiPost(`${API.products}/categories/`, payload);
      toast('Thêm danh mục thành công', 'success');
    }
    closeCategoryModal();
    loadManageCategories();
  } catch (err) {
    toast('Lỗi lưu danh mục: ' + (err?.detail || err?.name?.[0] || err?.slug?.[0] || ''), 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Lưu danh mục';
  }
});

async function deleteCategory(id) {
  if (!confirm('Bạn có chắc muốn xóa danh mục này?')) return;
  try {
    await apiDelete(`${API.products}/categories/${id}/`);
    toast('Xóa thành công', 'success');
    loadManageCategories();
  } catch {
    toast('Không thể xóa danh mục. Có thể vẫn còn sản phẩm con.', 'error');
  }
}

// ════════════════════════════════════════════════════════════
//  MANAGE PRODUCTS
// ════════════════════════════════════════════════════════════
let manageProductsData = [];

async function loadManageProducts(page = 1) {
  const tbody  = qs('#manage-products-body');
  const search = qs('#manage-product-search').value.trim();
  const cat    = qs('#manage-product-category').value;
  
  tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">Đang tải…</td></tr>';
  
  let url = `${API.products}/?page=${page}&page_size=12`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (cat)    url += `&category=${encodeURIComponent(cat)}`;
  
  try {
    const data = await apiGet(url);
    manageProductsData = data.results || [];
    
    // Render pagination container specifically for manage-products
    renderManagePagination(data.count, page, 12);
    
    // Also fill filter categories if not filled
    const catSelect = qs('#manage-product-category');
    if (catSelect.options.length <= 1) {
      apiGet(`${API.products}/categories/?page_size=100`).then(res => {
         catSelect.innerHTML = '<option value="">Tất cả danh mục</option>' + 
           (res.results || []).map(c => `<option value="${c.slug}">${c.name}</option>`).join('');
      }).catch(()=>{});
    }
    
    if (!manageProductsData.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-3)">Không tìm thấy sản phẩm.</td></tr>`;
      return;
    }

    tbody.innerHTML = manageProductsData.map(p => `
      <tr>
        <td>${p.images?.[0] ? `<img src="${p.images[0]}" style="width:32px;height:32px;border-radius:4px;object-fit:cover" />` : '🛍️'}</td>
        <td style="font-weight:600;max-width:250px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${p.name}">${p.name}</td>
        <td><code style="color:var(--text-2);font-size:.8rem;">${p.sku}</code></td>
        <td>${p.category_name || '—'}</td>
        <td style="font-weight:600">${fmt.vnd(p.base_price)}</td>
        <td>${p.is_active ? '<span class="status status-delivered">Bật</span>' : '<span class="status status-cancelled">Tắt</span>'}</td>
        <td>
          <button class="btn-ghost" style="padding:4px 8px;font-size:0.875rem" onclick="toggleProductActive('${p.id}')">${p.is_active?'Tắt':'Bật'}</button>
          <button class="btn-ghost" style="padding:4px 8px;font-size:0.875rem;color:var(--primary-h)" onclick="openManageProductModal('${p.id}')">Sửa</button>
          <button class="btn-ghost" style="padding:4px 8px;font-size:0.875rem;color:var(--danger)" onclick="deleteProduct('${p.id}')">Xóa</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="7" class="loading-cell" style="color:var(--danger)">Lỗi tải sản phẩm.</td></tr>';
  }
}

function renderManagePagination(total, current, pageSize) {
  const container = qs('#manage-products-pagination');
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) { container.innerHTML = ''; return; }

  let btns = '';
  btns += `<button class="page-btn" onclick="loadManageProducts(${current-1})" ${current===1?'disabled':''}>←</button>`;
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || Math.abs(i - current) <= 2) {
      btns += `<button class="page-btn ${i===current?'active':''}" onclick="loadManageProducts(${i})">${i}</button>`;
    } else if (Math.abs(i - current) === 3) {
      btns += `<span style="color:var(--text-3);padding:0 .25rem">…</span>`;
    }
  }
  btns += `<button class="page-btn" onclick="loadManageProducts(${current+1})" ${current===totalPages?'disabled':''}>→</button>`;
  container.innerHTML = btns;
}

qs('#manage-product-search').addEventListener('input', () => {
  clearTimeout(productSearchTimer);
  productSearchTimer = setTimeout(() => loadManageProducts(1), 400);
});
qs('#manage-product-category').addEventListener('change', () => loadManageProducts(1));
qs('#btn-create-product').addEventListener('click', () => openManageProductModal());

async function toggleProductActive(id) {
  try {
    await apiPost(`${API.products}/${id}/toggle-active/`, {});
    loadManageProducts();
  } catch (err) {
    toast('Lỗi cập nhật trạng thái', 'error');
  }
}

async function fetchProductDetail(id) {
  const data = await apiGet(`${API.products}/${id}/`);
  return data.data || data;
}

async function openManageProductModal(prodId = null) {
  const modal = qs('#product-crud-modal');
  let p = null;
  
  if (prodId) {
    try { p = await fetchProductDetail(prodId); } catch { return toast('Không thể tải dữ liệu chi tiết', 'error'); }
  }
  
  // Fill categories
  apiGet(`${API.products}/categories/?page_size=100`).then(res => {
     qs('#prod-category').innerHTML = '<option value="">-- Không có --</option>' + (res.results || []).map(c => `<option value="${c.id}">${c.name}</option>`).join('');
     if (p?.category) qs('#prod-category').value = p.category;
  }).catch(()=>{});

  qs('#product-crud-modal-title').textContent = p ? 'Sửa sản phẩm' : 'Thêm sản phẩm';
  qs('#prod-id').value            = p?.id || '';
  qs('#prod-name').value          = p?.name || '';
  qs('#prod-sku').value           = p?.sku || '';
  qs('#prod-slug').value          = p?.slug || '';
  qs('#prod-price').value         = p?.base_price || '';
  qs('#prod-compare-price').value = p?.compare_price || '';
  qs('#prod-images').value        = (p?.images || []).join('\n');
  qs('#prod-desc').value          = p?.description || '';
  qs('#prod-tags').value          = (p?.tags || []).join(', ');
  qs('#prod-active').checked      = p ? p.is_active : true;
  
  modal.classList.remove('hidden');
}

qs('#product-crud-modal-close').addEventListener('click', closeProductModal);
qs('#product-crud-modal-cancel').addEventListener('click', closeProductModal);
qs('#product-crud-modal-backdrop').addEventListener('click', closeProductModal);

function closeProductModal() { qs('#product-crud-modal').classList.add('hidden'); }

qs('#product-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = qs('#prod-id').value;
  const rawImages = qs('#prod-images').value.split('\n').map(i => i.trim()).filter(Boolean);
  const rawTags   = qs('#prod-tags').value.split(',').map(t => t.trim()).filter(Boolean);
  
  const payload = {
    name: qs('#prod-name').value.trim(),
    sku: qs('#prod-sku').value.trim(),
    slug: qs('#prod-slug').value.trim(),
    category: qs('#prod-category').value || null,
    base_price: parseFloat(qs('#prod-price').value),
    compare_price: parseFloat(qs('#prod-compare-price').value) || null,
    description: qs('#prod-desc').value.trim(),
    images: rawImages,
    tags: rawTags,
    is_active: qs('#prod-active').checked,
  };

  const btn = e.target.querySelector('button[type="submit"]');
  btn.disabled = true; btn.textContent = 'Đang lưu…';

  try {
    if (id) {
      await apiPut(`${API.products}/${id}/`, payload);
      toast('Sửa sản phẩm thành công', 'success');
    } else {
      await apiPost(`${API.products}/`, payload);
      toast('Thêm sản phẩm thành công', 'success');
    }
    closeProductModal();
    loadManageProducts();
  } catch (err) {
    toast('Lỗi lưu sản phẩm: ' + (err?.detail || err?.sku?.[0] || err?.slug?.[0] || ''), 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Lưu sản phẩm';
  }
});

async function deleteProduct(id) {
  if (!confirm('Chắc chắn xóa sản phẩm này? Thao tác không thể hoàn tác!')) return;
  try {
    await apiDelete(`${API.products}/${id}/`);
    toast('Xóa thành công', 'success');
    loadManageProducts();
  } catch {
    toast('Khoong thể xóa', 'error');
  }
}

// ════════════════════════════════════════════════════════════
//  PRODUCT DETAIL AND REVIEWS
// ════════════════════════════════════════════════════════════

async function loadProductDetailPage() {
  if (!State.currentProductId) return navigateTo('products');
  const id = State.currentProductId;
  
  // reset qty
  qs('#pd-qty').textContent = '1';
  
  // Show Write Review Form if logged in
  if (State.user) {
    qs('#pd-write-review-container').style.display = 'block';
    qs('#pd-review-text').value = '';
    setReviewStars(5);
  } else {
    qs('#pd-write-review-container').style.display = 'none';
  }
  
  // Load Product info
  try {
    const p = await fetchProductDetail(id);
    const img = p.images?.[0]
      ? `<img src="${p.images[0]}" alt="${p.name}" style="width:100%;height:100%;object-fit:cover" />`
      : '🛍️';
      
    qs('#pd-image-container').innerHTML = img;
    qs('#pd-name').textContent = p.name;
    qs('#pd-sku').textContent = p.sku;
    
    if (p.category_name) {
      qs('#pd-category-wrap').style.display = 'inline';
      qs('#pd-category').textContent = p.category_name;
    } else {
       qs('#pd-category-wrap').style.display = 'none';
    }
    
    qs('#pd-price').textContent = fmt.vnd(p.base_price);
    if (p.compare_price && p.compare_price > p.base_price) {
      qs('#pd-compare-price').textContent = fmt.vnd(p.compare_price);
      qs('#pd-compare-price').style.display = 'inline';
    } else {
      qs('#pd-compare-price').style.display = 'none';
    }
    
    qs('#pd-desc').textContent = p.description || 'Chưa có thông tin mô tả chi tiết sản phẩm này.';
    
    // Attributes
    const attrs = (p.attributes || []).map(a => 
      `<span style="background:var(--bg-3);padding:0.25rem 0.75rem;border-radius:12px;font-size:0.875rem;">${a.attribute_name}: <span style="font-weight:600">${a.value}</span></span>`
    ).join('');
    qs('#pd-attributes').innerHTML = attrs;
    
    // Add to cart bind
    qs('#pd-add-cart').onclick = async (e) => {
       const qty = parseInt(qs('#pd-qty').textContent);
       await addToCart(p.id, qty, e.currentTarget);
    };
    
  } catch (err) {
    toast('Không thể tải thông tin chi tiết sản phẩm. Có thể nó đã bị xóa.', 'error');
    return navigateTo('products');
  }
  
  loadProductReviews(id);
}

// Review QTY logic
qs('#pd-qty-minus').onclick = () => {
    const el = qs('#pd-qty');
    el.textContent = Math.max(1, +el.textContent - 1);
};
qs('#pd-qty-plus').onclick = () => {
    const el = qs('#pd-qty');
    el.textContent = +el.textContent + 1;
};

// Reviews loading Logic
async function loadProductReviews(productId) {
  const listEl = qs('#pd-reviews-list');
  listEl.innerHTML = '<div class="loading-cell">Đang tải đánh giá...</div>';
  qs('#pd-avg-rating').textContent = '0';
  qs('#pd-total-reviews').textContent = 'Chưa có review nào';

  try {
    const data = await apiGet(`${API.reviews}/?product_id=${productId}&page_size=100`);
    const reviews = data.results || [];
    
    qs('#pd-total-reviews').textContent = `${reviews.length} đánh giá`;
    
    if (reviews.length === 0) {
      listEl.innerHTML = '<div style="color: var(--text-3); text-align: center; padding: 2rem 0">Chưa có đánh giá nào cho sản phẩm này. Hãy là người đầu tiên!</div>';
      return;
    }
    
    const avg = reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length;
    qs('#pd-avg-rating').textContent = avg.toFixed(1);
    
    listEl.innerHTML = reviews.map(r => `
      <div style="padding: 1.5rem; background: var(--bg-1); border-radius: 12px; border: 1px solid var(--border-1)">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 0.5rem">
           <div>
             <div style="font-weight:600; margin-bottom:0.25rem">${r.user_name}</div>
             <div style="color:#ff9f43; font-size:1rem; letter-spacing: 2px;">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</div>
           </div>
           <div style="font-size:0.8rem; color:var(--text-3)">${fmt.date(r.created_at)}</div>
        </div>
        <p style="color:var(--text-1); line-height:1.5;">${r.body || ''}</p>
      </div>
    `).join('');
    
  } catch (err) {
    listEl.innerHTML = '<div style="color: var(--danger); padding: 1rem 0">Không thể tải đánh giá sản phẩm. Thử lại sau.</div>';
  }
}

// Handling Stars Selection
function setReviewStars(v) {
  qs('#pd-rating-input').value = v;
  const stars = qsa('#pd-star-select span');
  stars.forEach((s, i) => {
    s.textContent = i < v ? '★' : '☆';
  });
}
qsa('#pd-star-select span').forEach(el => {
  el.addEventListener('click', () => {
    const val = parseInt(el.getAttribute('data-val'));
    setReviewStars(val);
  });
});

// Submit New Review
qs('#pd-review-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = qs('#pd-submit-review');
  const rating = qs('#pd-rating-input').value;
  const bodyText = qs('#pd-review-text').value.trim();
  const productId = State.currentProductId;
  
  if (!productId) return;
  
  btn.disabled = true;
  btn.textContent = 'Đang gửi...';
  
  try {
     await apiPost(`${API.reviews}/`, {
       product_id: productId,
       order_id: null,
       rating: parseInt(rating),
       body: bodyText,
       title: "Đánh giá từ khách hàng"
     });
     toast('Gửi đánh giá thành công!', 'success');
     qs('#pd-review-text').value = '';
     setReviewStars(5);
     // Reload reviews smoothly
     loadProductReviews(productId);
  } catch (err) {
     toast('Lỗi: ' + (err?.message || err?.detail || 'Không thể gửi đánh giá'), 'error');
  } finally {
     btn.disabled = false;
     btn.textContent = 'Gửi đánh giá';
  }
});

// ════════════════════════════════════════════════════════════
//  CHECKOUT & PAYMENT
// ════════════════════════════════════════════════════════════
let checkoutCartItems = [];
let checkoutTotal = 0;

async function loadCheckoutPage() {
  const listEl = qs('#checkout-items-list');
  listEl.innerHTML = '<div class="loading-cell">Đang tải giỏ hàng...</div>';
  
  try {
    const data = await apiGet(`${API.cart}/me/`);
    const cart = data.data || data;
    checkoutCartItems = cart.items || [];
    
    if (checkoutCartItems.length === 0) {
      toast('Giỏ hàng trống, không thể thanh toán!', 'warning');
      return navigateTo('cart');
    }
    
    listEl.innerHTML = checkoutCartItems.map(item => `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.75rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-1);">
        <div style="display:flex; gap: 0.5rem; align-items:center;">
          <img src="${item.product_image || ''}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover; background: var(--bg-3)" />
          <div>
            <div style="font-weight: 600; font-size: 0.85rem">${item.product_name}</div>
            <div style="color: var(--text-2); font-size: 0.75rem">Số lượng: ${item.quantity}</div>
          </div>
        </div>
        <div style="font-weight: 600; font-size: 0.85rem">${fmt.vnd(item.unit_price * item.quantity)}</div>
      </div>
    `).join('');
    
    checkoutTotal = checkoutCartItems.reduce((acc, curr) => acc + (curr.unit_price * curr.quantity), 0);
    qs('#checkout-subtotal').textContent = fmt.vnd(checkoutTotal);
    qs('#checkout-total').textContent = fmt.vnd(checkoutTotal);
    
    // Auto fill user info if available
    if (State.user) {
       if (!qs('#ch-name').value) qs('#ch-name').value = State.user.full_name || '';
       if (!qs('#ch-phone').value) qs('#ch-phone').value = State.user.phone || '';
    }
    
  } catch (err) {
    toast('Không thể tải giỏ hàng', 'error');
    navigateTo('cart');
  }
}

qs('#checkout-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = qs('#btn-submit-order');
  
  // Validate
  if (checkoutCartItems.length === 0) return toast('Giỏ hàng rỗng.', 'error');
  
  btn.disabled = true;
  btn.innerHTML = 'Đang xử lý...';
  
  const shippingAddress = {
     name: qs('#ch-name').value.trim(),
     phone: qs('#ch-phone').value.trim(),
     address: qs('#ch-address').value.trim()
  };
  
  const paymentMethodInfo = qs('input[name="ch-payment"]:checked');
  const paymentMethod = paymentMethodInfo ? paymentMethodInfo.value : 'cod';
  
  try {
     // 1. Gửi sang Order Service
     const orderRes = await apiPost(`${API.orders}/checkout/`, {
         shipping_address: shippingAddress,
         payment_method: paymentMethod,
         items: checkoutCartItems.map(i => ({
             product_id: i.product_id,
             product_name: i.product_name,
             product_image: i.product_image,
             unit_price: Number(i.unit_price),
             quantity: Number(i.quantity)
         }))
     });
     
     const orderId = orderRes.data.id;
     
     // 2. Gửi sang Payment Service
     const txnStatus = paymentMethod === 'cod' ? 'pending' : 'completed';
     await apiPost(`${API.payments}/transactions/`, {
         order_id: orderId,
         amount: checkoutTotal,
         status: txnStatus
     });
     
     // 3. Clear Cart
     await apiDelete(`${API.cart}/clear/`);
     
     // Hoàn tất
     toast('🎉 Đặt hàng thành công!', 'success');
     qs('#checkout-form').reset();
     checkoutCartItems = [];
     navigateTo('orders');
     
  } catch (err) {
     toast('Lỗi khi đặt hàng: ' + (err?.message || err?.detail || ''), 'error');
  } finally {
     btn.disabled = false;
     btn.innerHTML = '💳 Đặt hàng ngay';
  }
});

// ════════════════════════════════════════════════════════════
//  BOOTSTRAP
// ════════════════════════════════════════════════════════════
async function boot() {
  if (State.accessToken) {
    try {
      await initApp();
    } catch {
      showAuth();
    }
  } else {
    showAuth();
  }

  // Preload categories for filter
  loadCategories();
}

boot();
