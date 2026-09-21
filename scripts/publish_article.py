#!/usr/bin/env python3
"""
Motor editorial automatizado para Jessica Cabello.
Toma el siguiente artículo en cola de _queue/, lo fecha, lo traslada al sitio activo,
actualiza blog/index.html, archivos de categorías, sitemap.xml y search-index.json.
"""

import os
import sys
import re
import json
import shutil
import argparse
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
QUEUE_DIR = os.path.join(REPO_DIR, "_queue")

SPANISH_MONTHS = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

CATEGORY_NAMES = {
    "comunicacion": "Expresión Oral",
    "comprension-lectora": "Comprensión Lectora",
    "atencion-en-el-aula": "Atención en el Aula",
    "escritura-creativa": "Escritura Creativa",
    "pnl-aplicada": "PNL Aplicada",
    "recursos-docentes": "Recursos Docentes",
    "clima-de-aula": "Clima de Aula",
    "biblioteca-practica": "Biblioteca"
}

def format_spanish_date(dt):
    return f"{dt.day} de {SPANISH_MONTHS[dt.month]} de {dt.year}"

def format_iso_date(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

def format_short_date(dt):
    return dt.strftime("%Y-%m-%d")

def publish_one():
    if not os.path.exists(QUEUE_DIR):
        print("Queue directory does not exist.")
        return False

    items = sorted([d for d in os.listdir(QUEUE_DIR) if os.path.isdir(os.path.join(QUEUE_DIR, d))])
    if not items:
        print("La cola de artículos está vacía. Todos los 120 artículos han sido publicados.")
        return False

    item_folder = items[0]
    src_path = os.path.join(QUEUE_DIR, item_folder)
    meta_path = os.path.join(src_path, "meta.json")

    if not os.path.isfile(meta_path):
        print(f"Error: {meta_path} no encontrado.")
        return False

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    slug = meta["slug"]
    num = meta.get("num", 0)
    title = meta["title"]
    excerpt = meta.get("excerpt", "")
    category = meta.get("category", "comunicacion")
    category_name = meta.get("category_name", "Expresión Oral")
    categories = meta.get("categories", [category])
    featured_img = meta.get("featured_img", f"articulo-{num:03d}-destacada.webp")

    now = datetime.now(timezone.utc)
    spanish_date = format_spanish_date(now)
    iso_date = format_iso_date(now)
    short_date = format_short_date(now)

    print(f"\n==========================================")
    print(f"Publicando Articulo #{num:03d}: {title}")
    print(f"Slug: {slug} | Categoria: {category_name}")
    print(f"Fecha: {spanish_date}")
    print(f"==========================================")

RECOMMENDED_SIDEBAR_POSTS = [
    {
        "slug": "alumno-timido-exponer",
        "title": "Alumno tímido: guía en 7 pasos para exponer sin ansiedad",
        "img": "/wp-content/uploads/2026/08/articulo-001-destacada.webp"
    },
    {
        "slug": "dinamicas-de-pnl-hablar-publico",
        "title": "5 dinámicas de PNL para hablar en público en tercer grado",
        "img": "/wp-content/uploads/2026/08/articulo-003-destacada.webp"
    },
    {
        "slug": "estrategias-de-comprension-lectora",
        "title": "Estrategias de comprensión lectora antes, durante y después",
        "img": "/wp-content/uploads/2026/08/articulo-026-destacada.webp"
    },
    {
        "slug": "tecnicas-de-pnl-atencion-aula",
        "title": "Técnicas de PNL para recuperar la atención en el aula",
        "img": "/wp-content/uploads/2026/08/articulo-051-destacada.webp"
    }
]

def apply_editorial_layout_to_html(html, slug, title, cat_slug, cat_name, featured_img, publish_date):
    if 'class="editorial-layout-wrapper"' in html:
        return html

    css_link = '<link rel="stylesheet" href="/wp-content/themes/astra/assets/css/editorial-article.css">'
    if 'editorial-article.css' not in html:
        html = html.replace('</head>', f'{css_link}\n</head>', 1)

    rec_items = []
    for p in RECOMMENDED_SIDEBAR_POSTS:
        if p["slug"] != slug:
            rec_items.append(f'''<li class="widget-recent-item">
  <a href="/{p["slug"]}/">
    <img src="{p["img"]}" alt="{p["title"]}" class="widget-recent-thumb" width="64" height="48" loading="lazy">
    <span class="widget-recent-item-title">{p["title"]}</span>
  </a>
</li>''')
        if len(rec_items) == 3:
            break
    rec_html = "\\n".join(rec_items)

    sidebar_html = f'''<aside class="editorial-sidebar" aria-label="Barra lateral informativa">
  <div class="editorial-widget widget-author">
    <div class="widget-author-header">
      <img src="/wp-content/uploads/2026/09/jessica-cabello-autora-retrato.webp" alt="Jessica Cabello Salirrosas" class="widget-author-avatar" width="76" height="76" loading="lazy">
      <h3 class="widget-author-name">Jessica Cabello</h3>
      <p class="widget-author-subtitle">Docente &middot; Especialista en PNL</p>
    </div>
    <p class="widget-author-bio">
      Docente de Educación Primaria apasionada por la expresión oral, el modelado respetuoso y la comunicación auténtica en el aula. Autora del libro <em>La magia de PNL en el aula</em>.
    </p>
    <a href="/sobre-jessica/" class="widget-btn-secondary">Conocer a Jessica &rarr;</a>
  </div>
  <div class="editorial-widget widget-book">
    <div class="widget-book-badge">Compendio Maestro</div>
    <div class="widget-book-cover-wrap">
      <a href="https://www.amazon.es/MAGIA-PNL-AULA-programaci%C3%B3n-neuroling%C3%BC%C3%ADstica/dp/B0DS9GLGS2" target="_blank" rel="noopener noreferrer">
        <img src="/wp-content/uploads/2026/09/la-magia-de-pnl-en-el-aula-libro-3d-realista-v3.webp" alt="Portada del libro La magia de PNL en el aula" class="widget-book-cover" width="125" height="188" loading="lazy">
      </a>
    </div>
    <h3 class="widget-book-title">La magia de PNL en el aula</h3>
    <p class="widget-book-desc">
      Guía didáctica completa (200 páginas) con 3 sesiones modelo, rúbricas de evaluación oral y herramientas prácticas para tercer grado.
    </p>
    <a href="https://www.amazon.es/MAGIA-PNL-AULA-programaci%C3%B3n-neuroling%C3%BC%C3%ADstica/dp/B0DS9GLGS2" target="_blank" rel="noopener noreferrer" class="widget-btn-primary">
      Ver en Amazon KDP &rarr;
    </a>
    <a href="/el-libro/" class="widget-book-link">Ver índice y capítulos del libro</a>
  </div>
  <div class="editorial-widget widget-resources">
    <div class="widget-resources-icon">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
    </div>
    <h3 class="widget-resources-title">Fichas y R&uacute;bricas PDF</h3>
    <p class="widget-resources-desc">
      Descarga gratis la <strong>R&uacute;brica de Expresi&oacute;n Oral</strong> y la <strong>Plantilla de Diagn&oacute;stico VAK</strong> listas para imprimir.
    </p>
    <a href="/recursos-descargables/" class="widget-btn-outline">
      Descargar Recursos PDF &rarr;
    </a>
  </div>
  <div class="editorial-widget widget-recent-posts">
    <h3 class="widget-recent-title">Lecturas Recomendadas</h3>
    <ul class="widget-recent-list">
      {rec_html}
    </ul>
  </div>
</aside>'''

    words = len(re.findall(r'\\b\\w+\\b', html))
    read_time = max(3, min(12, round(words / 250)))
    clean_title = re.sub(r'<[^>]+>', '', title)
    img_url = f"/wp-content/uploads/2026/08/{featured_img}" if not featured_img.startswith('/') else featured_img

    hero_header = f'''<nav class="editorial-breadcrumbs" aria-label="Ruta de navegación">
  <a href="/">Inicio</a>
  <span class="editorial-breadcrumbs-separator">&rsaquo;</span>
  <a href="/blog/">Blog</a>
  <span class="editorial-breadcrumbs-separator">&rsaquo;</span>
  <a href="/category/{cat_slug}/">{cat_name}</a>
</nav>

<header class="editorial-hero-header">
  <div class="editorial-category-badge">
    <a href="/category/{cat_slug}/">{cat_name}</a>
  </div>
  <h1 class="editorial-title">{title}</h1>
  <div class="editorial-meta-bar">
    <div class="editorial-author">
      <img src="/wp-content/uploads/2026/09/jessica-cabello-autora-retrato.webp" alt="Jessica Cabello Salirrosas" class="editorial-avatar" width="46" height="46" loading="lazy">
      <div class="editorial-author-info">
        <a href="/sobre-jessica/" class="editorial-author-name">Jessica Cabello</a>
        <span class="editorial-author-role">Docente de Primaria &middot; Autora</span>
      </div>
    </div>
    <div class="editorial-meta-divider" aria-hidden="true"></div>
    <div class="editorial-meta-info">
      <span class="editorial-meta-item">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
        {publish_date}
      </span>
      <span class="editorial-meta-item">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        {read_time} min de lectura
      </span>
    </div>
  </div>
  <div class="editorial-featured-media">
    <img src="{img_url}" alt="{clean_title}" class="editorial-featured-img" width="1200" height="675" loading="eager">
    <p class="editorial-featured-caption">Estrategias pedagógicas y recursos prácticos para el aula de comunicación en primaria.</p>
  </div>
</header>'''

    old_header_pattern = re.compile(r'<header class="entry-header\\s*">[\\s\\S]*?</header>')
    html = old_header_pattern.sub(hero_header, html, count=1)

    content_start = re.search(r'<div class="entry-content clear"[^>]*itemprop="text">', html)
    if not content_start:
        content_start = re.search(r'<div class="entry-content clear"[^>]*>', html)

    if content_start:
        start_tag = content_start.group(0)
        html = html.replace(start_tag, f'<div class="editorial-layout-wrapper">\\n<div class="editorial-main-content">\\n{start_tag}', 1)
        article_end = '</article>'
        if article_end in html:
            html = html.replace(article_end, f'</div><!-- .editorial-main-content -->\\n{sidebar_html}\\n</div><!-- .editorial-layout-wrapper -->\\n{article_end}', 1)

    return html

    # 1. Update dates in article index.html
    article_html_path = os.path.join(src_path, "index.html")
    if os.path.isfile(article_html_path):
        with open(article_html_path, "r", encoding="utf-8") as f:
            article_html = f.read()

        # Replace placeholders
        article_html = article_html.replace("{{PUBLISH_DATE_SPANISH}}", spanish_date)
        article_html = article_html.replace("{{PUBLISH_DATE_ISO}}", iso_date)
        article_html = article_html.replace("{{PUBLISH_DATE_SHORT}}", short_date)

        # Apply editorial layout
        article_html = apply_editorial_layout_to_html(article_html, slug, title, category, category_name, featured_img, spanish_date)

        with open(article_html_path, "w", encoding="utf-8") as f:
            f.write(article_html)

    # 2. Destination directory in root
    dest_path = os.path.join(REPO_DIR, slug)
    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)
    shutil.move(src_path, dest_path)
    print(f"[OK] Movido a: /{slug}/")

    # 3. Update blog/index.html
    update_blog_index(slug, num, title, excerpt, categories, category, category_name, featured_img, spanish_date)

    # 4. Update category archive
    update_category_archive(category, slug, num, title, excerpt, category_name, featured_img, spanish_date)

    # 5. Update sitemap.xml
    update_sitemap(slug, short_date)

    # 6. Update search-index.json
    update_search_index(slug, title, excerpt, categories)

    print(f"[OK] Articulo #{num:03d} '{title}' publicado con exito!\n")
    return True

