const translations = {
    en: { "settings-title": "Settings", "language-label": "Language", "save-btn": "Save Changes", "nav-home": "Home", "nav-settings": "Settings" },
    es: { "settings-title": "Configuraciones", "language-label": "Idioma", "save-btn": "Guardar cambios", "nav-home": "Inicio", "nav-settings": "Configuraciones" },
    fr: { "settings-title": "Paramètres", "language-label": "Langue", "save-btn": "Enregistrer les modifications", "nav-home": "Accueil", "nav-settings": "Paramètres" },
    de: { "settings-title": "Einstellungen", "language-label": "Sprache", "save-btn": "Änderungen speichern", "nav-home": "Startseite", "nav-settings": "Einstellungen" },
    hi: { "settings-title": "सेटिंग्स", "language-label": "भाषा", "save-btn": "परिवर्तन सहेजें", "nav-home": "होम", "nav-settings": "सेटिंग्स" }
};

function setLanguage(lang) {
    localStorage.setItem('language', lang);
    document.querySelectorAll('[data-translate]').forEach(el => {
        const key = el.getAttribute('data-translate');
        if (translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });
}

function loadLanguage() {
    const savedLanguage = localStorage.getItem('language') || 'en';
    setLanguage(savedLanguage);
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.value = savedLanguage;
        languageSelect.addEventListener('change', (event) => {
            setLanguage(event.target.value);
        });
    }
}

document.addEventListener('DOMContentLoaded', loadLanguage);
