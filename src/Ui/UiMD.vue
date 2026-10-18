<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
    /** Raw markdown source (may include inline <svg>, <img>, <audio>, <video>). */
    source?: string;
    /** Extra classes on the root element. */
    class?: string;
}>(), {
    source: '',
});

/* ──────────────────────────────────────────────────────────────────── *
 * Escaping
 * ──────────────────────────────────────────────────────────────────── */
function escapeHtml(s: string) {
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function escapeRegex(s: string) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/* ──────────────────────────────────────────────────────────────────── *
 * URL safety — blocks data:image/svg+xml (which can carry scripts).
 * ──────────────────────────────────────────────────────────────────── */
function safeUrl(url: string): string {
    const t = (url ?? '').trim();
    if (!t) return '';
    if (/^(https?:)?\/\//i.test(t)) return t;

    // Raster image data URIs only — NOT svg+xml.
    if (/^data:image\/(png|jpe?g|gif|webp|avif|bmp|ico);/i.test(t)) return t;
    if (/^data:audio\/(mpeg|mp3|ogg|wav|webm|aac|flac|opus);/i.test(t)) return t;
    if (/^data:video\/(mp4|webm|ogg|quicktime);/i.test(t)) return t;

    if (/^\//.test(t)) return t;    // site-relative
    if (/^#/.test(t)) return t;     // anchor
    if (/^mailto:/i.test(t)) return t;
    return '';
}

/* ──────────────────────────────────────────────────────────────────── *
 * SVG sanitizer (DOMParser based)
 * ──────────────────────────────────────────────────────────────────── */
const ALLOWED_SVG_TAGS = new Set([
    'svg', 'g', 'path', 'circle', 'ellipse', 'rect', 'line', 'polyline',
    'polygon', 'text', 'tspan', 'textpath', 'defs', 'lineargradient',
    'radialgradient', 'stop', 'use', 'symbol', 'title', 'desc', 'clippath',
    'mask', 'marker', 'pattern', 'filter', 'fegaussianblur', 'feblend',
    'fecolormatrix', 'feoffset', 'femerge', 'femergenode', 'fecomposite',
    'fedropshadow', 'animate', 'animatetransform', 'animatemotion', 'set',
    'image', 'a',
]);

const ALLOWED_SVG_ATTRS = new Set([
    // geometry
    'x', 'y', 'x1', 'x2', 'y1', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
    'width', 'height', 'd', 'points', 'dx', 'dy', 'rotate', 'transform',
    'viewbox', 'preserveaspectratio', 'pathlength',
    // presentation
    'fill', 'fill-opacity', 'fill-rule', 'stroke', 'stroke-width',
    'stroke-linecap', 'stroke-linejoin', 'stroke-dasharray',
    'stroke-dashoffset', 'stroke-miterlimit', 'stroke-opacity', 'opacity',
    'color', 'display', 'visibility', 'clip-path', 'clip-rule', 'mask',
    'marker-start', 'marker-mid', 'marker-end', 'filter', 'vector-effect',
    'shape-rendering', 'paint-order',
    // gradient stops
    'offset', 'stop-color', 'stop-opacity', 'gradientunits',
    'gradienttransform', 'spreadmethod',
    // text
    'font-family', 'font-size', 'font-weight', 'font-style',
    'text-anchor', 'dominant-baseline', 'letter-spacing', 'word-spacing',
    'text-decoration',
    // identity / a11y
    'id', 'class', 'lang', 'tabindex', 'role', 'aria-hidden', 'aria-label',
    'aria-labelledby', 'focusable', 'xmlns', 'xmlns:xlink', 'version',
    // links / images
    'href', 'xlink:href', 'target', 'rel',
    // animation timing
    'attributename', 'attributetype', 'from', 'to', 'by', 'values', 'dur',
    'repeatcount', 'repeatdur', 'begin', 'end', 'calcmode', 'keytimes',
    'keysplines', 'type',
]);

const URL_ATTRS = new Set(['href', 'xlink:href', 'src']);

/** Sanitize an SVG DOM node recursively. */
function sanitizeSvgNode(node: Node): Node | null {
    if (node.nodeType === Node.TEXT_NODE) {
        return document.createTextNode(node.textContent ?? '');
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return null;

    const el = node as Element;
    const tag = el.tagName.toLowerCase();
    if (!ALLOWED_SVG_TAGS.has(tag)) return null;

    const safe = document.createElementNS('http://www.w3.org/2000/svg', tag);

    for (const attr of Array.from(el.attributes)) {
        const rawName = attr.name;
        const lower = rawName.toLowerCase();
        const local = lower.includes(':') ? lower.split(':')[1] : lower;

        if (lower.startsWith('on')) continue;
        if (!ALLOWED_SVG_ATTRS.has(lower) && !ALLOWED_SVG_ATTRS.has(local)) continue;

        let value = attr.value;
        if (local === 'style') continue; // no inline CSS in SVG
        if (URL_ATTRS.has(local)) {
            const safeHref = safeUrl(value);
            if (!safeHref) continue;
            value = safeHref;
        }
        try {
            safe.setAttribute(rawName, value);
        } catch {
            // Invalid attribute name for the SVG namespace — skip.
        }
    }

    if (tag === 'svg') {
        safe.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    }

    for (const child of Array.from(el.childNodes)) {
        const clean = sanitizeSvgNode(child);
        if (clean) safe.appendChild(clean);
    }

    return safe;
}

function sanitizeSvg(raw: string): string {
    const doc = new DOMParser().parseFromString(raw, 'image/svg+xml');
    if (doc.querySelector('parsererror')) return '';
    const root = doc.documentElement;
    if (!root || root.tagName.toLowerCase() !== 'svg') return '';
    const clean = sanitizeSvgNode(root);
    if (!clean) return '';
    return new XMLSerializer().serializeToString(clean);
}

/* ──────────────────────────────────────────────────────────────────── *
 * <img> sanitizer
 * ──────────────────────────────────────────────────────────────────── */
function sanitizeImg(raw: string): string {
    const doc = new DOMParser().parseFromString(raw, 'text/html');
    const el = doc.body.firstElementChild as HTMLImageElement | null;
    if (!el || el.tagName.toLowerCase() !== 'img') return '';

    const src = safeUrl(el.getAttribute('src') ?? '');
    if (!src) return '';

    const alt = escapeHtml(el.getAttribute('alt') ?? '');
    const title = el.getAttribute('title')
        ? ` title="${escapeHtml(el.getAttribute('title')!)}"`
        : '';

    const num = (v: string | null) => (v && /^\d+$/.test(v) ? v : '');
    const w = num(el.getAttribute('width'));
    const h = num(el.getAttribute('height'));

    const loading = ['lazy', 'eager'].includes(el.getAttribute('loading') ?? '')
        ? el.getAttribute('loading')!
        : 'lazy';
    const decoding = ['sync', 'async', 'auto'].includes(el.getAttribute('decoding') ?? '')
        ? el.getAttribute('decoding')!
        : 'async';

    const cls = 'my-2 max-w-full rounded-md border border-border';

    return (
        `<img src="${escapeHtml(src)}" alt="${alt}"${title}` +
        `${w ? ` width="${w}"` : ''}${h ? ` height="${h}"` : ''}` +
        ` loading="${loading}" decoding="${decoding}" class="${cls}" />`
    );
}

/* ──────────────────────────────────────────────────────────────────── *
 * <audio> / <video> sanitizer — "media"
 * ──────────────────────────────────────────────────────────────────── */
function sanitizeMedia(raw: string, tag: 'audio' | 'video'): string {
    const doc = new DOMParser().parseFromString(raw, 'text/html');
    const el = doc.body.firstElementChild as HTMLElement | null;
    if (!el || el.tagName.toLowerCase() !== tag) return '';

    const src = safeUrl(el.getAttribute('src') ?? '');
    const poster = tag === 'video' ? safeUrl(el.getAttribute('poster') ?? '') : '';

    // Accept nested <source> children too (in case the author used them).
    const innerSources: string[] = [];
    for (const child of Array.from(el.children)) {
        if (child.tagName.toLowerCase() !== 'source') continue;
        const childSrc = safeUrl(child.getAttribute('src') ?? '');
        if (!childSrc) continue;
        const type = child.getAttribute('type');
        const typeAttr = type && /^[\w-]+\/[\w.+-]+$/.test(type)
            ? ` type="${escapeHtml(type)}"`
            : '';
        innerSources.push(`<source src="${escapeHtml(childSrc)}"${typeAttr} />`);
    }

    if (!src && innerSources.length === 0) return '';

    // Boolean attributes.
    const hasAttr = (n: string) => el.hasAttribute(n);
    const boolAttrs: string[] = [];
    if (hasAttr('controls')) boolAttrs.push('controls');
    if (hasAttr('autoplay')) boolAttrs.push('autoplay');
    if (hasAttr('loop')) boolAttrs.push('loop');
    if (hasAttr('muted')) boolAttrs.push('muted');
    if (hasAttr('playsinline')) boolAttrs.push('playsinline');

    const preload = ['none', 'metadata', 'auto'].includes(el.getAttribute('preload') ?? '')
        ? el.getAttribute('preload')!
        : 'metadata';

    const num = (v: string | null) => (v && /^\d+$/.test(v) ? v : '');
    const w = num(el.getAttribute('width'));
    const h = num(el.getAttribute('height'));

    const srcAttr = src ? ` src="${escapeHtml(src)}"` : '';
    const posterAttr = poster ? ` poster="${escapeHtml(poster)}"` : '';

    return (
        `<${tag}${srcAttr}${posterAttr} preload="${preload}" ` +
        `${boolAttrs.join(' ')}${w ? ` width="${w}"` : ''}${h ? ` height="${h}"` : ''}` +
        ` class="my-3 w-full rounded-md border border-border">` +
        innerSources.join('') +
        `</${tag}>`
    );
}

/* ──────────────────────────────────────────────────────────────────── *
 * Raw HTML extraction — runs BEFORE markdown.
 * Order: svg → img → video → audio (longest/most specific first).
 * ──────────────────────────────────────────────────────────────────── */
interface RawBlock { token: string; html: string; }

const TOKEN_OPEN = '%%RAW';
const TOKEN_CLOSE = '%%';

function extractRawTags(src: string): { cleaned: string; raws: RawBlock[] } {
    const raws: RawBlock[] = [];
    let out = src;

    const push = (html: string) => {
        const token = `${TOKEN_OPEN}${raws.length}${TOKEN_CLOSE}`;
        raws.push({ token, html });
        return token;
    };

    // 1. <svg>…</svg>
    out = out.replace(/<svg\b[^>]*>[\s\S]*?<\/svg>/gi, (m) => {
        const clean = sanitizeSvg(m);
        return clean ? push(clean) : escapeHtml(m);
    });

    // 2. Self-closing <svg … />
    out = out.replace(/<svg\b[^>]*\/>/gi, (m) => {
        const clean = sanitizeSvg(m);
        return clean ? push(clean) : escapeHtml(m);
    });

    // 3. <video>…</video>
    out = out.replace(/<video\b[^>]*>[\s\S]*?<\/video>/gi, (m) => {
        const clean = sanitizeMedia(m, 'video');
        return clean ? push(clean) : escapeHtml(m);
    });

    // 4. Self-closing / void <video … />
    out = out.replace(/<video\b[^>]*\/>/gi, (m) => {
        const clean = sanitizeMedia(m, 'video');
        return clean ? push(clean) : escapeHtml(m);
    });

    // 5. <audio>…</audio>
    out = out.replace(/<audio\b[^>]*>[\s\S]*?<\/audio>/gi, (m) => {
        const clean = sanitizeMedia(m, 'audio');
        return clean ? push(clean) : escapeHtml(m);
    });

    // 6. Self-closing / void <audio … />
    out = out.replace(/<audio\b[^>]*\/>/gi, (m) => {
        const clean = sanitizeMedia(m, 'audio');
        return clean ? push(clean) : escapeHtml(m);
    });

    // 7. <img …> (void)
    out = out.replace(/<img\b[^>]*\/?>/gi, (m) => {
        const clean = sanitizeImg(m);
        return clean ? push(clean) : escapeHtml(m);
    });

    return { cleaned: out, raws };
}

/** Put sanitized raw blocks back after markdown rendering. */
function reinsertRawTags(rendered: string, raws: RawBlock[]): string {
    let out = rendered;

    for (const { token, html } of raws) {
        const tokenRe = escapeRegex(token);

        // If the whole paragraph is just the token, replace it entirely.
        const wrapped = new RegExp(`<p[^>]*>\\s*${tokenRe}\\s*<\\/p>`, 'g');
        out = out.replace(wrapped, html);

        // Token inline inside a <p>…</p> → split the paragraph around it.
        const inline = new RegExp(tokenRe, 'g');
        out = out.replace(inline, (_match, offset: number, full: string) => {
            const before = full.slice(0, offset);
            const openIdx = before.lastIndexOf('<p');
            const closeIdx = before.lastIndexOf('</p>');
            if (openIdx > closeIdx) {
                return `</p>${html}<p class="my-2 leading-relaxed">`;
            }
            return html;
        });
    }

    return out;
}

/* ──────────────────────────────────────────────────────────────────── *
 * Inline markdown (unchanged)
 * ──────────────────────────────────────────────────────────────────── */
function renderInline(escaped: string): string {
    let out = escaped;

    out = out.replace(
        /`([^`]+)`/g,
        '<code class="rounded bg-code-bg border border-code-border px-1 py-0.5 text-[0.85em] font-mono">$1</code>',
    );

    out = out.replace(
        /!\[([^\]]*)\]\((\S+?)(?:\s+&quot;([^&]*)&quot;)?\)/g,
        (_m, alt, url, title) => {
            const href = safeUrl(url);
            if (!href) return alt;
            const t = title ? ` title="${title}"` : '';
            return `<img src="${href}" alt="${alt}"${t} class="my-2 max-w-full rounded-md border border-border" loading="lazy" />`;
        },
    );

    out = out.replace(
        /\[([^\]]+)\]\((\S+?)(?:\s+&quot;([^&]*)&quot;)?\)/g,
        (_m, text, url, title) => {
            const href = safeUrl(url);
            if (!href) return text;
            const t = title ? ` title="${title}"` : '';
            const external = /^https?:/i.test(href);
            const rel = external ? ' target="_blank" rel="noopener noreferrer"' : '';
            return `<a href="${href}"${t}${rel} class="text-accent hover:text-accent-hover underline underline-offset-2">${text}</a>`;
        },
    );

    out = out.replace(
        /\*\*([^*]+)\*\*/g,
        '<strong class="font-semibold text-text-h">$1</strong>',
    );

    out = out.replace(
        /(^|[^*])\*([^*\n]+)\*(?!\*)/g,
        '$1<em class="italic">$2</em>',
    );

    out = out.replace(
        /~~([^~]+)~~/g,
        '<del class="line-through text-text-muted">$1</del>',
    );

    return out;
}

/* ──────────────────────────────────────────────────────────────────── *
 * Block renderer
 * ──────────────────────────────────────────────────────────────────── */
const VIDEO_EXT = /\.(mp4|webm|ogg|ogv|mov|m4v)(\?.*)?$/i;
const AUDIO_EXT = /\.(mp3|wav|ogg|oga|flac|aac|m4a|opus|weba)(\?.*)?$/i;
const RAW_TOKEN_LINE = new RegExp(`^\\s*${escapeRegex(TOKEN_OPEN)}\\d+${escapeRegex(TOKEN_CLOSE)}\\s*$`);

function renderBlocks(src: string): string {
    const lines = src.replace(/\r\n?/g, '\n').split('\n');
    const html: string[] = [];
    let i = 0;
    const push = (s: string) => html.push(s);

    while (i < lines.length) {
        const line = lines[i];

        // Raw-token line — pass through untouched.
        if (RAW_TOKEN_LINE.test(line)) {
            push(line.trim());
            i++;
            continue;
        }

        // Fenced code
        const fence = line.match(/^```\s*([\w-]*)\s*$/);
        if (fence) {
            const lang = fence[1] || '';
            const buf: string[] = [];
            i++;
            while (i < lines.length && !/^```\s*$/.test(lines[i])) {
                buf.push(lines[i]);
                i++;
            }
            i++;
            const code = escapeHtml(buf.join('\n'));
            const langAttr = lang ? ` data-lang="${escapeHtml(lang)}"` : '';
            push(
                `<pre${langAttr} class="my-3 overflow-x-auto rounded-md border border-code-border bg-code-bg p-3 text-sm"><code class="font-mono whitespace-pre">${code}</code></pre>`,
            );
            continue;
        }

        if (/^\s*$/.test(line)) { i++; continue; }

        if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) {
            push('<hr class="my-4 border-border" />');
            i++;
            continue;
        }

        const h = line.match(/^(#{1,6})\s+(.*)$/);
        if (h) {
            const level = h[1].length;
            const sizes: Record<number, string> = {
                1: 'text-2xl font-bold mt-5 mb-2',
                2: 'text-xl font-bold mt-4 mb-2',
                3: 'text-lg font-semibold mt-4 mb-1.5',
                4: 'text-base font-semibold mt-3 mb-1',
                5: 'text-sm font-semibold mt-3 mb-1',
                6: 'text-xs font-semibold uppercase tracking-wider mt-3 mb-1 text-text-muted',
            };
            push(
                `<h${level} class="${sizes[level]} text-text-h">${renderInline(escapeHtml(h[2]))}</h${level}>`,
            );
            i++;
            continue;
        }

        if (/^\s*>\s?/.test(line)) {
            const buf: string[] = [];
            while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
                buf.push(lines[i].replace(/^\s*>\s?/, ''));
                i++;
            }
            push(
                `<blockquote class="my-3 border-l-4 border-border-strong pl-3 text-text-muted italic">${renderInline(escapeHtml(buf.join('\n'))).replace(/\n/g, '<br />')}</blockquote>`,
            );
            continue;
        }

        if (/^\s*[-*+]\s+/.test(line)) {
            const items: string[] = [];
            while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
                items.push(lines[i].replace(/^\s*[-*+]\s+/, ''));
                i++;
            }
            const inner = items
                .map((it) => `<li class="ml-5 list-disc">${renderInline(escapeHtml(it))}</li>`)
                .join('');
            push(`<ul class="my-2 flex flex-col gap-1">${inner}</ul>`);
            continue;
        }

        if (/^\s*\d+\.\s+/.test(line)) {
            const items: string[] = [];
            while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
                items.push(lines[i].replace(/^\s*\d+\.\s+/, ''));
                i++;
            }
            const inner = items
                .map((it) => `<li class="ml-5 list-decimal">${renderInline(escapeHtml(it))}</li>`)
                .join('');
            push(`<ol class="my-2 flex flex-col gap-1">${inner}</ol>`);
            continue;
        }

        // Standalone media URL line → <video> or <audio>
        const vid = line.trim().match(/^(\S+)$/);
        if (vid && VIDEO_EXT.test(vid[1])) {
            const href = safeUrl(vid[1]);
            if (href) {
                push(
                    `<video controls preload="metadata" class="my-3 w-full rounded-md border border-border"><source src="${href}" /></video>`,
                );
                i++;
                continue;
            }
        }
        if (vid && AUDIO_EXT.test(vid[1])) {
            const href = safeUrl(vid[1]);
            if (href) {
                push(
                    `<audio controls preload="metadata" class="my-3 w-full rounded-md border border-border"><source src="${href}" /></audio>`,
                );
                i++;
                continue;
            }
        }

        // Paragraph
        const buf: string[] = [];
        while (
            i < lines.length &&
            !/^\s*$/.test(lines[i]) &&
            !/^```/.test(lines[i]) &&
            !/^#{1,6}\s/.test(lines[i]) &&
            !/^\s*>\s?/.test(lines[i]) &&
            !/^\s*[-*+]\s+/.test(lines[i]) &&
            !/^\s*\d+\.\s+/.test(lines[i]) &&
            !/^\s*([-*_])(\s*\1){2,}\s*$/.test(lines[i]) &&
            !RAW_TOKEN_LINE.test(lines[i])
        ) {
            buf.push(lines[i]);
            i++;
        }
        const text = buf.join('\n');
        const withBreaks = renderInline(escapeHtml(text)).replace(/\n/g, '<br />');
        push(`<p class="my-2 leading-relaxed">${withBreaks}</p>`);
    }

    return html.join('\n');
}

/* ──────────────────────────────────────────────────────────────────── *
 * Public pipeline
 * ──────────────────────────────────────────────────────────────────── */
const html = computed(() => {
    const src = props.source ?? '';
    const { cleaned, raws } = extractRawTags(src);
    const rendered = renderBlocks(cleaned);
    return reinsertRawTags(rendered, raws);
});
</script>

<template>
    <div
        class="text-sm text-text [&_svg]:inline-block [&_svg]:align-middle [&_img]:inline-block [&_img]:align-middle [&_audio]:my-3 [&_video]:my-3"
        :class="props.class"
        v-html="html"
    />
</template>