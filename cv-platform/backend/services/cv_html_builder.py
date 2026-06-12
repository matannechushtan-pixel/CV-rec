"""Renders structured CV data into self-contained HTML documents.

build_cv_html() supports a library of 20 CV templates (10 visual designs,
each with a "_photo" and "_nophoto" variant). Every template is rendered as
a standalone HTML page with Tailwind CSS / Font Awesome / Google Fonts
loaded from CDNs, plus an embedded html2pdf.js download button so the page
can be served directly as a preview or saved as a standalone .html file.
"""

import html as _html
import os
import re

_INITIALS_RE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _esc(value) -> str:
    if value is None:
        return ""
    return _html.escape(str(value))


def _initials(full_name: str) -> str:
    parts = [p for p in _INITIALS_RE.split((full_name or "").strip()) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _bullets_html(bullets: list[str] | None, color: str = "#374151") -> str:
    bullets = bullets or []
    if not bullets:
        return ""
    items = "".join(f"<li>{_esc(b)}</li>" for b in bullets)
    return (
        f'<ul class="list-disc ml-4 text-[13.5px] space-y-0.5 mt-1" '
        f'style="color:{color}">{items}</ul>'
    )


# ---------------------------------------------------------------------------
# Photo / avatar blocks
# ---------------------------------------------------------------------------

def _photo_engine_html(photo_base64: str, theme: dict, size: str, radius: str) -> str:
    """An interactive zoom/pan photo container with a hidden-on-print zoom slider."""
    src = photo_base64
    if not src.startswith("data:"):
        src = f"data:image/jpeg;base64,{src}"
    return (
        f'<div id="photo-container" style="width:{size};height:{size};border-radius:{radius};'
        f'border:4px solid {theme["avatar_border"]};box-shadow:0 2px 8px rgba(0,0,0,.12);'
        'margin:0 auto;background:#e5e7eb;">'
        f'<img id="profile-photo-img" src="{src}" alt="Profile photo" />'
        "</div>"
        '<div class="no-print" style="margin-top:8px;text-align:center;">'
        '<input type="range" id="zoom-slider" min="100" max="300" step="1" value="120" '
        'style="width:120px;" />'
        '<div style="font-size:10px;color:#94a3b8;margin-top:2px;">Drag photo &middot; scroll to zoom</div>'
        "</div>"
    )


def _photo_circle(full_name: str, photo_base64: str | None, theme: dict, size: str = "9rem") -> str:
    """A circular photo with zoom/pan controls, or an initials avatar in the theme accent colour."""
    if photo_base64:
        return _photo_engine_html(photo_base64, theme, size=size, radius="50%")
    return (
        f'<div style="width:{size};height:{size};border:4px solid {theme["avatar_border"]};'
        f'background:{theme["primary"]};color:{theme["on_primary"]};" '
        'class="rounded-full shadow-md mx-auto flex items-center justify-center '
        'text-3xl font-bold">'
        f"{_esc(_initials(full_name))}"
        "</div>"
    )


def _photo_square(full_name: str, photo_base64: str | None, theme: dict, size: str = "9rem") -> str:
    """A rounded-square photo with zoom/pan controls, or an initials avatar in the theme accent colour."""
    if photo_base64:
        return _photo_engine_html(photo_base64, theme, size=size, radius="1rem")
    return (
        f'<div style="width:{size};height:{size};border:4px solid {theme["avatar_border"]};'
        f'background:{theme["on_primary"]};color:{theme["primary"]};" '
        'class="rounded-2xl shadow-md mx-auto flex items-center justify-center '
        'text-4xl font-extrabold">'
        f"{_esc(_initials(full_name))}"
        "</div>"
    )


# ---------------------------------------------------------------------------
# Theme-aware section builders
# ---------------------------------------------------------------------------

def _section_heading(text: str, theme: dict, size: str = "1.05rem") -> str:
    return (
        f'<h2 class="section-title" style="color:{theme["primary"]};font-size:{size};font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.05em;'
        f'border-bottom:2px solid {theme["divider"]};padding-bottom:0.25rem;'
        f'font-family:{theme["font_heading"]};">{_esc(text)}</h2>'
    )


def _sidebar_heading(text: str, theme: dict) -> str:
    return (
        f'<h3 class="sidebar-title" style="color:{theme["sidebar_accent"]};font-size:0.85rem;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.05em;'
        f'border-bottom:2px solid {theme["sidebar_divider"]};padding-bottom:0.25rem;'
        f'font-family:{theme["font_heading"]};">{_esc(text)}</h3>'
    )


def _contact_section(contact: dict | None, theme: dict, sidebar: bool = True, title: str | None = None) -> str:
    contact = contact or {}
    icons = {
        "location": "fa-location-dot",
        "phone": "fa-phone",
        "email": "fa-envelope",
    }
    rows = []
    icon_color = theme["sidebar_accent"] if sidebar else theme["primary"]
    text_color = theme["sidebar_text"] if sidebar else theme["body_text"]
    for key, icon in icons.items():
        value = contact.get(key)
        if not value:
            continue
        rows.append(
            f'<div class="flex items-center gap-2 text-sm" style="color:{text_color}">'
            f'<i class="fa-solid {icon} w-4 text-center" style="color:{icon_color}"></i>'
            f"<span>{_esc(value)}</span>"
            "</div>"
        )
    if not rows:
        return ""
    title = title or "Contact"
    heading = _sidebar_heading(title, theme) if sidebar else _section_heading(title, theme)
    return (
        '<div class="mb-6">'
        + heading
        + '<div class="space-y-1.5 mt-2">' + "".join(rows) + "</div>"
        "</div>"
    )


def _education_section(education: list[dict] | None, theme: dict, sidebar: bool = True, title: str | None = None) -> str:
    education = education or []
    if not education:
        return ""
    text_color = theme["sidebar_text"] if sidebar else theme["body_text"]
    muted = theme["sidebar_muted"] if sidebar else theme["muted_text"]
    items = []
    for edu in education:
        notes_html = ""
        if edu.get("notes"):
            notes_html = f'<p class="text-xs mt-1" style="color:{muted}">{_esc(edu["notes"])}</p>'
        items.append(
            '<div class="mb-3">'
            f'<p class="text-sm font-bold" style="color:{text_color}">{_esc(edu.get("institution"))}</p>'
            f'<p class="text-xs" style="color:{text_color}">{_esc(edu.get("degree"))}</p>'
            f'<p class="text-xs" style="color:{muted}">{_esc(edu.get("dates"))}</p>'
            f"{notes_html}"
            "</div>"
        )
    title = title or "Education"
    heading = _sidebar_heading(title, theme) if sidebar else _section_heading(title, theme)
    return (
        '<div class="mb-6">' + heading
        + '<div class="mt-2">' + "".join(items) + "</div>"
        "</div>"
    )


def _languages_section(languages: list[dict] | None, theme: dict, sidebar: bool = True, title: str | None = None) -> str:
    languages = languages or []
    if not languages:
        return ""
    text_color = theme["sidebar_text"] if sidebar else theme["body_text"]
    muted = theme["sidebar_muted"] if sidebar else theme["muted_text"]
    items = []
    for lang in languages:
        items.append(
            '<div class="flex justify-between text-sm mb-1">'
            f'<span class="font-bold" style="color:{text_color}">{_esc(lang.get("name"))}</span>'
            f'<span class="text-xs" style="color:{muted}">{_esc(lang.get("level"))}</span>'
            "</div>"
        )
    title = title or "Languages"
    heading = _sidebar_heading(title, theme) if sidebar else _section_heading(title, theme)
    return (
        '<div class="mb-6">' + heading
        + '<div class="mt-2">' + "".join(items) + "</div>"
        "</div>"
    )


def _hobbies_section(hobbies: str | None, theme: dict, sidebar: bool = True, title: str | None = None) -> str:
    if not hobbies:
        return ""
    text_color = theme["sidebar_text"] if sidebar else theme["body_text"]
    title = title or "Hobbies"
    heading = _sidebar_heading(title, theme) if sidebar else _section_heading(title, theme)
    return (
        '<div class="mb-6">' + heading
        + f'<p class="text-sm mt-2" style="color:{text_color}">{_esc(hobbies)}</p>'
        "</div>"
    )


def _skills_chips(skills: list[str] | None, theme: dict, sidebar: bool = True, title: str | None = None) -> str:
    skills = skills or []
    if not skills:
        return ""
    if sidebar:
        chip_bg = theme["sidebar_chip_bg"]
        chip_text = theme["sidebar_chip_text"]
        chip_border = f'border:1px solid {theme["sidebar_divider"]};'
    else:
        chip_bg = theme["chip_bg"]
        chip_text = theme["chip_text"]
        chip_border = ""
    chips = "".join(
        f'<span class="inline-block text-xs px-2 py-1 rounded-full mr-1 mb-1" '
        f'style="background:{chip_bg};color:{chip_text};{chip_border}">{_esc(s)}</span>'
        for s in skills
    )
    title = title or "Skills"
    heading = _sidebar_heading(title, theme) if sidebar else _section_heading(title, theme)
    return (
        '<div class="mb-6">' + heading
        + f'<div class="mt-2">{chips}</div>'
        "</div>"
    )


def _experience_section(experience: list[dict] | None, theme: dict, heading_size: str = "1.05rem", title: str | None = None) -> str:
    experience = experience or []
    if not experience:
        return ""
    entries = []
    for exp in experience:
        location_html = (
            f' <span style="color:{theme["muted_text"]}">· {_esc(exp["location"])}</span>'
            if exp.get("location")
            else ""
        )
        entries.append(
            '<div class="mb-4">'
            '<div class="flex items-start justify-between flex-wrap gap-1">'
            f'<p class="text-sm font-bold" style="color:{theme["heading_text"]}">'
            f'{_esc(exp.get("company"))}{location_html}'
            "</p>"
            f'<span class="text-xs px-2 py-0.5 rounded" '
            f'style="background:{theme["tag_bg"]};color:{theme["tag_text"]}">{_esc(exp.get("dates"))}</span>'
            "</div>"
            f'<p class="text-sm font-semibold uppercase tracking-wider mt-0.5" '
            f'style="color:{theme["primary"]}">{_esc(exp.get("role"))}</p>'
            f"{_bullets_html(exp.get('bullets'), theme['body_text'])}"
            "</div>"
        )
    return (
        '<div class="mb-6">'
        + _section_heading(title or "Professional Experience", theme, heading_size)
        + '<div class="mt-3">' + "".join(entries) + "</div>"
        "</div>"
    )


def _military_section(military: dict | None, theme: dict, title: str | None = None) -> str:
    if not military or not any(military.get(k) for k in ("unit", "role", "dates", "bullets")):
        return ""
    return (
        '<div class="mb-6">'
        + _section_heading(title or "Military Service", theme)
        + '<div class="mt-3">'
        '<div class="flex items-start justify-between flex-wrap gap-1">'
        f'<p class="text-sm font-bold" style="color:{theme["heading_text"]}">{_esc(military.get("unit"))}</p>'
        f'<span class="text-xs px-2 py-0.5 rounded" '
        f'style="background:{theme["tag_bg"]};color:{theme["tag_text"]}">{_esc(military.get("dates"))}</span>'
        "</div>"
        f'<p class="text-sm font-semibold uppercase tracking-wider mt-0.5" '
        f'style="color:{theme["primary"]}">{_esc(military.get("role"))}</p>'
        f"{_bullets_html(military.get('bullets'), theme['body_text'])}"
        "</div>"
        "</div>"
    )


def _volunteering_section(volunteering: list[dict] | None, theme: dict, title: str | None = None) -> str:
    volunteering = volunteering or []
    if not volunteering:
        return ""
    cards = []
    for v in volunteering:
        cards.append(
            '<div>'
            f'<p class="text-sm font-bold" style="color:{theme["heading_text"]}">{_esc(v.get("org"))} '
            f'<span class="text-xs font-normal" style="color:{theme["muted_text"]}">'
            f'({_esc(v.get("year"))})</span></p>'
            f'<p class="text-[13.5px]" style="color:{theme["body_text"]}">{_esc(v.get("description"))}</p>'
            "</div>"
        )
    return (
        '<div class="mb-6">'
        + _section_heading(title or "Volunteering", theme)
        + '<div class="grid grid-cols-2 gap-4 mt-3">' + "".join(cards) + "</div>"
        "</div>"
    )


def _skills_section_main(skills: list[str] | None, theme: dict, title: str | None = None) -> str:
    return _skills_chips(skills, theme, sidebar=False, title=title)


# ---------------------------------------------------------------------------
# Document wrapper
# ---------------------------------------------------------------------------

_DOWNLOAD_SCRIPT = """
function downloadCvPdf() {
  var opt = {
    margin: 0,
    filename: 'CV.pdf',
    image: { type: 'jpeg', quality: 1 },
    html2canvas: {
      scale: 4,
      useCORS: true,
      scrollY: 0,
      logging: false,
      letterRendering: true,
      onclone: function(clonedDoc) {
        var s = clonedDoc.getElementById('zoom-slider');
        if (s && s.parentNode) s.parentNode.style.display = 'none';
        clonedDoc.querySelectorAll('.no-print').forEach(function(el) {
          el.style.display = 'none';
        });
      }
    },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };
  var el = document.getElementById('cv-page');
  el.style.boxShadow = 'none';
  html2pdf().set(opt).from(el).save().then(function() {
    el.style.boxShadow = '';
  });
}
"""


_PHOTO_ENGINE_SCRIPT = """
(function() {
  var img = document.getElementById('profile-photo-img');
  var container = document.getElementById('photo-container');
  var slider = document.getElementById('zoom-slider');
  if (!img || !container) return;

  var state = { scale: 1.2, x: 0, y: 0, naturalW: 0, naturalH: 0 };
  var dragging = false, startX = 0, startY = 0, startPX = 0, startPY = 0;

  function updateTransform() {
    img.style.transformOrigin = 'center center';
    img.style.transform = 'translate(' + state.x + 'px, ' + state.y + 'px) scale(' + state.scale + ')';
  }

  function initImage(src, defaultScale, yRatio) {
    var temp = new Image();
    temp.onload = function() {
      var rect = container.getBoundingClientRect();
      var cw = rect.width || 144;
      var ch = rect.height || 144;
      var coverScale = Math.max(cw / temp.naturalWidth, ch / temp.naturalHeight);
      state.naturalW = temp.naturalWidth * coverScale;
      state.naturalH = temp.naturalHeight * coverScale;
      img.style.width = state.naturalW + 'px';
      img.style.height = state.naturalH + 'px';
      img.style.left = ((cw - state.naturalW) / 2) + 'px';
      img.style.top = ((ch - state.naturalH) / 2) + 'px';
      state.scale = (defaultScale || 120) / 100;
      state.x = 0;
      state.y = -(state.naturalH * (state.scale - 1)) * (yRatio || 0);
      updateTransform();
    };
    temp.src = src;
  }

  if (slider) {
    slider.addEventListener('input', function() {
      state.scale = parseInt(slider.value, 10) / 100;
      updateTransform();
    });
  }

  container.addEventListener('mousedown', function(e) {
    dragging = true;
    startX = e.clientX; startY = e.clientY;
    startPX = state.x; startPY = state.y;
    container.style.cursor = 'grabbing';
  });
  window.addEventListener('mousemove', function(e) {
    if (!dragging) return;
    state.x = startPX + (e.clientX - startX);
    state.y = startPY + (e.clientY - startY);
    updateTransform();
  });
  window.addEventListener('mouseup', function() {
    dragging = false;
    container.style.cursor = 'grab';
  });

  container.addEventListener('touchstart', function(e) {
    var t = e.touches[0];
    dragging = true;
    startX = t.clientX; startY = t.clientY;
    startPX = state.x; startPY = state.y;
  }, { passive: true });
  container.addEventListener('touchmove', function(e) {
    if (!dragging) return;
    var t = e.touches[0];
    state.x = startPX + (t.clientX - startX);
    state.y = startPY + (t.clientY - startY);
    updateTransform();
  }, { passive: true });
  window.addEventListener('touchend', function() { dragging = false; });

  container.addEventListener('wheel', function(e) {
    e.preventDefault();
    var newScale = state.scale - e.deltaY * 0.001;
    newScale = Math.max(1, Math.min(3, newScale));
    state.scale = newScale;
    if (slider) slider.value = Math.round(newScale * 100);
    updateTransform();
  }, { passive: false });

  window.addEventListener('load', function() {
    initImage(img.src, parseInt((slider && slider.value) || '120', 10), 0.15);
  });
})();
"""


def _apply_style_overrides(theme: dict, accent_color: str | None, font_family: str | None) -> dict:
    """Return a copy of theme with the accent colour and/or font family overridden.

    Any theme value equal to the original primary colour is swapped to the
    new accent colour, which preserves relationships (e.g. header bands or
    sidebars that reuse the primary colour as a background).
    """
    theme = dict(theme)
    if accent_color:
        old_primary = theme["primary"]
        for key, val in list(theme.items()):
            if isinstance(val, str) and val.lower() == old_primary.lower():
                theme[key] = accent_color
        theme["primary"] = accent_color
    if font_family:
        font_stack = f"'{font_family}', sans-serif"
        theme["font_heading"] = font_stack
        theme["font_body"] = font_stack
    return theme


_SYSTEM_FONTS = {"georgia", "times new roman", "arial"}


def _wrap_document(full_name: str, body_html: str, theme: dict, page_extra_style: str = "",
                    font_family: str | None = None) -> str:
    style = f"""
  body {{ font-family: {theme['font_body']}; }}
  #cv-page {{
    width: 210mm;
    min-height: 296mm;
    overflow: hidden;
    {page_extra_style}
  }}
  #profile-photo-img {{
    position: absolute;
    max-width: none;
    pointer-events: none;
    image-rendering: high-quality;
  }}
  #photo-container {{
    cursor: grab;
    position: relative;
    overflow: hidden;
  }}
  #photo-container:active {{ cursor: grabbing; }}
  @media print {{
    #download-btn {{ display: none; }}
  }}
"""
    font_link = ""
    if font_family and font_family.strip().lower() not in _SYSTEM_FONTS:
        font_link = (
            '<link href="https://fonts.googleapis.com/css2?family='
            f'{font_family.strip().replace(" ", "+")}:wght@300;400;500;600;700&display=swap" rel="stylesheet">'
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{_esc(full_name)} - CV</title>
<!-- Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
{font_link}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<style>{style}</style>
</head>
<body style="background:{theme['page_bg']}">
<div class="flex justify-center py-6">
  <button id="download-btn" onclick="downloadCvPdf()"
    class="no-print fixed top-4 right-4 z-50 text-sm font-semibold px-4 py-2 rounded-lg shadow-lg"
    style="background:{theme['primary']};color:{theme['on_primary']}">
    <i class="fa-solid fa-download mr-1"></i> Download PDF
  </button>
  {body_html}
</div>
<script>{_DOWNLOAD_SCRIPT}</script>
<script>{_PHOTO_ENGINE_SCRIPT}</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Layout renderers
# ---------------------------------------------------------------------------

def _layout_sidebar(cv_data: dict, photo_base64: str | None, has_photo: bool, theme: dict) -> str:
    """Two-column layout: sidebar (photo/contact/education/etc.) + main content."""
    full_name = cv_data.get("full_name") or ""
    summary = cv_data.get("summary") or ""
    titles = cv_data.get("section_titles") or {}

    if has_photo:
        avatar_html = _photo_circle(full_name, photo_base64, theme)
    else:
        # No photo: a simple initials circle in the theme's accent colour, with
        # extra top padding so the sidebar doesn't feel like it's missing something.
        avatar_html = (
            '<div class="pt-2">'
            + _photo_circle(full_name, None, theme)
            + "</div>"
        )

    sidebar = (
        avatar_html
        + '<div class="mt-6">'
        + _contact_section(cv_data.get("contact"), theme, sidebar=True, title=titles.get("contact"))
        + _education_section(cv_data.get("education"), theme, sidebar=True, title=titles.get("education"))
        + _languages_section(cv_data.get("languages"), theme, sidebar=True, title=titles.get("languages"))
        + _skills_chips(cv_data.get("skills"), theme, sidebar=True, title=titles.get("skills"))
        + _hobbies_section(cv_data.get("hobbies"), theme, sidebar=True, title=titles.get("hobbies"))
        + "</div>"
    )

    main = (
        '<div class="mb-6">'
        f'<h1 class="text-4xl font-extrabold" style="color:{theme["heading_text"]};'
        f'font-family:{theme["font_heading"]}">{_esc(full_name)}</h1>'
        f'<p class="text-[13.5px] mt-3" style="color:{theme["body_text"]}">{_esc(summary)}</p>'
        "</div>"
        + _experience_section(cv_data.get("experience"), theme, title=titles.get("experience"))
        + _military_section(cv_data.get("military"), theme, title=titles.get("military"))
        + _volunteering_section(cv_data.get("volunteering"), theme, title=titles.get("volunteering"))
    )

    sidebar_panel = (
        f'<div class="w-1/3 px-6 py-8" '
        f'style="background:{theme["sidebar_bg"]};border-{ "left" if theme["sidebar_pos"] == "right" else "right" }:'
        f'1px solid {theme["sidebar_divider"]}">{sidebar}</div>'
    )
    main_panel = f'<div class="w-2/3 px-8 py-8" style="background:{theme["main_bg"]}">{main}</div>'

    if theme["sidebar_pos"] == "right":
        cols = main_panel + sidebar_panel
    else:
        cols = sidebar_panel + main_panel

    return (
        f'<div id="cv-page" class="shadow-xl flex flex-row" style="background:{theme["main_bg"]}">'
        f"{cols}"
        "</div>"
    )


def _layout_split(cv_data: dict, photo_base64: str | None, has_photo: bool, theme: dict) -> str:
    """Large coloured panel (photo/identity) on one side, content on the other."""
    full_name = cv_data.get("full_name") or ""
    summary = cv_data.get("summary") or ""
    contact = cv_data.get("contact") or {}
    titles = cv_data.get("section_titles") or {}

    if has_photo:
        photo_html = _photo_square(full_name, photo_base64, theme, size="11rem")
    else:
        photo_html = (
            f'<div style="width:11rem;height:11rem;border:4px solid {theme["avatar_border"]};'
            f'background:{theme["on_primary"]};color:{theme["primary"]};" '
            'class="rounded-2xl shadow-md mx-auto flex items-center justify-center '
            'text-5xl font-extrabold">'
            f"{_esc(_initials(full_name))}"
            "</div>"
        )

    contact_rows = []
    icons = {"location": "fa-location-dot", "phone": "fa-phone", "email": "fa-envelope"}
    for key, icon in icons.items():
        value = contact.get(key)
        if not value:
            continue
        contact_rows.append(
            '<div class="flex items-center gap-2 text-sm" style="color:'
            f'{theme["on_primary"]}">'
            f'<i class="fa-solid {icon} w-4 text-center"></i><span>{_esc(value)}</span></div>'
        )

    panel_left = (
        f'<div class="w-2/5 px-8 py-10 flex flex-col items-center text-center" '
        f'style="background:{theme["primary"]};color:{theme["on_primary"]}">'
        + photo_html
        + f'<h1 class="text-2xl font-extrabold mt-5" style="font-family:{theme["font_heading"]}">'
        f"{_esc(full_name)}</h1>"
        + '<div class="space-y-1.5 mt-4 w-full text-left">' + "".join(contact_rows) + "</div>"
        + '<div class="mt-6 w-full text-left">'
        + _languages_section(cv_data.get("languages"), theme, sidebar=True, title=titles.get("languages"))
        + _skills_chips(cv_data.get("skills"), theme, sidebar=True, title=titles.get("skills"))
        + _hobbies_section(cv_data.get("hobbies"), theme, sidebar=True, title=titles.get("hobbies"))
        + "</div>"
        "</div>"
    )

    main = (
        '<div class="mb-6">'
        f'<h2 class="text-sm font-bold uppercase tracking-widest mb-2" style="color:{theme["primary"]}">Profile</h2>'
        f'<p class="text-[13.5px]" style="color:{theme["body_text"]}">{_esc(summary)}</p>'
        "</div>"
        + _experience_section(cv_data.get("experience"), theme, title=titles.get("experience"))
        + _education_section(cv_data.get("education"), theme, sidebar=False, title=titles.get("education"))
        + _military_section(cv_data.get("military"), theme, title=titles.get("military"))
        + _volunteering_section(cv_data.get("volunteering"), theme, title=titles.get("volunteering"))
    )
    panel_right = f'<div class="w-3/5 px-8 py-10" style="background:{theme["main_bg"]}">{main}</div>'

    return (
        f'<div id="cv-page" class="shadow-xl flex flex-row" style="background:{theme["main_bg"]}">'
        f"{panel_left}{panel_right}"
        "</div>"
    )


def _layout_single_column(cv_data: dict, photo_base64: str | None, has_photo: bool, theme: dict) -> str:
    """A single-column layout with a header band and stacked sections."""
    full_name = cv_data.get("full_name") or ""
    summary = cv_data.get("summary") or ""
    contact = cv_data.get("contact") or {}
    titles = cv_data.get("section_titles") or {}
    align = theme.get("header_align", "left")
    text_align_class = "text-center" if align == "center" else ""

    contact_parts = []
    icons = {"location": "fa-location-dot", "phone": "fa-phone", "email": "fa-envelope"}
    for key, icon in icons.items():
        value = contact.get(key)
        if not value:
            continue
        contact_parts.append(
            f'<span class="inline-flex items-center gap-1.5">'
            f'<i class="fa-solid {icon}" style="color:{theme["primary"]}"></i>{_esc(value)}</span>'
        )
    contact_html = (
        f'<div class="flex flex-wrap gap-x-5 gap-y-1 text-sm mt-2 '
        f'{"justify-center" if align == "center" else ""}" '
        f'style="color:{theme["muted_text"]}">' + "".join(contact_parts) + "</div>"
        if contact_parts
        else ""
    )

    header_text = (
        f'<h1 class="text-4xl font-extrabold" style="color:{theme["heading_text"]};'
        f'font-family:{theme["font_heading"]}">{_esc(full_name)}</h1>'
        + contact_html
    )

    if has_photo:
        avatar = _photo_circle(full_name, photo_base64, theme, size="6.5rem")
        header_inner = (
            f'<div class="flex items-center gap-6 {text_align_class}">'
            + (avatar if align != "center" else "")
            + f'<div class="flex-1">{header_text}</div>'
            + (avatar if align == "center" else "")
            + "</div>"
        )
    else:
        # Repurpose the photo space with a decorative monogram badge.
        badge = (
            f'<div class="rounded-full flex items-center justify-center font-extrabold text-2xl flex-shrink-0" '
            f'style="width:5rem;height:5rem;background:{theme["primary"]};color:{theme["on_primary"]}">'
            f"{_esc(_initials(full_name))}</div>"
        )
        header_inner = (
            f'<div class="flex items-center gap-6 {text_align_class} '
            f'{"justify-center" if align == "center" else ""}">'
            + badge
            + f'<div class="flex-1">{header_text}</div>'
            + "</div>"
        )

    header = (
        f'<div class="px-10 py-8" style="background:{theme["header_bg"]};'
        f'border-bottom: {theme["header_border"]}">{header_inner}</div>'
    )

    body = (
        '<div class="px-10 py-8">'
        + (
            f'<div class="mb-6"><p class="text-[13.5px]" style="color:{theme["body_text"]}">'
            f"{_esc(summary)}</p></div>"
            if summary
            else ""
        )
        + _experience_section(cv_data.get("experience"), theme, title=titles.get("experience"))
        + _education_section(cv_data.get("education"), theme, sidebar=False, title=titles.get("education"))
        + _military_section(cv_data.get("military"), theme, title=titles.get("military"))
        + '<div class="grid grid-cols-2 gap-8">'
        + _skills_section_main(cv_data.get("skills"), theme, title=titles.get("skills"))
        + (
            _languages_section(cv_data.get("languages"), theme, sidebar=False, title=titles.get("languages"))
            + _hobbies_section(cv_data.get("hobbies"), theme, sidebar=False, title=titles.get("hobbies"))
        )
        + "</div>"
        + _volunteering_section(cv_data.get("volunteering"), theme, title=titles.get("volunteering"))
        + "</div>"
    )

    return (
        f'<div id="cv-page" class="shadow-xl flex flex-col" style="background:{theme["main_bg"]}">'
        f"{header}{body}"
        "</div>"
    )


def _layout_timeline(cv_data: dict, photo_base64: str | None, has_photo: bool, theme: dict) -> str:
    """Single-column layout where Experience is rendered as a vertical timeline."""
    full_name = cv_data.get("full_name") or ""
    summary = cv_data.get("summary") or ""
    contact = cv_data.get("contact") or {}
    titles = cv_data.get("section_titles") or {}

    contact_parts = []
    icons = {"location": "fa-location-dot", "phone": "fa-phone", "email": "fa-envelope"}
    for key, icon in icons.items():
        value = contact.get(key)
        if not value:
            continue
        contact_parts.append(
            f'<span class="inline-flex items-center gap-1.5">'
            f'<i class="fa-solid {icon}" style="color:{theme["on_primary"]}"></i>{_esc(value)}</span>'
        )
    contact_html = (
        '<div class="flex flex-wrap gap-x-5 gap-y-1 text-sm mt-2" '
        f'style="color:{theme["on_primary"]};opacity:0.85">' + "".join(contact_parts) + "</div>"
        if contact_parts
        else ""
    )

    if has_photo:
        avatar = _photo_circle(full_name, photo_base64, theme, size="6.5rem")
    else:
        avatar = (
            f'<div class="rounded-full flex items-center justify-center font-extrabold text-2xl '
            f'flex-shrink-0 mx-auto" style="width:6.5rem;height:6.5rem;'
            f'background:{theme["on_primary"]};color:{theme["primary"]};'
            f'border:4px solid {theme["avatar_border"]}">'
            f"{_esc(_initials(full_name))}</div>"
        )

    header = (
        f'<div class="px-10 py-8 flex items-center gap-6" style="background:{theme["primary"]}">'
        + avatar
        + '<div>'
        + f'<h1 class="text-4xl font-extrabold" style="color:{theme["on_primary"]};'
        f'font-family:{theme["font_heading"]}">{_esc(full_name)}</h1>'
        + contact_html
        + "</div>"
        "</div>"
    )

    experience = cv_data.get("experience") or []
    timeline_items = []
    for exp in experience:
        location_html = (
            f' <span style="color:{theme["muted_text"]}">· {_esc(exp["location"])}</span>'
            if exp.get("location")
            else ""
        )
        timeline_items.append(
            '<div class="relative pl-8 pb-6">'
            f'<div class="absolute left-0 top-1.5 w-3 h-3 rounded-full" style="background:{theme["primary"]}"></div>'
            f'<div class="absolute left-[5px] top-4 bottom-0 w-px" style="background:{theme["divider"]}"></div>'
            '<div class="flex items-start justify-between flex-wrap gap-1">'
            f'<p class="text-sm font-bold" style="color:{theme["heading_text"]}">'
            f'{_esc(exp.get("company"))}{location_html}</p>'
            f'<span class="text-xs px-2 py-0.5 rounded" '
            f'style="background:{theme["tag_bg"]};color:{theme["tag_text"]}">{_esc(exp.get("dates"))}</span>'
            "</div>"
            f'<p class="text-sm font-semibold uppercase tracking-wider mt-0.5" '
            f'style="color:{theme["primary"]}">{_esc(exp.get("role"))}</p>'
            f"{_bullets_html(exp.get('bullets'), theme['body_text'])}"
            "</div>"
        )
    experience_html = (
        '<div class="mb-6">'
        + _section_heading(titles.get("experience") or "Professional Experience", theme)
        + '<div class="mt-4">' + "".join(timeline_items) + "</div>"
        "</div>"
        if timeline_items
        else ""
    )

    body = (
        '<div class="px-10 py-8">'
        + (
            f'<div class="mb-6"><p class="text-[13.5px]" style="color:{theme["body_text"]}">'
            f"{_esc(summary)}</p></div>"
            if summary
            else ""
        )
        + experience_html
        + _military_section(cv_data.get("military"), theme, title=titles.get("military"))
        + _education_section(cv_data.get("education"), theme, sidebar=False, title=titles.get("education"))
        + '<div class="grid grid-cols-2 gap-8">'
        + _skills_section_main(cv_data.get("skills"), theme, title=titles.get("skills"))
        + (
            _languages_section(cv_data.get("languages"), theme, sidebar=False, title=titles.get("languages"))
            + _hobbies_section(cv_data.get("hobbies"), theme, sidebar=False, title=titles.get("hobbies"))
        )
        + "</div>"
        + _volunteering_section(cv_data.get("volunteering"), theme, title=titles.get("volunteering"))
        + "</div>"
    )

    return (
        f'<div id="cv-page" class="shadow-xl flex flex-col" style="background:{theme["main_bg"]}">'
        f"{header}{body}"
        "</div>"
    )


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

THEMES: dict[str, dict] = {
    "classic_blue": {
        "font_heading": "'Inter', sans-serif",
        "font_body": "'Inter', sans-serif",
        "primary": "#1e3a8a",
        "on_primary": "#ffffff",
        "page_bg": "#e2e8f0",
        "main_bg": "#ffffff",
        "sidebar_bg": "#f8fafc",
        "sidebar_pos": "left",
        "sidebar_text": "#374151",
        "sidebar_muted": "#6b7280",
        "sidebar_accent": "#1e3a8a",
        "sidebar_divider": "#e5e7eb",
        "sidebar_chip_bg": "#ffffff",
        "sidebar_chip_text": "#374151",
        "heading_text": "#111827",
        "body_text": "#374151",
        "muted_text": "#6b7280",
        "divider": "#e5e7eb",
        "tag_bg": "#f3f4f6",
        "tag_text": "#374151",
        "chip_bg": "#eff6ff",
        "chip_text": "#1e3a8a",
        "avatar_border": "#ffffff",
        "header_bg": "#ffffff",
        "header_border": "none",
        "header_align": "left",
    },
    "executive_dark": {
        "font_heading": "'Inter', sans-serif",
        "font_body": "'Inter', sans-serif",
        "primary": "#d4af37",
        "on_primary": "#1f2937",
        "page_bg": "#e2e8f0",
        "main_bg": "#ffffff",
        "sidebar_bg": "#1f2937",
        "sidebar_pos": "left",
        "sidebar_text": "#e5e7eb",
        "sidebar_muted": "#9ca3af",
        "sidebar_accent": "#d4af37",
        "sidebar_divider": "#374151",
        "sidebar_chip_bg": "#374151",
        "sidebar_chip_text": "#e5e7eb",
        "heading_text": "#111827",
        "body_text": "#374151",
        "muted_text": "#6b7280",
        "divider": "#e5e7eb",
        "tag_bg": "#fef9e7",
        "tag_text": "#92722a",
        "chip_bg": "#fef9e7",
        "chip_text": "#92722a",
        "avatar_border": "#d4af37",
        "header_bg": "#ffffff",
        "header_border": "none",
        "header_align": "left",
    },
    "modern_split": {
        "font_heading": "'Inter', sans-serif",
        "font_body": "'Inter', sans-serif",
        "primary": "#0d9488",
        "on_primary": "#ffffff",
        "page_bg": "#e2e8f0",
        "main_bg": "#ffffff",
        "sidebar_bg": "#0d9488",
        "sidebar_pos": "left",
        "sidebar_text": "#ecfdf5",
        "sidebar_muted": "#a7f3d0",
        "sidebar_accent": "#ecfdf5",
        "sidebar_divider": "rgba(255,255,255,0.25)",
        "sidebar_chip_bg": "rgba(255,255,255,0.15)",
        "sidebar_chip_text": "#ffffff",
        "heading_text": "#0f172a",
        "body_text": "#374151",
        "muted_text": "#6b7280",
        "divider": "#e5e7eb",
        "tag_bg": "#f0fdfa",
        "tag_text": "#0d9488",
        "chip_bg": "#f0fdfa",
        "chip_text": "#0d9488",
        "avatar_border": "#ffffff",
        "header_bg": "#ffffff",
        "header_border": "none",
        "header_align": "left",
    },
    "creative_sidebar": {
        "font_heading": "'Inter', sans-serif",
        "font_body": "'Inter', sans-serif",
        "primary": "#7c3aed",
        "on_primary": "#ffffff",
        "page_bg": "#e2e8f0",
        "main_bg": "#ffffff",
        "sidebar_bg": "#7c3aed",
        "sidebar_pos": "left",
        "sidebar_text": "#f5f3ff",
        "sidebar_muted": "#ddd6fe",
        "sidebar_accent": "#fde047",
        "sidebar_divider": "rgba(255,255,255,0.25)",
        "sidebar_chip_bg": "rgba(255,255,255,0.15)",
        "sidebar_chip_text": "#ffffff",
        "heading_text": "#1e1b4b",
        "body_text": "#374151",
        "muted_text": "#6b7280",
        "divider": "#e5e7eb",
        "tag_bg": "#f5f3ff",
        "tag_text": "#7c3aed",
        "chip_bg": "#f5f3ff",
        "chip_text": "#7c3aed",
        "avatar_border": "#fde047",
        "header_bg": "#ffffff",
        "header_border": "none",
        "header_align": "left",
    },
    "elegant_serif": {
        "font_heading": "'Playfair Display', serif",
        "font_body": "Georgia, 'Times New Roman', serif",
        "primary": "#78350f",
        "on_primary": "#ffffff",
        "page_bg": "#f1ede4",
        "main_bg": "#fffdf8",
        "sidebar_bg": "#fffdf8",
        "sidebar_pos": "left",
        "sidebar_text": "#44403c",
        "sidebar_muted": "#a8a29e",
        "sidebar_accent": "#78350f",
        "sidebar_divider": "#e7e0d4",
        "sidebar_chip_bg": "#f5f0e6",
        "sidebar_chip_text": "#78350f",
        "heading_text": "#292524",
        "body_text": "#44403c",
        "muted_text": "#a8a29e",
        "divider": "#e7e0d4",
        "tag_bg": "#f5f0e6",
        "tag_text": "#78350f",
        "chip_bg": "#f5f0e6",
        "chip_text": "#78350f",
        "avatar_border": "#78350f",
        "header_bg": "#fffdf8",
        "header_border": f"3px double #78350f",
        "header_align": "center",
    },
    "minimalist": {
        "font_heading": "'Inter', sans-serif",
        "font_body": "'Inter', sans-serif",
        "primary": "#111827",
        "on_primary": "#ffffff",
        "page_bg": "#f5f5f4",
        "main_bg": "#ffffff",
        "sidebar_bg": "#ffffff",
        "sidebar_pos": "left",
        "sidebar_text": "#374151",
        "sidebar_muted": "#9ca3af",
        "sidebar_accent": "#111827",
        "sidebar_divider": "#e5e7eb",
        "sidebar_chip_bg": "#f9fafb",
        "sidebar_chip_text": "#374151",
        "heading_text": "#111827",
        "body_text": "#4b5563",
        "muted_text": "#9ca3af",
        "divider": "#e5e7eb",
        "tag_bg": "#f9fafb",
        "tag_text": "#374151",
        "chip_bg": "#f9fafb",
        "chip_text": "#111827",
        "avatar_border": "#e5e7eb",
        "header_bg": "#ffffff",
        "header_border": "1px solid #e5e7eb",
        "header_align": "left",
    },
    "tech_dark": {
        "font_heading": "'Roboto Mono', monospace",
        "font_body": "'Inter', sans-serif",
        "primary": "#22d3ee",
        "on_primary": "#0f172a",
        "page_bg": "#0b1120",
        "main_bg": "#0f172a",
        "sidebar_bg": "#0b1324",
        "sidebar_pos": "left",
        "sidebar_text": "#cbd5e1",
        "sidebar_muted": "#64748b",
        "sidebar_accent": "#22d3ee",
        "sidebar_divider": "#1e293b",
        "sidebar_chip_bg": "#1e293b",
        "sidebar_chip_text": "#67e8f9",
        "heading_text": "#f1f5f9",
        "body_text": "#cbd5e1",
        "muted_text": "#64748b",
        "divider": "#1e293b",
        "tag_bg": "#1e293b",
        "tag_text": "#67e8f9",
        "chip_bg": "#1e293b",
        "chip_text": "#67e8f9",
        "avatar_border": "#22d3ee",
        "header_bg": "#0f172a",
        "header_border": "none",
        "header_align": "left",
    },
    "corporate_navy": {
        "font_heading": "'Inter', sans-serif",
        "font_body": "'Inter', sans-serif",
        "primary": "#1e293b",
        "on_primary": "#ffffff",
        "page_bg": "#e2e8f0",
        "main_bg": "#ffffff",
        "sidebar_bg": "#f1f5f9",
        "sidebar_pos": "right",
        "sidebar_text": "#334155",
        "sidebar_muted": "#64748b",
        "sidebar_accent": "#1e293b",
        "sidebar_divider": "#e2e8f0",
        "sidebar_chip_bg": "#ffffff",
        "sidebar_chip_text": "#334155",
        "heading_text": "#0f172a",
        "body_text": "#334155",
        "muted_text": "#64748b",
        "divider": "#e2e8f0",
        "tag_bg": "#f1f5f9",
        "tag_text": "#1e293b",
        "chip_bg": "#f1f5f9",
        "chip_text": "#1e293b",
        "avatar_border": "#ffffff",
        "header_bg": "#1e293b",
        "header_border": "none",
        "header_align": "left",
    },
    "bold_header": {
        "font_heading": "'Inter', sans-serif",
        "font_body": "'Inter', sans-serif",
        "primary": "#dc2626",
        "on_primary": "#ffffff",
        "page_bg": "#e2e8f0",
        "main_bg": "#ffffff",
        "sidebar_bg": "#fef2f2",
        "sidebar_pos": "left",
        "sidebar_text": "#374151",
        "sidebar_muted": "#9ca3af",
        "sidebar_accent": "#dc2626",
        "sidebar_divider": "#fecaca",
        "sidebar_chip_bg": "#ffffff",
        "sidebar_chip_text": "#374151",
        "heading_text": "#111827",
        "body_text": "#374151",
        "muted_text": "#6b7280",
        "divider": "#fecaca",
        "tag_bg": "#fef2f2",
        "tag_text": "#dc2626",
        "chip_bg": "#fef2f2",
        "chip_text": "#dc2626",
        "avatar_border": "#ffffff",
        "header_bg": "#dc2626",
        "header_border": "none",
        "header_align": "left",
    },
    "timeline_clean": {
        "font_heading": "'Inter', sans-serif",
        "font_body": "'Inter', sans-serif",
        "primary": "#059669",
        "on_primary": "#ffffff",
        "page_bg": "#e2e8f0",
        "main_bg": "#ffffff",
        "sidebar_bg": "#ecfdf5",
        "sidebar_pos": "left",
        "sidebar_text": "#374151",
        "sidebar_muted": "#9ca3af",
        "sidebar_accent": "#059669",
        "sidebar_divider": "#d1fae5",
        "sidebar_chip_bg": "#ffffff",
        "sidebar_chip_text": "#374151",
        "heading_text": "#111827",
        "body_text": "#374151",
        "muted_text": "#6b7280",
        "divider": "#d1fae5",
        "tag_bg": "#ecfdf5",
        "tag_text": "#059669",
        "chip_bg": "#ecfdf5",
        "chip_text": "#059669",
        "avatar_border": "#ffffff",
        "header_bg": "#059669",
        "header_border": "none",
        "header_align": "left",
    },
}


# ---------------------------------------------------------------------------
# Header colours used in the bold_header header band override.
# (header_bg for bold_header is the primary colour, so heading text in that
#  band must be on_primary, not heading_text — handled via a small override
#  inside _layout_single_column by always letting header_bg drive contrast.)
# ---------------------------------------------------------------------------


def _apply_header_band_contrast(theme: dict) -> dict:
    """Return a copy of theme with heading/body colours swapped for a coloured header band."""
    if theme["header_bg"] == theme["primary"]:
        patched = dict(theme)
        patched["heading_text"] = theme["on_primary"]
        patched["muted_text"] = theme["on_primary"]
        return patched
    return theme


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

def _sidebar_layout_with_band(cv_data, photo_base64, has_photo, theme):
    return _layout_sidebar(cv_data, photo_base64, has_photo, theme)


def _single_column_with_band(cv_data, photo_base64, has_photo, theme):
    band_theme = _apply_header_band_contrast(theme)
    full_name = cv_data.get("full_name") or ""
    summary = cv_data.get("summary") or ""
    contact = cv_data.get("contact") or {}
    titles = cv_data.get("section_titles") or {}
    contact_parts = []
    icons = {"location": "fa-location-dot", "phone": "fa-phone", "email": "fa-envelope"}
    for key, icon in icons.items():
        value = contact.get(key)
        if not value:
            continue
        contact_parts.append(
            f'<span class="inline-flex items-center gap-1.5">'
            f'<i class="fa-solid {icon}"></i>{_esc(value)}</span>'
        )
    contact_html = (
        '<div class="flex flex-wrap gap-x-5 gap-y-1 text-sm mt-2" '
        f'style="color:{band_theme["on_primary"]};opacity:0.9">' + "".join(contact_parts) + "</div>"
        if contact_parts
        else ""
    )

    if has_photo:
        avatar = _photo_circle(full_name, photo_base64, band_theme, size="6.5rem")
    else:
        avatar = (
            f'<div class="rounded-full flex items-center justify-center font-extrabold text-2xl '
            f'flex-shrink-0" style="width:6.5rem;height:6.5rem;'
            f'background:{band_theme["on_primary"]};color:{band_theme["primary"]};'
            f'border:4px solid {band_theme["avatar_border"]}">'
            f"{_esc(_initials(full_name))}</div>"
        )

    header = (
        f'<div class="px-10 py-8 flex items-center gap-6" style="background:{theme["header_bg"]}">'
        + avatar
        + '<div>'
        + f'<h1 class="text-4xl font-extrabold" style="color:{band_theme["on_primary"]};'
        f'font-family:{theme["font_heading"]}">{_esc(full_name)}</h1>'
        + contact_html
        + "</div>"
        "</div>"
    )

    body = (
        '<div class="px-10 py-8">'
        + (
            f'<div class="mb-6"><p class="text-[13.5px]" style="color:{theme["body_text"]}">'
            f"{_esc(summary)}</p></div>"
            if summary
            else ""
        )
        + _experience_section(cv_data.get("experience"), theme, title=titles.get("experience"))
        + _education_section(cv_data.get("education"), theme, sidebar=False, title=titles.get("education"))
        + _military_section(cv_data.get("military"), theme, title=titles.get("military"))
        + '<div class="grid grid-cols-2 gap-8">'
        + _skills_section_main(cv_data.get("skills"), theme, title=titles.get("skills"))
        + (
            _languages_section(cv_data.get("languages"), theme, sidebar=False, title=titles.get("languages"))
            + _hobbies_section(cv_data.get("hobbies"), theme, sidebar=False, title=titles.get("hobbies"))
        )
        + "</div>"
        + _volunteering_section(cv_data.get("volunteering"), theme, title=titles.get("volunteering"))
        + "</div>"
    )

    return (
        f'<div id="cv-page" class="shadow-xl flex flex-col" style="background:{theme["main_bg"]}">'
        f"{header}{body}"
        "</div>"
    )


TEMPLATES: dict[str, dict] = {
    "classic_blue_photo": {
        "name": "Classic Blue (with photo)",
        "has_photo": True,
        "design": "classic_blue",
        "description": "A timeless two-column resume with a navy sidebar, profile photo, and clean Inter typography.",
        "preview_colors": ["#1e3a8a", "#f8fafc", "#ffffff"],
        "layout": _layout_sidebar,
        "theme": "classic_blue",
    },
    "classic_blue_nophoto": {
        "name": "Classic Blue (no photo)",
        "has_photo": False,
        "design": "classic_blue",
        "description": "The Classic Blue layout with the photo slot replaced by a bold name card in the sidebar.",
        "preview_colors": ["#1e3a8a", "#f8fafc", "#ffffff"],
        "layout": _layout_sidebar,
        "theme": "classic_blue",
    },
    "executive_dark_photo": {
        "name": "Executive Dark (with photo)",
        "has_photo": True,
        "design": "executive_dark",
        "description": "A premium dark charcoal sidebar with gold accents, ideal for senior leadership profiles.",
        "preview_colors": ["#1f2937", "#d4af37", "#ffffff"],
        "layout": _layout_sidebar,
        "theme": "executive_dark",
    },
    "executive_dark_nophoto": {
        "name": "Executive Dark (no photo)",
        "has_photo": False,
        "design": "executive_dark",
        "description": "Executive Dark with a gold monogram card in place of the photo for a polished, photo-free look.",
        "preview_colors": ["#1f2937", "#d4af37", "#ffffff"],
        "layout": _layout_sidebar,
        "theme": "executive_dark",
    },
    "modern_split_photo": {
        "name": "Modern Split (with photo)",
        "has_photo": True,
        "design": "modern_split",
        "description": "A bold teal identity panel with a square photo alongside a spacious content column.",
        "preview_colors": ["#0d9488", "#ffffff", "#f0fdfa"],
        "layout": _layout_split,
        "theme": "modern_split",
    },
    "modern_split_nophoto": {
        "name": "Modern Split (no photo)",
        "has_photo": False,
        "design": "modern_split",
        "description": "Modern Split with a large initials badge filling the identity panel instead of a photo.",
        "preview_colors": ["#0d9488", "#ffffff", "#f0fdfa"],
        "layout": _layout_split,
        "theme": "modern_split",
    },
    "creative_sidebar_photo": {
        "name": "Creative Sidebar (with photo)",
        "has_photo": True,
        "design": "creative_sidebar",
        "description": "A vibrant violet sidebar with a circular photo and yellow accent highlights for creative roles.",
        "preview_colors": ["#7c3aed", "#fde047", "#ffffff"],
        "layout": _layout_sidebar,
        "theme": "creative_sidebar",
    },
    "creative_sidebar_nophoto": {
        "name": "Creative Sidebar (no photo)",
        "has_photo": False,
        "design": "creative_sidebar",
        "description": "Creative Sidebar with a colourful initials card replacing the photo space.",
        "preview_colors": ["#7c3aed", "#fde047", "#ffffff"],
        "layout": _layout_sidebar,
        "theme": "creative_sidebar",
    },
    "elegant_serif_photo": {
        "name": "Elegant Serif (with photo)",
        "has_photo": True,
        "design": "elegant_serif",
        "description": "A refined cream layout with serif headings, centered header, and a circular portrait.",
        "preview_colors": ["#78350f", "#fffdf8", "#f5f0e6"],
        "layout": _layout_single_column,
        "theme": "elegant_serif",
    },
    "elegant_serif_nophoto": {
        "name": "Elegant Serif (no photo)",
        "has_photo": False,
        "design": "elegant_serif",
        "description": "Elegant Serif with an engraved-style monogram badge in place of the portrait.",
        "preview_colors": ["#78350f", "#fffdf8", "#f5f0e6"],
        "layout": _layout_single_column,
        "theme": "elegant_serif",
    },
    "minimalist_photo": {
        "name": "Minimalist (with photo)",
        "has_photo": True,
        "design": "minimalist",
        "description": "A clean, airy single-column layout with a small circular photo and generous whitespace.",
        "preview_colors": ["#111827", "#ffffff", "#f9fafb"],
        "layout": _layout_single_column,
        "theme": "minimalist",
    },
    "minimalist_nophoto": {
        "name": "Minimalist (no photo)",
        "has_photo": False,
        "design": "minimalist",
        "description": "Minimalist with a subtle monogram badge instead of a photo, keeping focus on content.",
        "preview_colors": ["#111827", "#ffffff", "#f9fafb"],
        "layout": _layout_single_column,
        "theme": "minimalist",
    },
    "tech_dark_photo": {
        "name": "Tech Dark (with photo)",
        "has_photo": True,
        "design": "tech_dark",
        "description": "A dark, code-inspired layout with cyan accents, monospace headings, and a circular photo.",
        "preview_colors": ["#0f172a", "#22d3ee", "#1e293b"],
        "layout": _layout_sidebar,
        "theme": "tech_dark",
    },
    "tech_dark_nophoto": {
        "name": "Tech Dark (no photo)",
        "has_photo": False,
        "design": "tech_dark",
        "description": "Tech Dark with a cyan-on-dark initials terminal card replacing the photo.",
        "preview_colors": ["#0f172a", "#22d3ee", "#1e293b"],
        "layout": _layout_sidebar,
        "theme": "tech_dark",
    },
    "corporate_navy_photo": {
        "name": "Corporate Navy (with photo)",
        "has_photo": True,
        "design": "corporate_navy",
        "description": "A professional layout with a navy header band and a light right-hand sidebar with a photo.",
        "preview_colors": ["#1e293b", "#f1f5f9", "#ffffff"],
        "layout": _layout_sidebar,
        "theme": "corporate_navy",
    },
    "corporate_navy_nophoto": {
        "name": "Corporate Navy (no photo)",
        "has_photo": False,
        "design": "corporate_navy",
        "description": "Corporate Navy with a navy initials card replacing the photo in the right-hand sidebar.",
        "preview_colors": ["#1e293b", "#f1f5f9", "#ffffff"],
        "layout": _layout_sidebar,
        "theme": "corporate_navy",
    },
    "bold_header_photo": {
        "name": "Bold Header (with photo)",
        "has_photo": True,
        "design": "bold_header",
        "description": "A striking full-width red header band with a circular photo and bold name treatment.",
        "preview_colors": ["#dc2626", "#ffffff", "#fef2f2"],
        "layout": _single_column_with_band,
        "theme": "bold_header",
    },
    "bold_header_nophoto": {
        "name": "Bold Header (no photo)",
        "has_photo": False,
        "design": "bold_header",
        "description": "Bold Header with a high-contrast initials badge filling the header band instead of a photo.",
        "preview_colors": ["#dc2626", "#ffffff", "#fef2f2"],
        "layout": _single_column_with_band,
        "theme": "bold_header",
    },
    "timeline_clean_photo": {
        "name": "Timeline Clean (with photo)",
        "has_photo": True,
        "design": "timeline_clean",
        "description": "A fresh green header band and a vertical timeline that highlights career progression.",
        "preview_colors": ["#059669", "#ecfdf5", "#ffffff"],
        "layout": _layout_timeline,
        "theme": "timeline_clean",
    },
    "timeline_clean_nophoto": {
        "name": "Timeline Clean (no photo)",
        "has_photo": False,
        "design": "timeline_clean",
        "description": "Timeline Clean with an initials badge in the header band and the same vertical timeline.",
        "preview_colors": ["#059669", "#ecfdf5", "#ffffff"],
        "layout": _layout_timeline,
        "theme": "timeline_clean",
    },
}


def _apply_rtl(html: str) -> str:
    """Inject RTL direction and a Hebrew-friendly font into an HTML CV string."""
    if '<html lang="en">' in html:
        html = html.replace('<html lang="en">', '<html dir="rtl" lang="he">', 1)
    elif '<html ' in html:
        html = html.replace('<html ', '<html dir="rtl" lang="he" ', 1)
    else:
        html = html.replace('<html>', '<html dir="rtl" lang="he">', 1)

    rtl_css = """
    /* RTL overrides */
    body, .resume-page { direction: rtl; text-align: right; }
    .content-ltr { direction: rtl; text-align: right; }
    ul { padding-right: 1.2rem; padding-left: 0; }
    .list-disc { padding-right: 1.5rem; padding-left: 0; }
    /* Flip sidebar to right side for two-column layouts */
    .resume-page { flex-direction: row-reverse; }
    /* Flip border sides */
    [class*="border-r"] { border-right: none !important;
                          border-left: 1px solid; }
    [class*="border-l"] { border-left: none !important;
                          border-right: 3px solid; }
    /* Contact icons spacing */
    .fa, .fas, .far { margin-left: 0.5rem; margin-right: 0; }
    """
    html = html.replace('</style>', rtl_css + '\n</style>', 1)

    rubik_link = (
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Rubik:wght@300;400;500;600;700&display=swap" '
        'rel="stylesheet">'
    )
    rubik_override = (
        "<style>"
        "body, * { font-family: 'Rubik', sans-serif !important; }"
        "</style>"
    )
    html = html.replace('</head>', rubik_link + rubik_override + '</head>', 1)
    return html


def _validate_no_duplicate_headings(html: str, template_id: str):
    headings = re.findall(
        r'class="[^"]*(?:section-title|sidebar-title)[^"]*"[^>]*>\s*([^<]+)',
        html, re.IGNORECASE
    )
    normalized = [h.strip().upper() for h in headings]
    seen = set()
    for h in normalized:
        if h in seen:
            raise ValueError(
                f"Template '{template_id}': duplicate heading '{h}'"
            )
        seen.add(h)


def build_cv_html(cv_data: dict, template_id: str = "classic_blue_photo", photo_base64: str | None = None,
                  accent_color: str | None = None, font_family: str | None = None,
                  language: str = "English") -> str:
    """Render structured CV data into a self-contained HTML CV document.

    `template_id` selects one of the 20 entries in TEMPLATES (10 designs x
    photo/nophoto). Falls back to "classic_blue_photo" if unknown.
    `accent_color` and `font_family`, if provided, override the template's
    default accent colour and typography.
    `language`, if Hebrew, renders the document right-to-left with a
    Hebrew-friendly font.
    """
    cv_data = cv_data or {}
    tpl = TEMPLATES.get(template_id) or TEMPLATES["classic_blue_photo"]
    theme = THEMES[tpl["theme"]]
    theme = _apply_style_overrides(theme, accent_color, font_family)
    layout_fn = tpl["layout"]
    has_photo = tpl["has_photo"]
    body_html = layout_fn(cv_data, photo_base64 if has_photo else None, has_photo, theme)
    html = _wrap_document(cv_data.get("full_name") or "", body_html, theme, font_family=font_family)

    if language and language.lower() in ("hebrew", "עברית", "he"):
        html = _apply_rtl(html)

    if os.getenv("CV_VALIDATE_HTML"):
        _validate_no_duplicate_headings(html, template_id)

    return html


def get_templates() -> list[dict]:
    """Return metadata for all available CV templates (for the picker UI)."""
    return [
        {
            "id": key,
            "name": tpl["name"],
            "has_photo": tpl["has_photo"],
            "design": tpl["design"],
            "description": tpl["description"],
            "preview_colors": tpl["preview_colors"],
        }
        for key, tpl in TEMPLATES.items()
    ]
