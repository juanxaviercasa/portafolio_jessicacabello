/**
 * WP Static Architect - Buscador Estático Instantáneo
 * Cliente Vanilla JS puro (0 dependencias externas)
 * Desarrollado por Xavier Cabello (juan.cabellosalirrosas.com)
 */
(function () {
    'use strict';

    let searchIndex = null;
    let isLoadingIndex = false;
    let selectedIndex = -1;

    // Elementos del DOM
    let triggerBtn, backdrop, input, clearBtn, closeBtn, resultsBox;

    function init() {
        triggerBtn = document.getElementById('wpsa-search-trigger');
        backdrop   = document.getElementById('wpsa-search-backdrop');
        input      = document.getElementById('wpsa-search-input');
        clearBtn   = document.getElementById('wpsa-search-clear');
        closeBtn   = document.getElementById('wpsa-search-close');
        resultsBox = document.getElementById('wpsa-search-results');

        if (!backdrop || !input) return;

        // Atajo global Ctrl + K / Cmd + K
        window.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                toggleModal();
            } else if (e.key === 'Escape' && isModalOpen()) {
                e.preventDefault();
                closeModal();
            }
        });

        if (triggerBtn) {
            triggerBtn.addEventListener('click', openModal);
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                input.value = '';
                clearBtn.style.display = 'none';
                renderEmptyState('Escribe una palabra clave para buscar en todo el contenido estático.');
                input.focus();
            });
        }

        // Cierre al hacer clic en el backdrop fuera del modal
        backdrop.addEventListener('click', function (e) {
            if (e.target === backdrop || e.target.classList.contains('wpsa-search-container')) {
                closeModal();
            }
        });

        // Búsqueda en tiempo real
        input.addEventListener('input', function () {
            const query = input.value.trim();
            if (clearBtn) {
                clearBtn.style.display = query.length > 0 ? 'inline-flex' : 'none';
            }

            if (query.length < 2) {
                renderEmptyState('Escribe al menos 2 caracteres para buscar...');
                return;
            }

            performSearch(query);
        });

        // Navegación con teclado dentro de la lista de resultados
        input.addEventListener('keydown', function (e) {
            const items = resultsBox.querySelectorAll('.wpsa-search-item');
            if (!items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % items.length;
                updateSelection(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                updateSelection(items);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (selectedIndex >= 0 && items[selectedIndex]) {
                    const link = items[selectedIndex].querySelector('a');
                    if (link) link.click();
                }
            }
        });

        // Detectar si el sistema operativo es Mac para cambiar la tecla a "⌘ K"
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const kbd = document.querySelector('.wpsa-search-kbd');
        if (kbd && isMac) {
            kbd.textContent = '⌘ K';
        }
    }

    function isModalOpen() {
        return backdrop && backdrop.style.display !== 'none';
    }

    function toggleModal() {
        if (isModalOpen()) {
            closeModal();
        } else {
            openModal();
        }
    }

    function openModal() {
        if (!backdrop) return;
        backdrop.style.display = 'flex';
        document.body.classList.add('wpsa-search-open');
        input.value = '';
        if (clearBtn) clearBtn.style.display = 'none';
        renderEmptyState('Escribe una palabra clave para buscar en todo el contenido estático.');
        setTimeout(function () { input.focus(); }, 50);

        // Pre-cargar índice si aún no se ha descargado
        loadIndex();
    }

    function closeModal() {
        if (!backdrop) return;
        backdrop.style.display = 'none';
        document.body.classList.remove('wpsa-search-open');
        selectedIndex = -1;
    }

    function getIndexUrl() {
        // Soporte para URLs relativas o root-relative
        const rootAttr = document.body.getAttribute('data-wpsa-root');
        if (rootAttr) {
            return rootAttr.replace(/\/+$/, '') + '/search-index.json';
        }
        return '/search-index.json';
    }

    function loadIndex(callback) {
        if (searchIndex !== null) {
            if (callback) callback(searchIndex);
            return;
        }

        if (isLoadingIndex) return;
        isLoadingIndex = true;

        const url = getIndexUrl();
        fetch(url)
            .then(function (res) {
                if (!res.ok) {
                    // Si falla /search-index.json relativo a raíz, probar relativo al documento
                    return fetch('search-index.json');
                }
                return res;
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                searchIndex = Array.isArray(data) ? data : [];
                isLoadingIndex = false;
                if (callback) callback(searchIndex);
            })
            .catch(function (err) {
                console.warn('[WP Static Architect] No se pudo cargar search-index.json:', err);
                searchIndex = [];
                isLoadingIndex = false;
            });
    }

    function normalizeText(str) {
        if (!str) return '';
        return str
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');
    }

    function performSearch(rawQuery) {
        loadIndex(function (index) {
            const queryNorm = normalizeText(rawQuery);
            const tokens = queryNorm.split(/\s+/).filter(function (t) { return t.length > 0; });

            if (!tokens.length) {
                renderEmptyState('Escribe una palabra clave para buscar...');
                return;
            }

            const results = [];

            for (let i = 0; i < index.length; i++) {
                const item = index[i];
                const titleNorm = normalizeText(item.title || '');
                const excerptNorm = normalizeText(item.excerpt || '');
                const contentNorm = normalizeText(item.content || '');

                let score = 0;

                // Coincidencia exacta de frase
                if (titleNorm.indexOf(queryNorm) !== -1) {
                    score += 50;
                } else if (excerptNorm.indexOf(queryNorm) !== -1) {
                    score += 20;
                }

                // Coincidencia por tokens individuales
                let matchedAllTokens = true;
                for (let j = 0; j < tokens.length; j++) {
                    const token = tokens[j];
                    const inTitle = titleNorm.indexOf(token) !== -1;
                    const inExcerpt = excerptNorm.indexOf(token) !== -1;
                    const inContent = contentNorm.indexOf(token) !== -1;

                    if (inTitle) {
                        score += 15;
                    } else if (inExcerpt) {
                        score += 8;
                    } else if (inContent) {
                        score += 3;
                    } else {
                        matchedAllTokens = false;
                    }
                }

                if (score > 0 && (matchedAllTokens || tokens.length === 1)) {
                    results.push({ item: item, score: score });
                }
            }

            // Ordenar por relevancia descendente
            results.sort(function (a, b) { return b.score - a.score; });

            renderResults(results.slice(0, 15), rawQuery);
        });
    }

    function highlightMatches(text, query) {
        if (!text) return '';
        if (!query) return escapeHtml(text);

        const tokens = query.trim().split(/\s+/).filter(Boolean);
        if (!tokens.length) return escapeHtml(text);

        const regex = new RegExp('(' + tokens.map(escapeRegExp).join('|') + ')', 'gi');
        return escapeHtml(text).replace(regex, '<mark class="wpsa-highlight">$1</mark>');
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function escapeHtml(text) {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return text.replace(/[&<>"']/g, function (m) { return map[m]; });
    }

    function renderResults(results, query) {
        if (!resultsBox) return;

        if (!results.length) {
            resultsBox.innerHTML =
                '<div class="wpsa-search-empty-state">' +
                    '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>' +
                    '<p>No se encontraron resultados para "<strong>' + escapeHtml(query) + '</strong>".</p>' +
                '</div>';
            selectedIndex = -1;
            return;
        }

        let html = '';
        for (let i = 0; i < results.length; i++) {
            const item = results[i].item;
            const highlightedTitle = highlightMatches(item.title, query);
            const highlightedExcerpt = highlightMatches(item.excerpt, query);
            const typeLabel = item.type === 'page' ? 'Página' : 'Artículo';
            const typeClass = item.type === 'page' ? 'badge-page' : 'badge-post';

            html +=
                '<div class="wpsa-search-item" data-index="' + i + '" role="option">' +
                    '<a href="' + escapeHtml(item.url) + '" class="wpsa-search-item-link">' +
                        '<div class="wpsa-item-header">' +
                            '<span class="wpsa-item-title">' + highlightedTitle + '</span>' +
                            '<span class="wpsa-item-badge ' + typeClass + '">' + typeLabel + '</span>' +
                        '</div>' +
                        (item.excerpt ? '<p class="wpsa-item-excerpt">' + highlightedExcerpt + '</p>' : '') +
                        '<div class="wpsa-item-url">' + escapeHtml(item.url) + '</div>' +
                    '</a>' +
                '</div>';
        }

        resultsBox.innerHTML = html;
        selectedIndex = -1;

        // Eventos hover y click
        const itemNodes = resultsBox.querySelectorAll('.wpsa-search-item');
        itemNodes.forEach(function (node, idx) {
            node.addEventListener('mouseenter', function () {
                selectedIndex = idx;
                updateSelection(itemNodes);
            });
        });
    }

    function updateSelection(items) {
        items.forEach(function (item, idx) {
            if (idx === selectedIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }

    function renderEmptyState(message) {
        if (!resultsBox) return;
        resultsBox.innerHTML =
            '<div class="wpsa-search-empty-state">' +
                '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>' +
                '<p>' + escapeHtml(message) + '</p>' +
            '</div>';
        selectedIndex = -1;
    }

    // Inicializar al cargar el DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
