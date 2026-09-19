/**
 * WP Static Architect - Supabase Comments Client
 * Implementación en Vanilla JavaScript ligera (sin dependencias).
 */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', initComments);

    function initComments() {
        const root = document.getElementById('wpsa-comments-root');
        if (!root) return;

        const postSlug = root.dataset.postSlug || 'home';
        const supabaseUrl = (root.dataset.supabaseUrl || '').replace(/\/+$/, '');
        const supabaseKey = root.dataset.supabaseKey || '';
        const autoApprove = root.dataset.autoApprove === 'true';

        if (!supabaseUrl || !supabaseKey) {
            console.warn('[WP Static Architect] Faltan credenciales públicas de Supabase.');
            return;
        }

        const commentsList = document.getElementById('wpsa-comments-list');
        const countBadge = document.getElementById('wpsa-comments-count');
        const form = document.getElementById('wpsa-comment-form');
        const submitBtn = document.getElementById('wpsa-submit-btn');
        const formAlert = document.getElementById('wpsa-form-alert');

        // Cargar comentarios existentes
        loadComments();

        // Enviar nuevo comentario
        if (form) {
            form.addEventListener('submit', handleFormSubmit);
        }

        /**
         * Consulta y renderiza los comentarios desde Supabase
         */
        async function loadComments() {
            try {
                const endpoint = `${supabaseUrl}/rest/v1/comments?post_slug=eq.${encodeURIComponent(postSlug)}&is_approved=eq.true&order=created_at.asc`;
                const response = await fetch(endpoint, {
                    method: 'GET',
                    headers: {
                        'apikey': supabaseKey,
                        'Authorization': `Bearer ${supabaseKey}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error(`Error de Supabase: HTTP ${response.status}`);
                }

                const comments = await response.json();
                renderComments(comments);
            } catch (err) {
                console.error('[WP Static Architect] Error al cargar comentarios:', err);
                if (commentsList) {
                    commentsList.innerHTML = '<div class="wpsa-empty-state"><p>No fue posible cargar los comentarios en este momento.</p></div>';
                }
            }
        }

        /**
         * Renderiza el listado de comentarios
         */
        function renderComments(comments) {
            if (!commentsList) return;

            if (countBadge) {
                countBadge.textContent = comments.length;
            }

            if (!comments || comments.length === 0) {
                commentsList.innerHTML = `
                    <div class="wpsa-empty-state">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <p>Aún no hay comentarios. ¡Sé el primero en compartir tu opinión!</p>
                    </div>
                `;
                return;
            }

            commentsList.innerHTML = '';
            comments.forEach(comment => {
                const card = createCommentCard(comment);
                commentsList.appendChild(card);
            });
        }

        /**
         * Genera la tarjeta DOM para un comentario
         */
        function createCommentCard(comment) {
            const card = document.createElement('article');
            card.className = 'wpsa-comment-item';
            card.id = `comment-${comment.id}`;

            const initials = getInitials(comment.author_name);
            const avatarColor = getDeterministicColor(comment.author_name);
            const relativeTime = formatRelativeTime(comment.created_at);

            card.innerHTML = `
                <div class="wpsa-comment-avatar" style="background-color: ${avatarColor};" aria-hidden="true">
                    <span>${escapeHTML(initials)}</span>
                </div>
                <div class="wpsa-comment-body">
                    <header class="wpsa-comment-meta">
                        <strong class="wpsa-comment-author">${escapeHTML(comment.author_name)}</strong>
                        <time class="wpsa-comment-time" datetime="${comment.created_at}">${escapeHTML(relativeTime)}</time>
                    </header>
                    <div class="wpsa-comment-content">
                        <p>${escapeHTML(comment.content).replace(/\n/g, '<br>')}</p>
                    </div>
                </div>
            `;

            return card;
        }

        /**
         * Manejador del envío del formulario
         */
        async function handleFormSubmit(e) {
            e.preventDefault();

            const authorName = (form.author_name.value || '').trim();
            const authorEmail = (form.author_email.value || '').trim();
            const content = (form.content.value || '').trim();

            if (!authorName || !content) {
                showAlert('Por favor completa todos los campos requeridos.', 'error');
                return;
            }

            // Comprobar token de Cloudflare Turnstile si está activo
            const turnstileEl = form.querySelector('.cf-turnstile');
            const turnstileToken = form.querySelector('[name="cf-turnstile-response"]');
            if (turnstileEl && (!turnstileToken || !turnstileToken.value)) {
                showAlert('Por favor completa la verificación de seguridad anti-spam.', 'error');
                return;
            }

            setSubmittingState(true);
            hideAlert();

            try {
                const endpoint = `${supabaseUrl}/rest/v1/comments`;
                const payload = {
                    post_slug: postSlug,
                    author_name: authorName,
                    author_email: authorEmail || null,
                    content: content,
                    is_approved: autoApprove
                };

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'apikey': supabaseKey,
                        'Authorization': `Bearer ${supabaseKey}`,
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    throw new Error(errData.message || `Error HTTP ${response.status}`);
                }

                const result = await response.json();
                form.reset();

                if (autoApprove && result && result.length > 0) {
                    // Quitar estado vacío si existe
                    const emptyState = commentsList.querySelector('.wpsa-empty-state');
                    if (emptyState) emptyState.remove();

                    const newCard = createCommentCard(result[0]);
                    commentsList.appendChild(newCard);

                    if (countBadge) {
                        const current = parseInt(countBadge.textContent, 10) || 0;
                        countBadge.textContent = current + 1;
                    }

                    showAlert('¡Comentario publicado exitosamente!', 'success');
                    newCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    showAlert('¡Gracias por tu comentario! Ha sido enviado para moderación y aparecerá publicado en breve.', 'success');
                }
            } catch (err) {
                console.error('[WP Static Architect] Error al enviar comentario:', err);
                showAlert('Hubo un inconveniente al enviar tu comentario. Por favor intenta de nuevo.', 'error');
            } finally {
                setSubmittingState(false);
                if (window.turnstile && typeof window.turnstile.reset === 'function') {
                    try { window.turnstile.reset(); } catch (e) {}
                }
            }
        }

        function setSubmittingState(isSubmitting) {
            if (!submitBtn) return;
            submitBtn.disabled = isSubmitting;
            submitBtn.classList.toggle('loading', isSubmitting);
        }

        function showAlert(message, type) {
            if (!formAlert) return;
            formAlert.className = `wpsa-alert wpsa-alert-${type}`;
            formAlert.textContent = message;
            formAlert.style.display = 'block';
        }

        function hideAlert() {
            if (!formAlert) return;
            formAlert.style.display = 'none';
        }

        function escapeHTML(str) {
            if (!str) return '';
            return str
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        function getInitials(name) {
            if (!name) return '?';
            const parts = name.trim().split(/\s+/);
            if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
            return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
        }

        function getDeterministicColor(str) {
            const colors = [
                '#4f46e5', '#2563eb', '#0891b2', '#059669',
                '#d97706', '#dc2626', '#7c3aed', '#db2777'
            ];
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                hash = str.charCodeAt(i) + ((hash << 5) - hash);
            }
            return colors[Math.abs(hash) % colors.length];
        }

        function formatRelativeTime(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffSeconds = Math.round((now - date) / 1000);

            if (isNaN(diffSeconds)) return dateString;

            if (diffSeconds < 60) return 'hace un momento';
            if (diffSeconds < 3600) {
                const mins = Math.floor(diffSeconds / 60);
                return `hace ${mins} ${mins === 1 ? 'minuto' : 'minutos'}`;
            }
            if (diffSeconds < 86400) {
                const hours = Math.floor(diffSeconds / 3600);
                return `hace ${hours} ${hours === 1 ? 'hora' : 'horas'}`;
            }
            if (diffSeconds < 2592000) {
                const days = Math.floor(diffSeconds / 86400);
                return `hace ${days} ${days === 1 ? 'día' : 'días'}`;
            }

            return date.toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        }
    }
})();
