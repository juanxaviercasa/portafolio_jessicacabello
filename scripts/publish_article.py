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

    # 1. Update dates in article index.html
    article_html_path = os.path.join(src_path, "index.html")
    if os.path.isfile(article_html_path):
        with open(article_html_path, "r", encoding="utf-8") as f:
            article_html = f.read()

        # Replace placeholders
        article_html = article_html.replace("{{PUBLISH_DATE_SPANISH}}", spanish_date)
        article_html = article_html.replace("{{PUBLISH_DATE_ISO}}", iso_date)
        article_html = article_html.replace("{{PUBLISH_DATE_SHORT}}", short_date)
        
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
    cat_links_html = " ".join([f'<a href="/category/{c}/" rel="category tag">{category_name}</a>' for c in categories])

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
