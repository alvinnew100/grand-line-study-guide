"""Layout and modern-CSS web problems: flexbox, grid, positioning, stacking, responsive grids, custom properties, motion."""


def page(title, css, body):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>'
            + title + "</title>\n<style>\n" + css.strip("\n") + "\n</style>\n</head>\n<body>\n" + body.strip("\n") + "\n</body>\n</html>\n")


def C(name, test):
    return {"name": name, "test": test}


RULES = "[...document.styleSheets].flatMap(s => [...s.cssRules])"
RECT = "document.querySelector('%s').getBoundingClientRect()"

CENTER_HTML = """
<div class="stage">
  <div class="box">Centred</div>
</div>
"""

NAV_HTML = """
<header class="site-header">
  <a class="brand" href="/">Kelp &amp; Co</a>
  <nav aria-label="Main">
    <ul class="menu">
      <li><a href="/" aria-current="page">Home</a></li>
      <li><a href="/shop">Shop</a></li>
      <li><a href="/recipes">Recipes</a></li>
      <li><a href="/contact">Contact</a></li>
    </ul>
  </nav>
</header>
<main><h1>Seaweed, sustainably harvested</h1></main>
"""

BADGE_HTML = """
<span class="icon" role="img" aria-label="Inbox, 3 unread">
  <span class="badge">3</span>
</span>
"""

STACK_HTML = """
<div class="stack">
  <div class="card a">A</div>
  <div class="card b">B</div>
  <div class="card c">C</div>
</div>
<div class="toast" role="status">Saved</div>
"""

LONG = "".join("<p>Paragraph %d. The tide table for the week is printed on the harbour office door and updated every Monday.</p>\n" % i for i in range(1, 71))

STICKY_HTML = """
<header class="bar">Harbour notices</header>
<main>
""" + LONG + """</main>
"""

FOOTER_HTML = """
<header>Ferry timetable</header>
<main><p>No sailings today.</p></main>
<footer>Harbour office, open 9 to 5</footer>
"""

TWOCOL_HTML = """
<div class="layout">
  <aside class="sidebar">Filters</aside>
  <main class="content">Results</main>
</div>
"""

GRAIL_HTML = """
<div class="page">
  <header>Header</header>
  <nav aria-label="Sections">Nav</nav>
  <main>Main content</main>
  <aside>Aside</aside>
  <footer>Footer</footer>
</div>
"""

CARDS_HTML = """
<div class="cards">
  <article class="card">Kelp</article>
  <article class="card">Dulse</article>
  <article class="card">Nori</article>
  <article class="card">Wakame</article>
  <article class="card">Sea lettuce</article>
  <article class="card">Carrageen</article>
</div>
"""

THEME_HTML = """
<main class="panel">
  <h1>Tide alerts</h1>
  <p>Get a message one hour before high water.</p>
  <button class="btn" type="button">Subscribe</button>
</main>
"""

HOVER_HTML = """
<article class="card">
  <h2>Coastal path</h2>
  <p>Seven miles from the harbour to the old light.</p>
</article>
"""