def update_blog_index(slug, num, title, excerpt, categories, category, category_name, featured_img, spanish_date):
    blog_path = os.path.join(REPO_DIR, "blog", "index.html")
    if not os.path.isfile(blog_path):
        return

    with open(blog_path, "r", encoding="utf-8") as f:
        html = f.read()

    cats_str = " ".join(categories)
    cat_links_html = " ".join([f'<a href="/category/{c}/" rel="category tag">{CATEGORY_NAMES.get(c, category_name)}</a>' for c in categories])

    card_html = f'''<article class="post-{num} post type-post status-publish format-standard has-post-thumbnail hentry category-{category} ast-grid-common-col ast-full-width ast-article-post remove-featured-img-padding" id="post-{num}" itemtype="https://schema.org/CreativeWork" itemscope="itemscope" data-categories="{cats_str}">
\t<div class="ast-post-format- blog-layout-4 ast-article-inner">
\t\t<div class="post-content ast-grid-common-col">
\t\t\t<div class="ast-blog-featured-section post-thumb ast-blog-single-element">
\t\t\t\t<div class="post-thumb-img-content post-thumb">
\t\t\t\t\t<a href="/{slug}/" aria-label="Leer: {title}">
\t\t\t\t\t\t<img width="1024" height="576" src="/wp-content/uploads/2026/09/{featured_img}" class="attachment-large size-large wp-post-image" alt="{title}" itemprop="image" decoding="async" loading="lazy">
\t\t\t\t\t</a>
\t\t\t\t</div>
\t\t\t</div>
\t\t\t<span class="ast-blog-single-element ast-taxonomy-container cat-links default">
\t\t\t\t{cat_links_html}
\t\t\t</span>
\t\t\t<h2 class="entry-title ast-blog-single-element" itemprop="headline">
\t\t\t\t<a href="/{slug}/" rel="bookmark">{title}</a>
\t\t\t</h2>
\t\t\t<header class="entry-header ast-blog-single-element ast-blog-meta-container">
\t\t\t\t<div class="entry-meta">
\t\t\t\t\t<span class="posted-by vcard author" itemtype="https://schema.org/Person" itemscope="itemscope" itemprop="author">
\t\t\t\t\t\t<a title="Ver todas las entradas de Jessica Cabello" href="/author/jxaviercabellosgmail-com/" rel="author" class="url fn n" itemprop="url">
\t\t\t\t\t\t\t<span class="author-name" itemprop="name">Jessica Cabello</span>
\t\t\t\t\t\t</a>
\t\t\t\t\t</span> / <span class="posted-on"><span class="published" itemprop="datePublished">{spanish_date}</span></span>
\t\t\t\t</div>
\t\t\t</header>
\t\t\t<div class="ast-excerpt-container ast-blog-single-element">
\t\t\t\t<p>{excerpt}</p>
\t\t\t</div>
\t\t\t<div class="entry-content clear" itemprop="text"></div>
\t\t</div>
\t</div>
</article>\n'''

    # Insert card at top of <div class="ast-row">
    row_marker = '<div class="ast-row">'
    if row_marker in html:
        html = html.replace(row_marker, f'{row_marker}\n{card_html}', 1)

    # Recalculate total articles
    total_articles = len(re.findall(r'<article[^>]*id="post-\d+"', html))
    html = re.sub(r'Mostrando \d+ artículos', f'Mostrando {total_articles} artículos', html)
    html = re.sub(r'Todos <span class="pill-count">\d+</span>', f'Todos <span class="pill-count">{total_articles}</span>', html)

    # Update category pill count
    for cat in categories:
        cat_count = len(re.findall(rf'data-categories="[^"]*\b{cat}\b[^"]*"', html))
        pattern = rf'(data-filter="{cat}"[^>]*>[^<]*<span class="pill-count">)\d+(</span>)'
        html = re.sub(pattern, rf'\g<1>{cat_count}\g<2>', html)

    with open(blog_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Actualizado blog/index.html (Total: {total_articles})")

def update_category_archive(category, slug, num, title, excerpt, category_name, featured_img, spanish_date):
    cat_dir = os.path.join(REPO_DIR, "category", category)
    cat_file = os.path.join(cat_dir, "index.html")
    if not os.path.isfile(cat_file):
        return

    with open(cat_file, "r", encoding="utf-8") as f:
        html = f.read()

    # Remove no-posts placeholder if present
    html = re.sub(r'<p class="no-posts-yet"[\s\S]*?</p>', '', html)

    card_html = f'''<article class="post-{num} post type-post status-publish format-standard has-post-thumbnail hentry category-{category} ast-grid-common-col ast-full-width ast-article-post remove-featured-img-padding" id="post-{num}" itemtype="https://schema.org/CreativeWork" itemscope="itemscope">
\t<div class="ast-post-format- blog-layout-4 ast-article-inner">
\t\t<div class="post-content ast-grid-common-col">
\t\t\t<div class="ast-blog-featured-section post-thumb ast-blog-single-element">
\t\t\t\t<div class="post-thumb-img-content post-thumb">
\t\t\t\t\t<a href="/{slug}/" aria-label="Leer: {title}">
\t\t\t\t\t\t<img width="1024" height="576" src="/wp-content/uploads/2026/09/{featured_img}" class="attachment-large size-large wp-post-image" alt="{title}" itemprop="image" decoding="async" loading="lazy">
\t\t\t\t\t</a>
\t\t\t\t</div>
\t\t\t</div>
\t\t\t<span class="ast-blog-single-element ast-taxonomy-container cat-links default">
\t\t\t\t<a href="/category/{category}/" rel="category tag">{category_name}</a>
\t\t\t</span>
\t\t\t<h2 class="entry-title ast-blog-single-element" itemprop="headline">
\t\t\t\t<a href="/{slug}/" rel="bookmark">{title}</a>
\t\t\t</h2>
\t\t\t<header class="entry-header ast-blog-single-element ast-blog-meta-container">
\t\t\t\t<div class="entry-meta">
\t\t\t\t\t<span class="posted-by vcard author" itemtype="https://schema.org/Person" itemscope="itemscope" itemprop="author">
\t\t\t\t\t\t<a title="Ver todas las entradas de Jessica Cabello" href="/author/jxaviercabellosgmail-com/" rel="author" class="url fn n" itemprop="url">
\t\t\t\t\t\t\t<span class="author-name" itemprop="name">Jessica Cabello</span>
\t\t\t\t\t\t</a>
\t\t\t\t\t</span> / <span class="posted-on"><span class="published" itemprop="datePublished">{spanish_date}</span></span>
\t\t\t\t</div>
\t\t\t</header>
\t\t\t<div class="ast-excerpt-container ast-blog-single-element">
\t\t\t\t<p>{excerpt}</p>
\t\t\t</div>
\t\t\t<div class="entry-content clear" itemprop="text"></div>
\t\t</div>
\t</div>
</article>\n'''

    row_marker = '<div class="ast-row">'
    if row_marker in html:
        html = html.replace(row_marker, f'{row_marker}\n{card_html}', 1)

    with open(cat_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Actualizado category/{category}/index.html")

def update_sitemap(slug, short_date):
    sitemap_path = os.path.join(REPO_DIR, "sitemap.xml")
    if not os.path.isfile(sitemap_path):
        return

    with open(sitemap_path, "r", encoding="utf-8") as f:
        content = f.read()

    url_entry = f'''\t<url>
\t\t<loc>https://jessica.cabellosalirrosas.com/{slug}/</loc>
\t\t<lastmod>{short_date}</lastmod>
\t\t<changefreq>monthly</changefreq>
\t\t<priority>0.8</priority>
\t</url>\n'''

    if f"/{slug}/" not in content:
        content = content.replace("</urlset>", f"{url_entry}</urlset>")
        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Añadido /{slug}/ a sitemap.xml")

def update_search_index(slug, title, excerpt, categories):
    search_path = os.path.join(REPO_DIR, "search-index.json")
    if not os.path.isfile(search_path):
        return

    with open(search_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entry = {
        "title": title,
        "url": f"/{slug}/",
        "excerpt": excerpt,
        "categories": categories
    }

    # Add entry if not existing
    exists = any(item.get("url") == f"/{slug}/" for item in data)
    if not exists:
        data.append(entry)
        with open(search_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Añadido /{slug}/ a search-index.json")

def main():
    parser = argparse.ArgumentParser(description="Publicador de cola de artículos")
    parser.add_argument("--count", type=int, default=1, help="Número de artículos a publicar")
    parser.add_argument("--all", action="store_true", help="Publicar todos los artículos pendientes")
    args = parser.parse_args()

    if args.all:
        published_any = False
        while publish_one():
            published_any = True
        return 0
    else:
        for _ in range(args.count):
            if not publish_one():
                break
        return 0

if __name__ == "__main__":
    sys.exit(main())
