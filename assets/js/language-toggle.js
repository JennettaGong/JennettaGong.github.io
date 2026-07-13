(function () {
  const KEY = 'site-language';
  const supported = ['zh', 'en'];
  function preferred() {
    const saved = localStorage.getItem(KEY);
    if (supported.includes(saved)) return saved;
    return navigator.language && navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';
  }
  function apply(lang) {
    if (!supported.includes(lang)) lang = 'en';
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.documentElement.dataset.lang = lang;
    document.querySelectorAll('[data-set-lang]').forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.dataset.setLang === lang));
    });
    localStorage.setItem(KEY, lang);
    window.dispatchEvent(new CustomEvent('site-language-change', { detail: { lang: lang } }));
  }
  document.addEventListener('click', function (event) {
    const button = event.target.closest('[data-set-lang]');
    if (button) {
      event.preventDefault();
      apply(button.dataset.setLang);
    }
  });
  document.addEventListener('DOMContentLoaded', function () { apply(preferred()); });
  window.siteLanguage = { get: preferred, set: apply };
})();