ANIM_HTML = """
<div class="dot" role="img" aria-label="Live"></div>
<div class="spinner" role="status" aria-label="Loading"></div>
"""

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="web-center-flex", title="Centre a box with flexbox", difficulty="Easy", pattern="Flexbox", kind="web",
    description=r"""
Centre `.box` both horizontally and vertically inside `.stage` using **flexbox**.

Requirements:

- `.stage` is a flex container at least as tall as the viewport (`min-height: 100vh`).
- `.stage` centres its child on the main axis (`justify-content: center`) and on the cross axis (`align-items: center`).
- The centre of `.box` coincides with the centre of `.stage`.
- `.box` stays in normal flow: do not use `position: absolute` or `fixed`.
""",
    starter=page("Centre", """
body { margin: 0; font-family: system-ui, sans-serif; }
.stage {
  background: #e8eaf6;
  /* your code */
}
.box { background: white; padding: 1.5rem 2.5rem; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / .2); }
""", CENTER_HTML),
    solution=page("Centre", """
body { margin: 0; font-family: system-ui, sans-serif; }
.stage {
  background: #e8eaf6;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
.box { background: white; padding: 1.5rem 2.5rem; border-radius: 12px; box-shadow: 0 4px 16px rgb(0 0 0 / .2); }
""", CENTER_HTML),
    checks=[
        C(".stage is a flex container", "getComputedStyle(document.querySelector('.stage')).display === 'flex'"),
        C("justify-content and align-items are center", "(c => c.justifyContent === 'center' && c.alignItems === 'center')(getComputedStyle(document.querySelector('.stage')))"),
        C(".stage is at least as tall as the viewport", (RECT % ".stage") + ".height >= window.innerHeight - 1"),
        C("The box is centred horizontally", "((s, b) => Math.abs((s.left + s.right) / 2 - (b.left + b.right) / 2) < 1)(" + (RECT % ".stage") + ", " + (RECT % ".box") + ")"),
        C("The box is centred vertically", "((s, b) => Math.abs((s.top + s.bottom) / 2 - (b.top + b.bottom) / 2) < 1 && s.height > b.height + 100)(" + (RECT % ".stage") + ", " + (RECT % ".box") + ")"),
        C("The box is not absolutely positioned", "getComputedStyle(document.querySelector('.box')).position === 'static'"),
    ],
    guide=dict(
        prereqs="Flex containers, the main and cross axes, `justify-content` and `align-items`. See *Flexbox in depth*.",
        intuition="A flex container can distribute its spare space. `justify-content: center` splits the leftover width equally on both sides of the item; `align-items: center` does the same with the leftover height. Vertical centring needs spare height to work with, which is why the container must be made tall.",
        hints=[
            "Start with `display: flex` on `.stage` (the parent), not on `.box`.",
            "In a row, `justify-content` is horizontal and `align-items` is vertical. Set both to `center`.",
            "The stage is only as tall as the box until you add `min-height: 100vh`.",
        ],
        approach="1. `.stage { display: flex; }`\n2. `justify-content: center;` centres along the row.\n3. `align-items: center;` centres across it.\n4. `min-height: 100vh;` gives the container the full viewport height to centre within.",
        pitfalls="- Putting the flex properties on the child.\n- Forgetting the height: horizontal centring works but vertical appears to do nothing.\n- `height: 100vh` instead of `min-height`: content taller than the window would overflow.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-navbar", title="A horizontal navigation bar", difficulty="Medium", pattern="Flexbox", kind="web",
    description=r"""
Turn the bulleted list of links into a navigation bar. The HTML is complete; write the CSS.

Requirements:

- `.site-header` is a flex container that vertically centres its children (`align-items: center`).
- The brand sits at the left; the menu is pushed to the **right edge** of the header (within 40px of the viewport's right edge).
- `.menu` is a flex container with **no bullets** (`list-style-type: none`), **no left padding** and a **16px** gap.
- All four menu items sit on one line.
- Each menu link is `display: block`, has at least **8px** of top and bottom padding, and is **not underlined**.
- The current page's link (`[aria-current="page"]`) has a different `background-color` from the other links.
""",
    starter=page("Kelp & Co", """
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
.site-header { background: #004d40; padding: 8px 24px; }
.brand { color: white; font-weight: 700; font-size: 1.2rem; text-decoration: none; }
.menu a { color: white; }
main { padding: 24px; }

/* your code */
""", NAV_HTML),
    solution=page("Kelp & Co", """
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
.site-header { background: #004d40; padding: 8px 24px; }
.brand { color: white; font-weight: 700; font-size: 1.2rem; text-decoration: none; }
.menu a { color: white; }
main { padding: 24px; }

.site-header {
  display: flex;
  align-items: center;
}
.site-header nav {
  margin-left: auto;
}
.menu {
  display: flex;
  gap: 16px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.menu a {
  display: block;
  padding: 10px 14px;
  border-radius: 6px;
  text-decoration: none;
}
.menu a:hover,
.menu a:focus-visible {
  background-color: rgb(0, 121, 107);
}
.menu a[aria-current="page"] {
  background-color: rgb(0, 137, 123);
}
""", NAV_HTML),
    checks=[
        C(".site-header is flex with align-items: center", "(c => c.display === 'flex' && c.alignItems === 'center')(getComputedStyle(document.querySelector('.site-header')))"),
        C("The brand is at the left and the menu reaches the right edge", "((b, m) => b.left < 60 && document.documentElement.clientWidth - m.right <= 40 && m.left > b.right + 100)(" + (RECT % ".brand") + ", " + (RECT % ".menu") + ")"),
        C(".menu is flex with no bullets and no left padding", "(c => c.display === 'flex' && c.listStyleType === 'none' && c.paddingLeft === '0px')(getComputedStyle(document.querySelector('.menu')))"),
        C("The gap between menu items is 16px", "(r => Math.round(r[1].left - r[0].right) === 16)([...document.querySelectorAll('.menu > li')].map(e => e.getBoundingClientRect()))"),
        C("All four items are on one line", "(r => r.length === 4 && r.every(x => Math.abs(x.top - r[0].top) < 1) && r[0].left < r[3].left)([...document.querySelectorAll('.menu > li')].map(e => e.getBoundingClientRect()))"),
        C("Links are blocks with at least 8px vertical padding and no underline", "[...document.querySelectorAll('.menu a')].every(a => (c => c.display === 'block' && parseFloat(c.paddingTop) >= 8 && parseFloat(c.paddingBottom) >= 8 && c.textDecorationLine === 'none')(getComputedStyle(a)))"),
        C("The current page link has its own background colour", "getComputedStyle(document.querySelector('.menu a[aria-current=\"page\"]')).backgroundColor !== getComputedStyle(document.querySelector('.menu a:not([aria-current])')).backgroundColor"),
    ],
    guide=dict(
        prereqs="Removing list defaults, flex containers, `gap`, auto margins. See *Styling lists, tables and forms* and *Flexbox in depth*.",
        intuition="A navigation bar is a list of links, so the HTML stays a `ul`. CSS strips the list's bullets and indent and lays the items in a row. Two flex containers are involved: the header (brand on one side, navigation on the other) and the menu itself. In a flex row, a `margin-left: auto` soaks up all the free space, shoving the item to the far end.",
        hints=[
            "Make `.site-header` a flex row with `align-items: center`, then give the `nav` (the header's second child) `margin-left: auto`.",
            "Reset the list: `list-style: none; margin: 0; padding: 0;`, then `display: flex; gap: 16px;`.",
            "Links are inline by default, so vertical padding does not enlarge them. Add `display: block` with padding, remove the underline, and target the current page with the attribute selector `[aria-current=\"page\"]`.",
        ],
        approach="1. Header: `display: flex; align-items: center;`.\n2. `nav { margin-left: auto; }` pushes the menu right.\n3. Menu: remove bullets, margin and padding; `display: flex; gap: 16px;`.\n4. Links: `display: block; padding: 10px 14px; text-decoration: none;`.\n5. States: a hover/focus background and a distinct background for `[aria-current=\"page\"]`.",
        pitfalls="- `list-style: none` without `padding: 0` leaves a 40px indent.\n- `justify-content: space-between` on the header also works, but the auto margin keeps working if more items are added on the left.\n- Applying `margin-left: auto` to `.menu`: it is not a child of the header, so it has no effect there.\n- Styling only `:hover` and forgetting keyboard focus.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-positioned-badge", title="A notification badge", difficulty="Easy", pattern="Positioning", kind="web",
    description=r"""
Pin the red badge to the **top-right corner** of the icon so that it overhangs the corner.

Requirements:

- `.icon` is the reference frame: `position: relative` (it must not move or change size; it stays 48 by 48 pixels).
- `.badge` is `position: absolute`, and its containing block is `.icon`.
- The badge overhangs by **6px**: its right edge is 6px to the right of the icon's right edge, and its top edge is 6px above the icon's top edge.
- The badge is round (`border-radius` of at least 10px, or 50%).
""",
    starter=page("Badge", """
body { font-family: system-ui, sans-serif; padding: 40px; }
.icon {
  display: inline-block;
  width: 48px; height: 48px; border-radius: 12px;
  background: #37474f;
  /* your code */
}
.badge {
  min-width: 20px; height: 20px; padding: 0 5px; box-sizing: border-box;
  background: #d32f2f; color: white;
  font: 700 12px/20px system-ui, sans-serif; text-align: center;
  /* your code */
}
""", BADGE_HTML),
    solution=page("Badge", """
body { font-family: system-ui, sans-serif; padding: 40px; }
.icon {
  display: inline-block;
  width: 48px; height: 48px; border-radius: 12px;
  background: #37474f;
  position: relative;
}
.badge {
  min-width: 20px; height: 20px; padding: 0 5px; box-sizing: border-box;
  background: #d32f2f; color: white;
  font: 700 12px/20px system-ui, sans-serif; text-align: center;
  position: absolute;
  top: -6px;
  right: -6px;
  border-radius: 999px;
}
""", BADGE_HTML),
    checks=[
        C(".icon is position: relative", "getComputedStyle(document.querySelector('.icon')).position === 'relative'"),
        C(".icon is still 48 by 48 pixels", "(r => Math.round(r.width) === 48 && Math.round(r.height) === 48)(" + (RECT % ".icon") + ")"),
        C(".badge is position: absolute", "getComputedStyle(document.querySelector('.badge')).position === 'absolute'"),
        C("The badge is positioned relative to the icon", "document.querySelector('.badge').offsetParent === document.querySelector('.icon')"),
        C("The badge overhangs the right edge by 6px", "((i, b) => Math.round(b.right - i.right) === 6)(" + (RECT % ".icon") + ", " + (RECT % ".badge") + ")"),
        C("The badge overhangs the top edge by 6px", "((i, b) => Math.round(i.top - b.top) === 6)(" + (RECT % ".icon") + ", " + (RECT % ".badge") + ")"),
        C("The badge is round", "(v => v.endsWith('%') ? parseFloat(v) >= 50 : parseFloat(v) >= 10)(getComputedStyle(document.querySelector('.badge')).borderTopLeftRadius)"),
    ],
    guide=dict(
        prereqs="`position: relative` and `absolute`, offsets, containing blocks. See *Normal flow, display, positioning and stacking*.",
        intuition="An absolutely positioned element measures its offsets from the nearest ancestor that is itself positioned. `position: relative` with no offsets leaves the icon exactly where it was but promotes it to that role. Negative offsets then move the badge *outside* the icon's edges.",
        hints=[
            "Parent first: add `position: relative` to `.icon`.",
            "Child next: `position: absolute` on `.badge`, then `top` and `right`.",
            "`right: 0` would line the badge's right edge up with the icon's. To overhang by 6px use `right: -6px`, and likewise `top: -6px`. Finish with `border-radius: 999px`.",
        ],
        approach="1. `.icon { position: relative; }`\n2. `.badge { position: absolute; top: -6px; right: -6px; }`\n3. `border-radius: 999px;` makes a pill or circle whatever the number inside.\n4. Remove the `position: relative` temporarily to see the badge jump to the corner of the page: that is what a missing reference frame looks like.",
        pitfalls="- Forgetting `position: relative` on the parent.\n- Using `left`/`bottom` and trying to calculate the icon's size: `top` and `right` anchor to the corner you care about.\n- Positive offsets, which push the badge inward.\n- Giving `.icon` offsets as well, which would move it.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-z-index-stack", title="Control the stacking order", difficulty="Medium", pattern="Positioning", kind="web",
    description=r"""
Three overlapping cards are drawn in source order, so C (last in the HTML) is on top. Reverse that **with CSS only**, and make sure the toast message stays above everything.

Requirements:

- Do not change the order of the cards in the HTML (A, B, C).
- Card **A** is on top, **B** in the middle, **C** at the bottom: their `z-index` values satisfy A > B > C (all numeric).
- `.stack` forms its own stacking context using `isolation: isolate`, so the cards' z-indexes cannot interfere with the rest of the page.
- `.toast` is `position: fixed` and has a numeric `z-index` of at least 1, which is enough to appear above the isolated stack.
- No `z-index` in the style sheet is larger than **10** (no "9999" arms race).
""",
    starter=page("Stacking", """
body { font-family: system-ui, sans-serif; margin: 0; padding: 24px; }
.stack { position: relative; height: 200px; }
.card { position: absolute; width: 160px; height: 110px; padding: 10px; color: white; font-weight: 700; border-radius: 12px; box-shadow: 0 3px 10px rgb(0 0 0 / .4); }
.a { left: 0;    top: 0;    background: #e53935; }
.b { left: 70px; top: 30px; background: #1e88e5; }
.c { left: 140px; top: 60px; background: #43a047; }
.toast { left: 90px; top: 70px; background: #212121; color: white; padding: 10px 16px; border-radius: 8px; }

/* your code */
""", STACK_HTML),
    solution=page("Stacking", """
body { font-family: system-ui, sans-serif; margin: 0; padding: 24px; }
.stack { position: relative; height: 200px; }
.card { position: absolute; width: 160px; height: 110px; padding: 10px; color: white; font-weight: 700; border-radius: 12px; box-shadow: 0 3px 10px rgb(0 0 0 / .4); }
.a { left: 0;    top: 0;    background: #e53935; }
.b { left: 70px; top: 30px; background: #1e88e5; }
.c { left: 140px; top: 60px; background: #43a047; }
.toast { left: 90px; top: 70px; background: #212121; color: white; padding: 10px 16px; border-radius: 8px; }

.stack { isolation: isolate; }
.a { z-index: 3; }
.b { z-index: 2; }
.c { z-index: 1; }
.toast { position: fixed; z-index: 1; }
""", STACK_HTML),
    checks=[
        C("The HTML order of the cards is still A, B, C", "[...document.querySelectorAll('.stack > .card')].map(e => e.textContent.trim()).join('') === 'ABC'"),
        C("z-index of A > B > C", "(z => z[0] > z[1] && z[1] > z[2])(['.a', '.b', '.c'].map(s => parseInt(getComputedStyle(document.querySelector(s)).zIndex, 10)))"),
        C(".stack uses isolation: isolate", "getComputedStyle(document.querySelector('.stack')).isolation === 'isolate'"),
        C(".toast is fixed with a z-index of at least 1", "(c => c.position === 'fixed' && parseInt(c.zIndex, 10) >= 1)(getComputedStyle(document.querySelector('.toast')))"),
        C("No z-index is larger than 10", "(z => z.length >= 4 && z.every(v => Math.abs(v) <= 10))(" + RULES + ".filter(r => r.style && r.style.zIndex && r.style.zIndex !== 'auto').map(r => parseInt(r.style.zIndex, 10)))"),
        C("Card A is the topmost card where all three overlap", "(e => !!e && e.classList.contains('a'))(document.elementsFromPoint(24 + 150, 24 + 80).find(e => e.classList.contains('card')))"),
    ],
    guide=dict(
        prereqs="`z-index`, positioned elements and stacking contexts. See *Normal flow, display, positioning and stacking*.",
        intuition="`z-index` orders positioned elements, but only against siblings in the same stacking context. `isolation: isolate` turns `.stack` into a sealed group: inside it the cards are ordered 3, 2, 1; from outside, the whole group behaves as one layer at the default level. The fixed toast with `z-index: 1` is therefore above the entire group, even though a card inside has a higher number.",
        hints=[
            "The cards are already `position: absolute`, so `z-index` will take effect on them. Give A the highest value and C the lowest.",
            "Add `isolation: isolate` to `.stack`.",
            "Make the toast `position: fixed` and give it `z-index: 1`. Small numbers are enough when contexts are isolated.",
        ],
        approach="1. `.a { z-index: 3; } .b { z-index: 2; } .c { z-index: 1; }`\n2. `.stack { isolation: isolate; }`\n3. `.toast { position: fixed; z-index: 1; }`\n4. Reason it through: the root stacking context contains the stack (level auto) and the toast (level 1); the toast wins. Inside the stack, 3 beats 2 beats 1.",
        pitfalls="- Reordering the HTML: that changes reading and tab order too.\n- `z-index` on an element with `position: static`: it is ignored.\n- Reaching for 9999. Large numbers do not escape a stacking context; they only make the next conflict harder to reason about.\n- Forgetting that the toast needs a `position` for both its offsets and its z-index to apply.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-sticky-header", title="A sticky header", difficulty="Easy", pattern="Positioning", kind="web",
    description=r"""
Keep the header visible at the top of the viewport while the long page scrolls underneath it.

Requirements:

- `.bar` uses `position: sticky` with `top: 0`.
- `.bar` has an opaque `background-color` (not transparent), so the text scrolling beneath does not show through.
- `.bar` has a numeric `z-index` of at least 1, so it is painted above the content.
- After the page is scrolled down by 600px, the header's top edge is still at the top of the viewport.
- The header remains a direct child of `<body>` (it sticks only within its parent, so the parent must be tall).
""",
    starter=page("Notices", """
body { margin: 0; font-family: system-ui, sans-serif; }
main { padding: 0 24px; }
.bar {
  padding: 14px 24px;
  font-weight: 700;
  color: white;
  /* your code */
}
""", STICKY_HTML),
    solution=page("Notices", """
body { margin: 0; font-family: system-ui, sans-serif; }
main { padding: 0 24px; }
.bar {
  padding: 14px 24px;
  font-weight: 700;
  color: white;
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: rgb(0, 77, 64);
}
""", STICKY_HTML),
    checks=[
        C(".bar is position: sticky with top: 0", "(c => c.position === 'sticky' && c.top === '0px')(getComputedStyle(document.querySelector('.bar')))"),
        C(".bar has an opaque background colour", "(b => b !== 'rgba(0, 0, 0, 0)' && b !== 'transparent' && (!b.startsWith('rgba') || parseFloat(b.split(',')[3]) === 1))(getComputedStyle(document.querySelector('.bar')).backgroundColor)"),
        C(".bar has a z-index of at least 1", "parseInt(getComputedStyle(document.querySelector('.bar')).zIndex, 10) >= 1"),
        C("The header is a direct child of body", "document.querySelector('.bar').parentElement === document.body"),
        C("The page is long enough to scroll", "document.documentElement.scrollHeight > window.innerHeight + 700"),
        C("After scrolling 600px the header is still at the top", "(() => { window.scrollTo(0, 600); const t = document.querySelector('.bar').getBoundingClientRect().top; const y = window.scrollY; window.scrollTo(0, 0); return y >= 590 && Math.abs(t) < 1; })()"),
    ],
    guide=dict(
        prereqs="`position: sticky`, offsets and `z-index`. See *Normal flow, display, positioning and stacking*.",
        intuition="A sticky element is an ordinary in-flow element until scrolling would push it past the offset you name. From then on it stays at that offset, for as long as its parent is still in view. It needs the threshold (`top: 0`) to know *where* to stick, a background so that it hides what passes beneath, and a z-index so that later content is not painted over it.",
        hints=[
            "Two declarations do the sticking: `position: sticky;` and `top: 0;`.",
            "Scroll the preview: the text is visible through the header. Give it a solid `background-color`.",
            "Add `z-index: 1` so that positioned content further down the page cannot cover it.",
        ],
        approach="1. `position: sticky; top: 0;`\n2. `background-color: rgb(0, 77, 64);` (any opaque colour with enough contrast against the white text).\n3. `z-index: 1;`\n4. Scroll the preview to confirm.",
        pitfalls="- `position: sticky` without `top`: nothing happens.\n- Wrapping the header in a container that is only as tall as the header: it has no room to slide and scrolls away with its parent.\n- An ancestor with `overflow: hidden` or `auto` becomes the scroll container and usually breaks the effect.\n- Using `position: fixed` instead: the header leaves the flow and covers the first lines of content.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-footer-bottom", title="Footer pinned to the bottom", difficulty="Easy", pattern="Flexbox", kind="web",
    description=r"""
This page has very little content, so the footer floats in the middle of the window. Push it to the bottom **without** taking it out of the flow.

Requirements:

- `<body>` is a flex container with `flex-direction: column` and is at least as tall as the viewport.
- `<main>` grows to absorb the spare height (`flex-grow: 1`).
- The footer's bottom edge is at the bottom edge of the viewport.
- The footer keeps `position: static` (no `fixed` or `absolute`), so on a long page it would follow the content normally.
""",
    starter=page("Timetable", """
body { margin: 0; font-family: system-ui, sans-serif; }
header, footer { background: #004d40; color: white; padding: 14px 24px; }
main { padding: 24px; }

/* your code */
""", FOOTER_HTML),
    solution=page("Timetable", """
body { margin: 0; font-family: system-ui, sans-serif; }
header, footer { background: #004d40; color: white; padding: 14px 24px; }
main { padding: 24px; }

body {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
main {
  flex: 1;
}
""", FOOTER_HTML),
    checks=[
        C("body is a column flex container", "(c => c.display === 'flex' && c.flexDirection === 'column')(getComputedStyle(document.body))"),
        C("body is at least as tall as the viewport", "document.body.getBoundingClientRect().height >= window.innerHeight - 1"),
        C("main has flex-grow: 1", "getComputedStyle(document.querySelector('main')).flexGrow === '1'"),
        C("The footer's bottom edge is at the bottom of the viewport", "Math.abs(document.querySelector('footer').getBoundingClientRect().bottom - window.innerHeight) < 1.5"),
        C("The header is still at the top", "Math.abs(document.querySelector('header').getBoundingClientRect().top) < 1"),
        C("The footer is not fixed or absolute", "getComputedStyle(document.querySelector('footer')).position === 'static'"),
    ],
    guide=dict(
        prereqs="Column flex containers, `min-height`, `flex-grow`. See *Flexbox in depth*.",
        intuition="Stack header, main and footer in a column that is at least one viewport tall. On a short page that leaves spare vertical space. `flex: 1` tells `main` to take all of it, which pushes the footer to the bottom. On a long page there is no spare space and the footer follows the content.",
        hints=[
            "Make the `body` the flex container: `display: flex; flex-direction: column;`.",
            "A column only has spare height if you give it some: `min-height: 100vh`.",
            "`main { flex: 1; }` grows the middle section.",
        ],
        approach="1. `body { display: flex; flex-direction: column; min-height: 100vh; }`\n2. `main { flex: 1; }`\n3. Add more paragraphs to `main` to confirm that the footer moves down with long content instead of overlapping it.",
        pitfalls="- `position: fixed` on the footer: it then covers content on long pages.\n- `height: 100vh` instead of `min-height`, which makes long content overflow the body.\n- Forgetting `margin: 0` on the body (already in the starter): the default 8px margin would make the page 16px taller than the window.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-two-column-grid", title="Sidebar and content with Grid", difficulty="Easy", pattern="Grid", kind="web",
    description=r"""
Place the sidebar beside the main content using **CSS Grid**.

Requirements:

- `.layout` is a grid with **two** columns: a fixed **240px** sidebar and a flexible column that takes the rest (`1fr`).
- The gap between the columns is **24px**.
- The sidebar and the content start at the same vertical position (same row).
- In the 1024px frame the content column is wider than 600px.
""",
    starter=page("Search", """
* { box-sizing: border-box; }
body { margin: 0; padding: 24px; font-family: system-ui, sans-serif; }
.sidebar { background: #d1c4e9; padding: 16px; border-radius: 10px; }
.content { background: #f3e5f5; padding: 16px; border-radius: 10px; min-height: 200px; }
.layout {
  /* your code */
}
""", TWOCOL_HTML),
    solution=page("Search", """
* { box-sizing: border-box; }
body { margin: 0; padding: 24px; font-family: system-ui, sans-serif; }
.sidebar { background: #d1c4e9; padding: 16px; border-radius: 10px; }
.content { background: #f3e5f5; padding: 16px; border-radius: 10px; min-height: 200px; }
.layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
}
""", TWOCOL_HTML),
    checks=[
        C(".layout is a grid", "getComputedStyle(document.querySelector('.layout')).display === 'grid'"),
        C("The grid has two columns and the first is 240px", "(c => c.length === 2 && c[0] === '240px')(getComputedStyle(document.querySelector('.layout')).gridTemplateColumns.split(' '))"),
        C("The sidebar is 240px wide", "Math.round(" + (RECT % ".sidebar") + ".width) === 240"),
        C("Sidebar and content are on the same row", "((s, c) => Math.abs(s.top - c.top) < 1 && s.left < c.left)(" + (RECT % ".sidebar") + ", " + (RECT % ".content") + ")"),
        C("The gap is 24px", "((s, c) => Math.round(c.left - s.right) === 24)(" + (RECT % ".sidebar") + ", " + (RECT % ".content") + ")"),
        C("The content column takes the remaining width", (RECT % ".content") + ".width > 600"),
    ],
    guide=dict(
        prereqs="`display: grid`, `grid-template-columns`, the `fr` unit and `gap`. See *CSS Grid in depth*.",
        intuition="`grid-template-columns` lists the width of each column. A fixed length reserves exactly that much; `1fr` means \"one share of whatever is left\". With a single `fr` column, it takes all the remaining space after the 240px column and the gap are subtracted.",
        hints=[
            "Turn `.layout` into a grid container with `display: grid`.",
            "Two values in `grid-template-columns` make two columns: a length for the sidebar and `1fr` for the content.",
            "Use `gap: 24px` for the gutter; do not add margins to the children.",
        ],
        approach="1. `display: grid;`\n2. `grid-template-columns: 240px 1fr;`\n3. `gap: 24px;`\n4. The two children are auto-placed into the two cells of the first row.",
        pitfalls="- `grid-template-columns: 240px 100%`: the second column would be as wide as the container and overflow.\n- Using margin for the gutter, which adds space at the outer edge too.\n- Writing the declarations on the children instead of on `.layout`.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-holy-grail", title="The holy grail layout", difficulty="Hard", pattern="Grid", kind="web",
    description=r"""
Build the classic page skeleton with **`grid-template-areas`**: a header across the top, a footer across the bottom, and three columns in between.

Requirements (checked in the 1024 by 768 frame):

- `.page` is a grid, at least as tall as the viewport, and its `grid-template-areas` is set (not `none`).
- `header` and `footer` each span the full width of the three columns.
- `nav`, `main` and `aside` sit side by side in the middle row, in that order from left to right.
- `nav` and `aside` are each **180px** wide; `main` takes the remaining width (more than 500px).
- The rows are sized so that the middle row stretches: the footer's bottom edge is at the bottom of the viewport.
- The HTML order (header, nav, main, aside, footer) must not change.
""",
    starter=page("Holy grail", """
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
.page > * { padding: 16px; }
header { background: #90caf9; }
nav    { background: #ce93d8; }
main   { background: #a5d6a7; }
aside  { background: #ffcc80; }
footer { background: #b0bec5; }

.page {
  /* your code */
}
""", GRAIL_HTML),
    solution=page("Holy grail", """
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
.page > * { padding: 16px; }
header { background: #90caf9; }
nav    { background: #ce93d8; }
main   { background: #a5d6a7; }
aside  { background: #ffcc80; }
footer { background: #b0bec5; }

.page {
  display: grid;
  min-height: 100vh;
  grid-template-columns: 180px 1fr 180px;
  grid-template-rows: auto 1fr auto;
  grid-template-areas:
    "header header header"
    "nav    main   aside"
    "footer footer footer";
}
header { grid-area: header; }
nav    { grid-area: nav; }
main   { grid-area: main; }
aside  { grid-area: aside; }
footer { grid-area: footer; }
""", GRAIL_HTML),
    checks=[
        C(".page is a grid using grid-template-areas", "(c => c.display === 'grid' && c.gridTemplateAreas !== 'none')(getComputedStyle(document.querySelector('.page')))"),
        C("nav, main and aside share the middle row, left to right", "((n, m, a) => Math.abs(n.top - m.top) < 1 && Math.abs(m.top - a.top) < 1 && n.right <= m.left + 1 && m.right <= a.left + 1)(" + (RECT % ".page > nav") + ", " + (RECT % ".page > main") + ", " + (RECT % ".page > aside") + ")"),
        C("nav and aside are 180px wide and main is wider than 500px", "((n, m, a) => Math.round(n.width) === 180 && Math.round(a.width) === 180 && m.width > 500)(" + (RECT % ".page > nav") + ", " + (RECT % ".page > main") + ", " + (RECT % ".page > aside") + ")"),
        C("The header spans all three columns", "((h, n, a) => Math.abs(h.left - n.left) < 1 && Math.abs(h.right - a.right) < 1 && h.bottom <= n.top + 1)(" + (RECT % ".page > header") + ", " + (RECT % ".page > nav") + ", " + (RECT % ".page > aside") + ")"),
        C("The footer spans all three columns below the middle row", "((f, n, a) => Math.abs(f.left - n.left) < 1 && Math.abs(f.right - a.right) < 1 && f.top >= n.bottom - 1)(" + (RECT % ".page > footer") + ", " + (RECT % ".page > nav") + ", " + (RECT % ".page > aside") + ")"),
        C("The middle row stretches so the footer reaches the viewport bottom", "((f, m) => Math.abs(f.bottom - window.innerHeight) < 2 && m.height > 400)(" + (RECT % ".page > footer") + ", " + (RECT % ".page > main") + ")"),
        C("The HTML order is unchanged", "[...document.querySelector('.page').children].map(e => e.tagName).join() === 'HEADER,NAV,MAIN,ASIDE,FOOTER'"),
    ],
    guide=dict(
        prereqs="`grid-template-columns`, `grid-template-rows`, `grid-template-areas`, `grid-area`. See *CSS Grid in depth*.",
        intuition="`grid-template-areas` lets you draw the layout as text: each quoted string is a row and each word a column. Repeating a name across a row makes that area span those columns. Each child then claims its area by name. Row sizes of `auto 1fr auto` mean \"header and footer as tall as their content; the middle takes whatever height is left\".",
        hints=[
            "Start with the tracks: three columns (`180px 1fr 180px`) and three rows (`auto 1fr auto`), plus `min-height: 100vh` so the `1fr` row has height to claim.",
            "Draw the areas: the header name three times in the first string, then `nav main aside`, then the footer name three times.",
            "Give each of the five children a matching `grid-area`. The names are your own choice, but they must match the template exactly.",
        ],
        approach="1. `.page { display: grid; min-height: 100vh; }`\n2. `grid-template-columns: 180px 1fr 180px;`\n3. `grid-template-rows: auto 1fr auto;`\n4. `grid-template-areas: \"header header header\" \"nav main aside\" \"footer footer footer\";`\n5. `header { grid-area: header; }` and so on for the other four.",
        pitfalls="- A misspelled area name, or rows with different numbers of words: the whole template is invalid and ignored.\n- Quoting the name in `grid-area` (`grid-area: \"header\"`): it takes a bare identifier.\n- Forgetting `min-height`: the grid is only as tall as its content and the footer does not reach the bottom.\n- Trying to achieve the spans by reordering HTML; areas place items regardless of source order, but the order should stay logical for keyboard and screen-reader users.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-modal-layout", title="A centred modal dialog", difficulty="Hard", pattern="Positioning", kind="web",
    description=r"""
Style and label a modal dialog that is already open: a dimmed overlay covering the whole viewport with a panel centred in it.

Requirements:

- `.overlay` is `position: fixed` with all four offsets at 0 (for example `inset: 0`), so it covers the viewport exactly.
- `.overlay` has a **semi-transparent** background colour (alpha greater than 0 and less than 1) and a `z-index` of at least 10.
- `.modal` is centred both horizontally and vertically in the viewport.
- `.modal` is at most **480px** wide (and at least 300px in this frame), with an opaque background.
- Accessibility: `.modal` has `role="dialog"`, `aria-modal="true"`, and `aria-labelledby` pointing at the id of the heading inside it.
- The close button (`.close`) has an accessible name of more than one character (its visible content is only a multiplication sign, so add an `aria-label`).
""",
    starter=page("Modal", """
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
main { padding: 24px; }
.modal { padding: 24px; border-radius: 14px; }
.close { float: right; font: inherit; border: 0; background: none; font-size: 1.4rem; cursor: pointer; }

.overlay {
  /* your code */
}
.modal {
  /* your code */
}
""", """
<main>
  <h1>Berth bookings</h1>
  <p>Your booking for berth 14 runs until Friday.</p>
</main>
<div class="overlay">
  <div class="modal">
    <button class="close" type="button">&times;</button>
    <h2>Cancel this booking?</h2>
    <p>The berth will be released to other visitors.</p>
    <button type="button">Keep booking</button>
    <button type="button">Cancel booking</button>
  </div>
</div>
"""),
    solution=page("Modal", """
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
main { padding: 24px; }
.modal { padding: 24px; border-radius: 14px; }
.close { float: right; font: inherit; border: 0; background: none; font-size: 1.4rem; cursor: pointer; }

.overlay {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: grid;
  place-items: center;
  background-color: rgb(0 0 0 / 0.5);
}
.modal {
  width: min(480px, 90%);
  background-color: white;
  box-shadow: 0 10px 40px rgb(0 0 0 / 0.4);
}
""", """
<main>
  <h1>Berth bookings</h1>
  <p>Your booking for berth 14 runs until Friday.</p>
</main>
<div class="overlay">
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <button class="close" type="button" aria-label="Close dialog">&times;</button>
    <h2 id="modal-title">Cancel this booking?</h2>
    <p>The berth will be released to other visitors.</p>
    <button type="button">Keep booking</button>
    <button type="button">Cancel booking</button>
  </div>
</div>
"""),
    checks=[
        C(".overlay is fixed with all offsets 0", "(c => c.position === 'fixed' && [c.top, c.right, c.bottom, c.left].every(v => v === '0px'))(getComputedStyle(document.querySelector('.overlay')))"),
        C(".overlay covers the whole viewport", "(r => Math.abs(r.width - document.documentElement.clientWidth) < 1 && Math.abs(r.height - window.innerHeight) < 1 && Math.abs(r.top) < 1)(" + (RECT % ".overlay") + ")"),
        C(".overlay has a semi-transparent background", "(b => b.startsWith('rgba') && parseFloat(b.split(',')[3]) > 0 && parseFloat(b.split(',')[3]) < 1)(getComputedStyle(document.querySelector('.overlay')).backgroundColor)"),
        C(".overlay has a z-index of at least 10", "parseInt(getComputedStyle(document.querySelector('.overlay')).zIndex, 10) >= 10"),
        C(".modal is centred in the viewport", "(r => Math.abs((r.left + r.right) / 2 - document.documentElement.clientWidth / 2) < 2 && Math.abs((r.top + r.bottom) / 2 - window.innerHeight / 2) < 2)(" + (RECT % ".modal") + ")"),
        C(".modal is 300 to 480px wide with an opaque background", "(m => m.getBoundingClientRect().width <= 480.5 && m.getBoundingClientRect().width >= 300 && (b => b !== 'rgba(0, 0, 0, 0)' && !b.startsWith('rgba'))(getComputedStyle(m).backgroundColor))(document.querySelector('.modal'))"),
        C("role=dialog, aria-modal=true and aria-labelledby reference the heading", "(m => m.getAttribute('role') === 'dialog' && m.getAttribute('aria-modal') === 'true' && (h => !!h && m.contains(h) && /^H[1-6]$/.test(h.tagName))(document.getElementById(m.getAttribute('aria-labelledby') || '-')))(document.querySelector('.modal'))"),
        C("The close button has an accessible name", "(b => ((b.getAttribute('aria-label') || '').trim() || b.textContent.trim()).length > 1)(document.querySelector('.modal .close'))"),
    ],
    guide=dict(
        prereqs="`position: fixed`, `inset`, alpha colours, grid centring, `z-index`; `role`, `aria-modal`, `aria-labelledby`, `aria-label`. See *Normal flow, display, positioning and stacking* and *Accessibility*.",
        intuition="The overlay is a fixed box stretched to all four edges of the viewport, so it covers the page and does not scroll. Making that box a grid with `place-items: center` centres its only child, the panel, without any arithmetic. The translucent colour must be an *alpha colour* on the overlay, not `opacity`, because opacity would fade the panel as well. The ARIA attributes tell assistive technology that this is a dialog and what it is called.",
        hints=[
            "Overlay: `position: fixed; inset: 0;` plus a background such as `rgb(0 0 0 / 0.5)` and `z-index: 10`.",
            "Centre the panel by turning the overlay into a grid: `display: grid; place-items: center;`. Limit the panel with `width: min(480px, 90%)` and give it a solid background.",
            "In the HTML add `role=\"dialog\" aria-modal=\"true\" aria-labelledby=\"modal-title\"` to `.modal`, `id=\"modal-title\"` to the `h2`, and `aria-label=\"Close dialog\"` to the close button.",
        ],
        approach="1. `.overlay { position: fixed; inset: 0; z-index: 10; background-color: rgb(0 0 0 / .5); }`\n2. `.overlay { display: grid; place-items: center; }`\n3. `.modal { width: min(480px, 90%); background-color: white; }`\n4. Add the three ARIA attributes and the heading id.\n5. Name the close button.\n\nIn a real project prefer the native `<dialog>` element with `showModal()`: it supplies the backdrop, focus trapping and Escape handling for you.",
        pitfalls="- `opacity: 0.5` on the overlay makes the panel translucent too.\n- `position: absolute` instead of `fixed`: the overlay scrolls away with the page.\n- An `aria-labelledby` value that does not match any id labels nothing.\n- A close button whose only content is a symbol is announced as \"times\" or \"multiplication sign\".\n- This exercise covers layout and labelling only; a working modal must also move focus into the dialog, keep it there, close on Escape and return focus afterwards.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-auto-fit-cards", title="Responsive card grid with auto-fit", difficulty="Medium", pattern="Grid", kind="web",
    description=r"""
Lay the six cards out in a grid that chooses its own number of columns from the available width, **without any media queries**.

Requirements:

- `.cards` is a grid whose `grid-template-columns` uses `repeat()` with `auto-fit` (or `auto-fill`) and `minmax(220px, 1fr)`.
- The gap is **16px**.
- In the 1024px-wide frame this produces exactly **four** columns: cards 1 to 4 on the first row at four different horizontal positions, and card 5 starting a second row directly under card 1.
- All cards have the same width, at least 220px.
- The style sheet contains no `@media` rule.
""",
    starter=page("Seaweeds", """
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
.cards {
  padding: 16px;
  /* your code */
}
.card { background: #e0f2f1; border-radius: 12px; padding: 24px; min-height: 100px; }
""", CARDS_HTML),
    solution=page("Seaweeds", """
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
.cards {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.card { background: #e0f2f1; border-radius: 12px; padding: 24px; min-height: 100px; }
""", CARDS_HTML),
    checks=[
        C(".cards is a grid", "getComputedStyle(document.querySelector('.cards')).display === 'grid'"),
        C("grid-template-columns uses auto-fit or auto-fill with minmax(220px, 1fr)", RULES + ".some(r => r.style && /auto-fi(t|ll)/.test(r.style.gridTemplateColumns) && r.style.gridTemplateColumns.replace(/\\s/g, '').includes('minmax(220px,1fr)'))"),
        C("There are four columns at 1024px: cards 1 to 4 have four different left positions", "(r => r.length === 6 && new Set(r.slice(0, 4).map(x => Math.round(x.left))).size === 4 && r.slice(0, 4).every(x => Math.abs(x.top - r[0].top) < 1))([...document.querySelectorAll('.card')].map(e => e.getBoundingClientRect()))"),
        C("Card 5 starts a second row under card 1", "(r => r[4].top > r[0].bottom - 1 && Math.abs(r[4].left - r[0].left) < 1 && Math.abs(r[5].left - r[1].left) < 1)([...document.querySelectorAll('.card')].map(e => e.getBoundingClientRect()))"),
        C("All cards are the same width, at least 220px", "(r => r.every(x => Math.abs(x.width - r[0].width) < 1 && x.width >= 220))([...document.querySelectorAll('.card')].map(e => e.getBoundingClientRect()))"),
        C("The gap is 16px in both directions", "(r => Math.round(r[1].left - r[0].right) === 16 && Math.round(r[4].top - r[0].bottom) === 16)([...document.querySelectorAll('.card')].map(e => e.getBoundingClientRect()))"),
        C("No media queries are used", "!" + RULES + ".some(r => r instanceof CSSMediaRule)"),
    ],
    guide=dict(
        prereqs="`repeat()`, `auto-fit`, `minmax()`, `fr` and `gap`. See *CSS Grid in depth* and *Responsive design*.",
        intuition="`minmax(220px, 1fr)` describes one column: never narrower than 220px, and allowed to grow to an equal share of the free space. `repeat(auto-fit, ...)` asks the browser to fit as many of those columns as the container can hold. The arithmetic for this frame: the container's content box is 1024 - 32 = 992px. Four columns need 4 x 220 + 3 x 16 = 928px, which fits; five would need 1164px, which does not. So there are four columns, each stretched to (992 - 48) / 4 = 236px.",
        hints=[
            "Begin with `display: grid; gap: 16px;` on `.cards`.",
            "Instead of a fixed number of columns, write `repeat(auto-fit, <one column>)`.",
            "The one column is `minmax(220px, 1fr)`. The full declaration: `grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));`.",
        ],
        approach="1. `display: grid;`\n2. `grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));`\n3. `gap: 16px;`\n4. Narrow the preview to watch the column count fall from four to three, two and one with no breakpoint written anywhere.",
        pitfalls="- `repeat(4, 1fr)` passes at this width but is not responsive: on a phone the columns would be far too narrow.\n- Using flexbox with wrapping: the last row's items would stretch differently from the rows above.\n- On containers narrower than 220px the column overflows; `minmax(min(220px, 100%), 1fr)` guards against that in production code.\n- Adding media queries, which this technique makes unnecessary.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-custom-props-theme", title="A light and dark theme with custom properties", difficulty="Medium", pattern="Custom properties", kind="web",
    description=r"""
Replace the hard-coded colours with **custom properties** and add a dark theme that is switched by an attribute on the root element.

Requirements:

- `:root` defines `--bg`, `--text` and `--accent`.
  - Light values: `--bg` white (`rgb(255, 255, 255)`), `--text` `rgb(31, 35, 40)`, `--accent` `rgb(11, 87, 208)`.
- When `<html>` has `data-theme="dark"`, the same three properties are redefined:
  - `--bg` `rgb(17, 20, 24)`, `--text` `rgb(230, 232, 235)`, `--accent` `rgb(138, 180, 248)`.
- `body` uses `var(--bg)` for its background and `var(--text)` for its text colour.
- `.btn` uses `var(--accent)` for its background colour.
- At least three declarations in the style sheet use `var(--...)`.

The checks read the colours, then set `data-theme="dark"` on `<html>` and read them again.
""",
    starter=page("Tide alerts", """
body { font-family: system-ui, sans-serif; margin: 0; padding: 24px; background-color: rgb(255, 255, 255); color: rgb(31, 35, 40); }
.panel { max-width: 24rem; }
.btn { font: inherit; border: 0; border-radius: 8px; padding: 10px 16px; color: white; background-color: rgb(11, 87, 208); }

/* your code */
""", THEME_HTML),
    solution=page("Tide alerts", """
:root {
  --bg: rgb(255, 255, 255);
  --text: rgb(31, 35, 40);
  --accent: rgb(11, 87, 208);
  --on-accent: rgb(255, 255, 255);
}
:root[data-theme="dark"] {
  --bg: rgb(17, 20, 24);
  --text: rgb(230, 232, 235);
  --accent: rgb(138, 180, 248);
  --on-accent: rgb(11, 27, 51);
}
body { font-family: system-ui, sans-serif; margin: 0; padding: 24px; background-color: var(--bg); color: var(--text); }
.panel { max-width: 24rem; }
.btn { font: inherit; border: 0; border-radius: 8px; padding: 10px 16px; color: var(--on-accent); background-color: var(--accent); }
""", THEME_HTML),
    checks=[
        C(":root defines --bg, --text and --accent", "['--bg', '--text', '--accent'].every(p => getComputedStyle(document.documentElement).getPropertyValue(p).trim() !== '')"),
        C("Light theme: white page, dark text", "(c => c.backgroundColor === 'rgb(255, 255, 255)' && c.color === 'rgb(31, 35, 40)')(getComputedStyle(document.body))"),
        C("Light theme: the button uses the blue accent", "getComputedStyle(document.querySelector('.btn')).backgroundColor === 'rgb(11, 87, 208)'"),
        C("At least three declarations use var(--...)", RULES + ".filter(r => r.style).reduce((n, r) => n + [...r.style].filter(p => !p.startsWith('--') && r.style.getPropertyValue(p).includes('var(--')).length, 0) >= 3"),
        C("Dark theme: page colours change when data-theme=dark is set", "(() => { const h = document.documentElement; h.setAttribute('data-theme', 'dark'); const c = getComputedStyle(document.body); const ok = c.backgroundColor === 'rgb(17, 20, 24)' && c.color === 'rgb(230, 232, 235)'; h.removeAttribute('data-theme'); return ok; })()"),
        C("Dark theme: the button accent changes too", "(() => { const h = document.documentElement; h.setAttribute('data-theme', 'dark'); const ok = getComputedStyle(document.querySelector('.btn')).backgroundColor === 'rgb(138, 180, 248)'; h.removeAttribute('data-theme'); return ok; })()"),
        C("The custom properties themselves are redefined in dark mode", "(() => { const h = document.documentElement; const a = getComputedStyle(h).getPropertyValue('--accent').trim(); h.setAttribute('data-theme', 'dark'); const b = getComputedStyle(h).getPropertyValue('--accent').trim(); h.removeAttribute('data-theme'); return a !== '' && b !== '' && a !== b; })()"),
    ],
    guide=dict(
        prereqs="Declaring custom properties, `var()`, inheritance and attribute selectors. See *Custom properties and theming*.",
        intuition="A theme is a set of named values. Components refer to the names, never to the colours themselves. Because custom properties inherit, redefining the names on the root element changes what every `var()` on the page resolves to, so switching theme is a matter of changing one attribute.",
        hints=[
            "Create a `:root { ... }` rule declaring `--bg`, `--text` and `--accent` with the light values.",
            "Replace each hard-coded colour in `body` and `.btn` with `var(--name)`.",
            "Add a second rule, `:root[data-theme=\"dark\"] { ... }`, that declares the same three names with the dark values. It must come after the first rule or have higher specificity (the attribute selector gives it that).",
        ],
        approach="1. `:root { --bg: rgb(255, 255, 255); --text: rgb(31, 35, 40); --accent: rgb(11, 87, 208); }`\n2. `body { background-color: var(--bg); color: var(--text); }`\n3. `.btn { background-color: var(--accent); }`\n4. `:root[data-theme=\"dark\"] { --bg: rgb(17, 20, 24); --text: rgb(230, 232, 235); --accent: rgb(138, 180, 248); }`\n5. Test by adding `data-theme=\"dark\"` to the `<html>` tag in the editor.\n\nThe solution also introduces `--on-accent` for the button's text, because white text on the pale dark-mode accent would have poor contrast.",
        pitfalls="- Writing `color: --text` without `var()`.\n- Redefining the properties on `body[data-theme]` while the attribute is set on `<html>`.\n- Leaving one hard-coded colour behind: it will not change with the theme.\n- Naming variables after their appearance (`--white`), which becomes misleading in the dark theme.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-transition-hover", title="A hover lift with a transition", difficulty="Easy", pattern="Motion", kind="web",
    description=r"""
Make the card rise gently when it is hovered, and respect people who prefer less motion.

Requirements:

- The base rule `.card` (selector exactly `.card`) declares a transition on **`transform`** and **`box-shadow`** (not `all`), each lasting **0.2s**.
- At rest the card has no transform.
- A rule whose selector contains `.card:hover` moves the card up with `transform` (or `translate`) and changes its `box-shadow`.
- An `@media (prefers-reduced-motion: reduce)` block exists and, inside it, a rule for `.card` removes the transition (`transition: none`).
""",
    starter=page("Card hover", """
body { font-family: system-ui, sans-serif; padding: 40px; background: #eceff1; }
.card {
  background: white; border-radius: 14px; padding: 20px 24px; max-width: 20rem;
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.2);
  /* your code */
}
.card h2 { margin: 0 0 .3rem; }
.card p { margin: 0; }

/* your code */
""", HOVER_HTML),
    solution=page("Card hover", """
body { font-family: system-ui, sans-serif; padding: 40px; background: #eceff1; }
.card {
  background: white; border-radius: 14px; padding: 20px 24px; max-width: 20rem;
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.2);
  transition: transform 0.2s ease-out, box-shadow 0.2s ease-out;
}
.card h2 { margin: 0 0 .3rem; }
.card p { margin: 0; }

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 24px rgb(0 0 0 / 0.25);
}

@media (prefers-reduced-motion: reduce) {
  .card { transition: none; }
}
""", HOVER_HTML),
    checks=[
        C("The .card rule transitions transform and box-shadow", "(r => !!r && r.style.transitionProperty.includes('transform') && r.style.transitionProperty.includes('box-shadow'))(" + RULES + ".find(r => r.selectorText === '.card'))"),
        C("The transition does not use 'all'", "(r => !!r && !r.style.transitionProperty.split(',').map(s => s.trim()).includes('all'))(" + RULES + ".find(r => r.selectorText === '.card'))"),
        C("Each transition lasts 0.2s", "(r => !!r && r.style.transitionDuration !== '' && r.style.transitionDuration.split(',').every(d => Math.abs(parseFloat(d) * (d.trim().endsWith('ms') ? 0.001 : 1) - 0.2) < 0.001))(" + RULES + ".find(r => r.selectorText === '.card'))"),
        C("At rest the card has no transform", "(r => !!r && !r.style.transform && !r.style.translate)(" + RULES + ".find(r => r.selectorText === '.card'))"),
        C("A .card:hover rule sets transform and box-shadow", RULES + ".some(r => r.selectorText && r.selectorText.includes('.card:hover') && !!(r.style.transform || r.style.translate) && !!r.style.boxShadow)"),
        C("A prefers-reduced-motion block removes the transition on .card", RULES + ".some(r => r instanceof CSSMediaRule && r.conditionText.includes('prefers-reduced-motion') && [...r.cssRules].some(x => x.selectorText && x.selectorText.includes('.card') && (x.style.transitionProperty === 'none' || x.style.transitionDuration === '0s')))"),
    ],
    guide=dict(
        prereqs="`transition`, `transform`, `:hover`, and the `prefers-reduced-motion` media query. See *Transitions, transforms and animations*.",
        intuition="A transition belongs on the element's resting rule: it says \"whenever these properties change, take this long\". The hover rule only states the new values. Naming `transform` and `box-shadow` (instead of `all`) keeps the browser from animating things you did not intend, and `transform` moves the card without disturbing the layout around it.",
        hints=[
            "In `.card`, add `transition: transform 0.2s, box-shadow 0.2s;`.",
            "Write a separate rule `.card:hover { transform: translateY(-4px); box-shadow: ...; }` with a larger, softer shadow.",
            "Wrap an override in `@media (prefers-reduced-motion: reduce) { .card { transition: none; } }`.",
        ],
        approach="1. Base rule: the comma-separated transition for the two properties.\n2. Hover rule: a negative `translateY` and a deeper shadow.\n3. Media query: `transition: none` for people who asked for reduced motion. The card still changes on hover, but instantly.",
        pitfalls="- Putting `transition` inside `:hover`: the lift animates but the return snaps.\n- `transition: all 0.2s`: slower and unpredictable.\n- Moving the card with `margin-top` or `top`: that triggers layout on every frame and shifts neighbours.\n- Forgetting keyboard users: add `:focus-within` or make the card's link show the same effect on focus.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-css-animation", title="Keyframe animations: a pulse and a spinner", difficulty="Medium", pattern="Motion", kind="web",
    description=r"""
Create two looping animations with `@keyframes`.

Requirements:

- An `@keyframes` rule named **`pulse`** with at least two keyframes that change `transform` (or `scale`) and/or `opacity`.
- `.dot` runs `pulse`: its computed `animation-name` is `pulse`, the duration is **1.5s**, the timing function is `ease-in-out`, and it repeats **infinitely**.
- An `@keyframes` rule named **`spin`** that rotates through a full turn.
- `.spinner` runs `spin`: duration **1s**, timing function **`linear`**, repeating **infinitely**.
""",
    starter=page("Animations", """
body { font-family: system-ui, sans-serif; padding: 40px; display: flex; gap: 40px; align-items: center; }
.dot { width: 24px; height: 24px; border-radius: 50%; background: #d32f2f; }
.spinner { width: 40px; height: 40px; border-radius: 50%; border: 5px solid #cfd8dc; border-top-color: #1565c0; }

/* your code */
""", ANIM_HTML),
    solution=page("Animations", """
body { font-family: system-ui, sans-serif; padding: 40px; display: flex; gap: 40px; align-items: center; }
.dot { width: 24px; height: 24px; border-radius: 50%; background: #d32f2f; }
.spinner { width: 40px; height: 40px; border-radius: 50%; border: 5px solid #cfd8dc; border-top-color: #1565c0; }

@keyframes pulse {
  from { transform: scale(1); opacity: 1; }
  50%  { transform: scale(1.4); opacity: 0.6; }
  to   { transform: scale(1); opacity: 1; }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.dot {
  animation: pulse 1.5s ease-in-out infinite;
}
.spinner {
  animation: spin 1s linear infinite;
}
""", ANIM_HTML),
    checks=[
        C("@keyframes pulse exists with at least two keyframes changing transform, scale or opacity", "(k => !!k && k.cssRules.length >= 2 && [...k.cssRules].some(f => !!(f.style.transform || f.style.scale || f.style.opacity)))(" + RULES + ".find(r => r instanceof CSSKeyframesRule && r.name === 'pulse'))"),
        C(".dot runs the pulse animation", "getComputedStyle(document.querySelector('.dot')).animationName === 'pulse'"),
        C(".dot: 1.5s, ease-in-out, infinite", "(c => c.animationDuration === '1.5s' && c.animationTimingFunction === 'ease-in-out' && c.animationIterationCount === 'infinite')(getComputedStyle(document.querySelector('.dot')))"),
        C("@keyframes spin exists and rotates", "(k => !!k && [...k.cssRules].some(f => /rotate|turn/.test(f.style.transform + ' ' + f.style.rotate)))(" + RULES + ".find(r => r instanceof CSSKeyframesRule && r.name === 'spin'))"),
        C(".spinner runs the spin animation", "getComputedStyle(document.querySelector('.spinner')).animationName === 'spin'"),
        C(".spinner: 1s, linear, infinite", "(c => c.animationDuration === '1s' && c.animationTimingFunction === 'linear' && c.animationIterationCount === 'infinite')(getComputedStyle(document.querySelector('.spinner')))"),
    ],
    guide=dict(
        prereqs="`@keyframes`, the `animation` shorthand and its parts, `transform`. See *Transitions, transforms and animations*.",
        intuition="An animation has two halves. `@keyframes name { ... }` is the script: a list of snapshots at percentages of the timeline. The `animation` property on an element is the performance: which script, how long, with what easing, how many times. A spinner uses `linear` so its speed never changes and the loop has no visible seam; a pulse uses `ease-in-out` so it swells and settles softly.",
        hints=[
            "Define the scripts first: `@keyframes pulse { ... }` with `from`, `50%` and `to` blocks, and `@keyframes spin { to { transform: rotate(360deg); } }`.",
            "Attach them with the shorthand: name, duration, timing function, iteration count.",
            "`.dot { animation: pulse 1.5s ease-in-out infinite; }` and `.spinner { animation: spin 1s linear infinite; }`.",
        ],
        approach="1. `@keyframes pulse`: scale 1, then about 1.4 at 50%, then back to 1 (optionally with opacity).\n2. `@keyframes spin`: only a `to` keyframe rotating 360 degrees; the start is taken from the element's current, unrotated state.\n3. Apply each with the `animation` shorthand.\n4. In production, wrap decorative motion in a `prefers-reduced-motion` query and give anything that loops for more than five seconds a way to pause.",
        pitfalls="- A name in `animation` that does not match the `@keyframes` name exactly (names are case-sensitive): nothing moves.\n- Omitting the duration: the default is `0s`, so the animation is invisible.\n- `ease` on a spinner: it visibly speeds up and slows down on each turn.\n- Animating `width` or `margin` for a pulse: use `transform: scale()` so that no layout work is triggered.",
    ),
),
]
