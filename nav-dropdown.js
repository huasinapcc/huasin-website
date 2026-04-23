/**
 * Dynamic Nav Dropdown for Huasin Website
 * Fetches therapist data from Google Sheets and populates the nav dropdown.
 * Uses the standard 'therapists' sheet as the data source.
 */
(function() {
  const SHEET_ID = '1o0di_U7q_NKiDuwkHEnUqlX2QQNxAeXR1TKpAJl0WAQ';
  const SHEET_NAME = 'therapists';
  const URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=${encodeURIComponent(SHEET_NAME)}`;

  async function initDropdown() {
    const dropdownContainer = document.getElementById('navTherapistDropdown');
    if (!dropdownContainer) return;

    try {
      const res = await fetch(URL);
      const text = await res.text();
      const json = JSON.parse(text.replace(/^.*?({.*}).*$/s,'$1'));
      
      // Determine columns
      const cols = json.table.cols.map(c => (c.label || '').toLowerCase().trim());
      const rows = json.table.rows || [];

      // Map rows to objects
      const therapists = rows.map(row => {
        const obj = {};
        cols.forEach((col, i) => {
          if (col) {
            obj[col] = row.c[i]?.v ?? '';
          }
        });
        return obj;
      }).filter(t => String(t.active).toUpperCase() === 'TRUE' && t.name);

      // Render Dropdown Items
      if (therapists.length > 0) {
        const innerHtml = therapists.map(t => {
          return `<a href="therapist.html?id=${t.id}">${t.name} ${t.title || ''}</a>`;
        }).join('');
        
        dropdownContainer.innerHTML = `<div class="dropdown-menu-inner">${innerHtml}</div>`;
      } else {
        dropdownContainer.innerHTML = `<div class="dropdown-menu-inner"><a href="team.html">查看所有心理師</a></div>`;
      }
    } catch (e) {
      console.error('Failed to load nav therapists:', e);
      // Fallback: Just show a link to the team page
      dropdownContainer.innerHTML = `<div class="dropdown-menu-inner"><a href="team.html">查看更多心理師</a></div>`;
    }
  }

  function initMobileMenu() {
    const nav = document.querySelector('nav');
    const navLinks = nav && nav.querySelector('.nav-links');
    if (!nav || !navLinks) return;

    // Create hamburger button
    const btn = document.createElement('button');
    btn.className = 'nav-hamburger';
    btn.setAttribute('aria-label', '開啟選單');
    btn.innerHTML = '<span></span><span></span><span></span>';

    // Insert before nav-links (or at end of nav)
    nav.appendChild(btn);

    btn.addEventListener('click', () => {
      const isOpen = navLinks.classList.toggle('mobile-open');
      btn.classList.toggle('open', isOpen);
      btn.setAttribute('aria-label', isOpen ? '關閉選單' : '開啟選單');
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    // Close menu when a link is clicked
    navLinks.addEventListener('click', (e) => {
      if (e.target.tagName === 'A') {
        navLinks.classList.remove('mobile-open');
        btn.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  }

  // Handle window load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { initDropdown(); initMobileMenu(); });
  } else {
    initDropdown();
    initMobileMenu();
  }
})();
