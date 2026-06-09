// Language toggle
document.addEventListener('DOMContentLoaded', function () {
  const langToggleBtn = document.getElementById('langToggleBtn');
  const langLabel = document.getElementById('langLabel');
  const contentEn = document.getElementById('content-en');
  const contentKo = document.getElementById('content-ko');
  let currentLang = localStorage.getItem('mcp-lang') || 'ko';

  function setLanguage(lang) {
    currentLang = lang;
    document.querySelectorAll('.lang-content').forEach(function (el) { el.classList.remove('active'); });
    if (lang === 'en') {
      if (contentEn) contentEn.classList.add('active');
      if (langLabel) langLabel.textContent = 'EN / KO';
      document.documentElement.lang = 'en';
    } else {
      if (contentKo) contentKo.classList.add('active');
      if (langLabel) langLabel.textContent = 'KO / EN';
      document.documentElement.lang = 'ko';
    }
    localStorage.setItem('mcp-lang', lang);
  }
  if (langToggleBtn) {
    langToggleBtn.addEventListener('click', function () { setLanguage(currentLang === 'ko' ? 'en' : 'ko'); });
  }
  setLanguage(currentLang);

  // Dark mode toggle
  const darkModeToggle = document.getElementById('darkModeToggle');
  let isDark = localStorage.getItem('mcp-dark') === 'true';
  function applyDark(dark) {
    isDark = dark;
    if (dark) {
      document.documentElement.classList.add('dark');
      if (darkModeToggle) darkModeToggle.textContent = 'light_mode';
    } else {
      document.documentElement.classList.remove('dark');
      if (darkModeToggle) darkModeToggle.textContent = 'dark_mode';
    }
    localStorage.setItem('mcp-dark', dark);
  }
  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', function () { applyDark(!isDark); });
  }
  applyDark(isDark);

  // Header shadow on scroll
  var header = document.querySelector('header');
  if (header) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 20) {
        header.classList.add('shadow-md');
        header.classList.remove('shadow-sm');
      } else {
        header.classList.remove('shadow-md');
        header.classList.add('shadow-sm');
      }
    });
  }
});
