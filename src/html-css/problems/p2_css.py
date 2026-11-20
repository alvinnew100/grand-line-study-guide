"""CSS-focused web problems: cascade, selectors, typography, box model, component styling, architecture."""


def page(title, css, body):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>' + title + "</title>\n<style>\n"
            + css.strip("\n") + "\n</style>\n</head>\n<body>\n" + body.strip("\n") + "\n</body>\n</html>\n")


def C(name, test):
    return {"name": name, "test": test}


RULES = "[...document.styleSheets].flatMap(s => [...s.cssRules])"

TOOLBAR_HTML = """
<div id="toolbar" class="toolbar">
  <button class="btn" type="button">Cancel</button>
  <button class="btn btn--primary" type="button">Save</button>
</div>
"""

PSEUDO_HTML = """
<p class="quote">The sea, once it casts its spell, holds one in its net of wonder.</p>
<p>Read the <a class="external" href="https://example.org/tides">tide tables</a> before you sail.</p>
<ul>
  <li>Life jacket</li>
  <li>Chart</li>
  <li>Flask of tea</li>
</ul>
<label class="required" for="boat">Boat name</label>
<input id="boat" name="boat" required>
"""

ZEBRA_HTML = """
<table>
  <caption>Harbour arrivals</caption>
  <thead><tr><th scope="col">Vessel</th><th scope="col">From</th><th scope="col">Due</th></tr></thead>
  <tbody>
    <tr><th scope="row">Kittiwake</th><td>Oban</td><td>09:10</td></tr>
    <tr><th scope="row">Fulmar</th><td>Mallaig</td><td>10:45</td></tr>
    <tr><th scope="row">Gannet</th><td>Ullapool</td><td>12:30</td></tr>
    <tr><th scope="row">Petrel</th><td>Stornoway</td><td>14:05</td></tr>
    <tr><th scope="row">Shearwater</th><td>Lerwick</td><td>17:20</td></tr>
  </tbody>
</table>
"""

TYPE_HTML = """
<article class="prose">
  <h1>Keeping a tide diary</h1>
  <p>Write down the height and time of each high water for a month and a pattern appears. The range swells toward the full and new moon and shrinks in between.</p>
  <h2>What to record</h2>
  <p>Note the time, the height against a fixed mark, and the weather.</p>
  <h3>Choosing a mark</h3>
  <p>A painted line on a harbour wall works well. <small>Ask the harbour master first.</small></p>
</article>
"""

CARD_HTML = """
<div class="card">
  <h2>Day ticket</h2>
  <p>Unlimited ferry crossings until midnight.</p>
</div>
"""

BUTTON_HTML = """
<button class="btn" type="button">Book now</button>
<button class="btn" type="button" disabled>Sold out</button>
"""

PRICING_HTML = """
<h1>Mooring plans</h1>
<section class="pricing">
  <article class="plan">
    <h3>Visitor</h3>
    <p class="price">12 per night</p>
    <ul><li>One berth</li><li>Water</li><li>Showers</li></ul>
    <a class="cta" href="#visitor">Choose Visitor</a>
  </article>
  <article class="plan plan--featured">
    <h3>Season</h3>
    <p class="price">900 per year</p>
    <ul><li>Reserved berth</li><li>Water</li><li>Showers</li><li>Electricity</li><li>Winter storage</li></ul>
    <a class="cta" href="#season">Choose Season</a>
  </article>
  <article class="plan">
    <h3>Club</h3>
    <p class="price">400 per year</p>
    <ul><li>Shared berth</li><li>Water</li><li>Showers</li><li>Electricity</li></ul>
    <a class="cta" href="#club">Choose Club</a>
  </article>
</section>
"""

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="web-specificity-fix", title="Fix a specificity conflict", difficulty="Medium", pattern="Cascade", kind="web",
    description=r"""
The **Save** button should be white text on teal, but it shows up grey like the Cancel button. A selector written with an id is overriding the modifier class.

Fix the **CSS only** (leave the HTML as it is).

Requirements:

- The `.btn--primary` button has `color` white (`rgb(255, 255, 255)`) and `background-color` `rgb(0, 105, 92)`.
- The plain `.btn` button keeps `background-color` `rgb(236, 239, 241)` and `color` `rgb(38, 50, 56)`.
- No declaration uses `!important`.
- No selector contains an id (`#`).
- No inline `style` attributes are added.
""",
    starter=page("Toolbar", """
body { font-family: system-ui, sans-serif; }
.toolbar { display: flex; gap: .5rem; }

#toolbar .btn {
  background-color: rgb(236, 239, 241);
  color: rgb(38, 50, 56);
  border: 0;
  border-radius: 8px;
  padding: .5rem 1rem;
  font: inherit;
}

.btn--primary {
  background-color: rgb(0, 105, 92);
  color: rgb(255, 255, 255);
}
""", TOOLBAR_HTML),
    solution=page("Toolbar", """
body { font-family: system-ui, sans-serif; }
.toolbar { display: flex; gap: .5rem; }

.btn {
  background-color: rgb(236, 239, 241);
  color: rgb(38, 50, 56);
  border: 0;
  border-radius: 8px;
  padding: .5rem 1rem;
  font: inherit;
}

.btn--primary {
  background-color: rgb(0, 105, 92);
  color: rgb(255, 255, 255);
}
""", TOOLBAR_HTML),
    checks=[
        C("Save has white text", "getComputedStyle(document.querySelector('.btn--primary')).color === 'rgb(255, 255, 255)'"),
        C("Save has the teal background", "getComputedStyle(document.querySelector('.btn--primary')).backgroundColor === 'rgb(0, 105, 92)'"),
        C("Cancel keeps its grey background and dark text", "(c => c.backgroundColor === 'rgb(236, 239, 241)' && c.color === 'rgb(38, 50, 56)')(getComputedStyle(document.querySelector('.btn:not(.btn--primary)')))"),
        C("No declaration uses !important", "!" + RULES + ".some(r => r.style && [...r.style].some(p => r.style.getPropertyPriority(p) === 'important'))"),
        C("No selector contains an id", "!" + RULES + ".some(r => r.selectorText && r.selectorText.includes('#'))"),
        C("No inline styles were added", "!document.querySelector('[style]')"),
    ],
    guide=dict(
        prereqs="Specificity as three columns (ids, classes, elements) and source order. See *The cascade, specificity and inheritance*.",
        intuition="`#toolbar .btn` scores (1,1,0). `.btn--primary` scores (0,1,0). The id column is compared first, so the grey rule wins no matter where it appears in the file. Raising the modifier's specificity or adding `!important` would work, but each of those makes the next override harder. The durable fix is to *lower* the selector that is too strong.",
        hints=[
            "Work out the specificity of both selectors that set `background-color` on the Save button.",
            "The base button style does not need to know which toolbar it is in. What is the simplest selector that still matches every button?",
            "Change `#toolbar .btn` to `.btn`. Both rules are now (0,1,0), and the modifier wins because it comes later in the file.",
        ],
        approach="1. Open developer tools on the Save button: the `.btn--primary` declarations are struck through, beaten by `#toolbar .btn`.\n2. Replace the selector `#toolbar .btn` with `.btn`.\n3. Keep `.btn--primary` after `.btn` so that source order breaks the tie in its favour.",
        pitfalls="- Adding `!important` to the modifier: it works today and causes the next conflict tomorrow.\n- Writing `#toolbar .btn--primary`: it wins, but ties the button to one container.\n- Moving `.btn--primary` above `.btn` after the fix, which would make the base rule win the tie.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-pseudo-elements", title="Decorate with pseudo-elements", difficulty="Medium", pattern="Selectors", kind="web",
    description=r"""
Add four decorations **using CSS only**. The HTML must stay exactly as given.

Requirements:

- `.quote::before` inserts an opening curly quotation mark (the character U+201C; in CSS you can write `content: "\201C"`).
- `a.external::after` inserts a north-east arrow after the link text (the character U+2197, `content: " \2197"`).
- `.required::after` inserts an asterisk `*` coloured `rgb(198, 40, 40)`.
- List markers are coloured `rgb(0, 105, 92)` with the `::marker` pseudo-element.
- None of these characters may be typed into the HTML.
""",
    starter=page("Pseudo-elements", """
body { font-family: Georgia, serif; max-width: 30rem; }
label { font-family: system-ui, sans-serif; display: block; margin-top: 1rem; }

/* your code */
""", PSEUDO_HTML),
    solution=page("Pseudo-elements", """
body { font-family: Georgia, serif; max-width: 30rem; }
label { font-family: system-ui, sans-serif; display: block; margin-top: 1rem; }

.quote::before {
  content: "\\201C";
  color: rgb(0, 105, 92);
  font-size: 1.6em;
}
a.external::after {
  content: " \\2197";
}
.required::after {
  content: " *";
  color: rgb(198, 40, 40);
}
li::marker {
  color: rgb(0, 105, 92);
}
""", PSEUDO_HTML),
    checks=[
        C(".quote::before inserts an opening curly quote", "getComputedStyle(document.querySelector('.quote'), '::before').content.includes('\\u201c')"),
        C("a.external::after inserts an arrow", "getComputedStyle(document.querySelector('a.external'), '::after').content.includes('\\u2197')"),
        C(".required::after inserts an asterisk", "getComputedStyle(document.querySelector('.required'), '::after').content.includes('*')"),
        C("The asterisk is red", "getComputedStyle(document.querySelector('.required'), '::after').color === 'rgb(198, 40, 40)'"),
        C("List markers are teal", "getComputedStyle(document.querySelector('li'), '::marker').color === 'rgb(0, 105, 92)'"),
        C("The characters are not typed into the HTML", "!document.body.textContent.includes('\\u201c') && !document.body.textContent.includes('\\u2197') && !document.querySelector('.required').textContent.includes('*')"),
    ],
    guide=dict(
        prereqs="Pseudo-elements `::before`, `::after`, `::marker` and the `content` property. See *Introducing CSS*.",
        intuition="`::before` and `::after` create an extra box inside an element, as its first or last child, without touching the HTML. The box only exists if you give it `content`. That makes them ideal for decoration that should follow a class around: mark a link `external` and the arrow appears.",
        hints=[
            "Every `::before` or `::after` rule needs a `content` declaration, or nothing is generated.",
            "Characters outside the keyboard can be written as a backslash and their code: `content: \"\\201C\"` for the opening quote and `\"\\2197\"` for the arrow.",
            "Colour the asterisk inside the `.required::after` rule itself, and use `li::marker { color: ... }` for the bullets.",
        ],
        approach="1. `.quote::before { content: \"\\201C\"; }`\n2. `a.external::after { content: \" \\2197\"; }` (the leading space separates it from the text).\n3. `.required::after { content: \" *\"; color: rgb(198, 40, 40); }`\n4. `li::marker { color: rgb(0, 105, 92); }`",
        pitfalls="- Forgetting `content`: the pseudo-element does not render.\n- Typing the characters into the HTML instead: the decoration would then have to be repeated by hand everywhere.\n- Expecting `::marker` to accept any property; it supports only a few, such as `color` and the font properties.\n- Putting essential information only in generated content: the `required` attribute on the input is what actually tells assistive technology the field is mandatory.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-zebra-table", title="Zebra-striped table rows", difficulty="Easy", pattern="Selectors", kind="web",
    description=r"""
Style the arrivals table **without adding any classes or attributes to the rows**.

Requirements:

- Every **even** row of the `<tbody>` (2nd, 4th, ...) has `background-color` `rgb(236, 239, 241)`, set on the `<tr>` with an `:nth-child` selector. Odd rows keep a transparent background.
- The header cells in `<thead>` have `background-color` `rgb(38, 50, 56)` and white text.
- A rule with `tr:hover` in its selector changes the row's `background-color`.
- The table's borders are collapsed.
""",
    starter=page("Arrivals", """
body { font-family: system-ui, sans-serif; }
table { min-width: 24rem; }
th, td { padding: .5rem .9rem; text-align: left; }

/* your code */
""", ZEBRA_HTML),
    solution=page("Arrivals", """
body { font-family: system-ui, sans-serif; }
table { min-width: 24rem; border-collapse: collapse; }
th, td { padding: .5rem .9rem; text-align: left; }

thead th { background-color: rgb(38, 50, 56); color: rgb(255, 255, 255); }
tbody tr:nth-child(even) { background-color: rgb(236, 239, 241); }
tbody tr:hover { background-color: rgb(178, 223, 219); }
""", ZEBRA_HTML),
    checks=[
        C("Even body rows are grey and odd rows are transparent", "(rows => rows.length === 5 && rows.every((r, i) => (getComputedStyle(r).backgroundColor === 'rgb(236, 239, 241)') === (i % 2 === 1)))([...document.querySelectorAll('tbody tr')])"),
        C("A selector uses :nth-child", RULES + ".some(r => r.selectorText && r.selectorText.includes(':nth-child') && !!r.style.backgroundColor)"),
        C("Header cells are dark with white text", "[...document.querySelectorAll('thead th')].every(h => getComputedStyle(h).backgroundColor === 'rgb(38, 50, 56)' && getComputedStyle(h).color === 'rgb(255, 255, 255)')"),
        C("A tr:hover rule sets a background colour", RULES + ".some(r => r.selectorText && r.selectorText.includes('tr:hover') && !!r.style.backgroundColor)"),
        C("Borders are collapsed", "getComputedStyle(document.querySelector('table')).borderCollapse === 'collapse'"),
        C("No classes or inline styles were added to rows or cells", "!document.querySelector('tbody tr[class], tbody tr[style], tbody td[class], tbody td[style], tbody th[class], tbody th[style]')"),
    ],
    guide=dict(
        prereqs="The `:nth-child()` pseudo-class, `:hover`, and `border-collapse`. See *Introducing CSS* and *Styling lists, tables and forms*.",
        intuition="`:nth-child(even)` selects an element by its position among its siblings, so the stripes are worked out by the browser. Add or remove a row and the pattern repairs itself, which would not happen with hand-written classes.",
        hints=[
            "Scope the stripes to the body with `tbody tr`, so the header row is not counted.",
            "`tbody tr:nth-child(even)` matches rows 2 and 4. Set the background on the row, not on the cells.",
            "Write the hover rule **after** the stripe rule. Both have the same specificity, so the later one wins when a striped row is hovered.",
        ],
        approach="1. `table { border-collapse: collapse; }`\n2. `thead th { background-color: rgb(38, 50, 56); color: white; }`\n3. `tbody tr:nth-child(even) { background-color: rgb(236, 239, 241); }`\n4. `tbody tr:hover { background-color: ...; }` placed last.",
        pitfalls="- Writing `tr:nth-child(even)` without `tbody`: the header row is in a different parent, so the count restarts there, but it also stripes rows you may not intend in `tfoot`.\n- Putting the hover rule first, so stripes override it.\n- Without collapsed borders, small gaps between cells show the table background through the stripes.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-typography-rem", title="A type scale in rem", difficulty="Medium", pattern="Typography", kind="web",
    description=r"""
Give the article a consistent type scale. All font sizes must be written in **`rem`** so they respect the reader's browser setting.

Requirements (the root font size stays at the default 16px):

- `h1` is `2.5rem` (40px), `h2` is `2rem` (32px), `h3` is `1.5rem` (24px), `small` is `0.875rem` (14px).
- Every `font-size` declaration in the style sheet uses the `rem` unit (at least four declarations).
- `body` has a **unitless** `line-height: 1.5` (so paragraphs get 24px lines).
- Headings `h1`, `h2`, `h3` have `line-height: 1.2` (so the `h1` gets 48px lines).
- `.prose` has a `max-width` written in the `ch` unit, giving a comfortable line length (between 45ch and 80ch).
""",
    starter=page("Tide diary", """
body { font-family: Georgia, serif; margin: 2rem; }
h1 { font-size: 40px; }
h2 { font-size: 30px; }

/* your code */
""", TYPE_HTML),
    solution=page("Tide diary", """
body { font-family: Georgia, serif; margin: 2rem; line-height: 1.5; }
.prose { max-width: 65ch; }
h1, h2, h3 { line-height: 1.2; }
h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }
small { font-size: 0.875rem; }
""", TYPE_HTML),
    checks=[
        C("The root font size is still 16px", "getComputedStyle(document.documentElement).fontSize === '16px'"),
        C("h1, h2 and h3 compute to 40px, 32px and 24px", "['h1', 'h2', 'h3'].map(s => getComputedStyle(document.querySelector(s)).fontSize).join() === '40px,32px,24px'"),
        C("small computes to 14px", "getComputedStyle(document.querySelector('small')).fontSize === '14px'"),
        C("Every font-size declaration uses rem (at least four)", "(f => f.length >= 4 && f.every(r => r.style.fontSize.endsWith('rem')))(" + RULES + ".filter(r => r.style && r.style.fontSize))"),
        C("body has a unitless line-height of 1.5", RULES + ".some(r => r.selectorText && r.selectorText.split(',').map(s => s.trim()).includes('body') && r.style.lineHeight === '1.5')"),
        C("Paragraph lines are 24px and h1 lines are 48px", "getComputedStyle(document.querySelector('p')).lineHeight === '24px' && getComputedStyle(document.querySelector('h1')).lineHeight === '48px'"),
        C(".prose has a max-width between 45ch and 80ch", "(m => m.endsWith('ch') && parseFloat(m) >= 45 && parseFloat(m) <= 80)(" + RULES + ".filter(r => r.selectorText && r.selectorText.includes('.prose') && r.style.maxWidth).map(r => r.style.maxWidth).pop() || '')"),
    ],
    guide=dict(
        prereqs="The `rem`, `em` and `ch` units, `line-height`, and inheritance. See *Typography: fonts, sizes, spacing and units*.",
        intuition="`1rem` equals the root font size, which is 16px unless the reader has chosen something else. Sizes written in `rem` therefore scale with that preference, while `px` sizes ignore it. A unitless `line-height` is inherited as a multiplier, so each element computes its own line spacing from its own font size.",
        hints=[
            "Divide the target pixel size by 16 to get the `rem` value: 40 / 16 = 2.5.",
            "Replace the two pixel sizes already in the starter, then add rules for `h3` and `small`.",
            "Put `line-height: 1.5` (no unit) on `body`, `line-height: 1.2` on the headings, and `max-width: 65ch` on `.prose`.",
        ],
        approach="1. `h1 { font-size: 2.5rem; }`, `h2 { font-size: 2rem; }`, `h3 { font-size: 1.5rem; }`, `small { font-size: 0.875rem; }`.\n2. `body { line-height: 1.5; }`: a paragraph at 16px gets 24px lines.\n3. `h1, h2, h3 { line-height: 1.2; }`: the 40px heading gets 48px lines.\n4. `.prose { max-width: 65ch; }`.",
        pitfalls="- Leaving a `px` font size in the sheet.\n- Writing `line-height: 1.5em` or `24px`: the *computed length* would be inherited, and large headings would overlap.\n- Changing `html { font-size }` to make the arithmetic easier; it breaks the 16px assumption used by everything else.\n- Using `em` for heading sizes: nested contexts would compound.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-card-box-model", title="A card and the box model", difficulty="Easy", pattern="Box model", kind="web",
    description=r"""
Style `.card` so that its size is predictable.

Requirements:

- `box-sizing` is `border-box`.
- The card's rendered width (border edge to border edge) is exactly **320px**.
- Padding is **24px** on every side.
- A **2px solid** border on every side.
- Corners are rounded with a **12px** radius.
- The card is centred horizontally in the page using automatic side margins.
""",
    starter=page("Card", """
body { font-family: system-ui, sans-serif; margin: 0; padding: 24px 0; background: #eceff1; }
.card {
  background: white;
  width: 320px;
  padding: 24px;
  /* your code */
}
.card h2 { margin-top: 0; }
""", CARD_HTML),
    solution=page("Card", """
body { font-family: system-ui, sans-serif; margin: 0; padding: 24px 0; background: #eceff1; }
.card {
  background: white;
  box-sizing: border-box;
  width: 320px;
  padding: 24px;
  border: 2px solid #90a4ae;
  border-radius: 12px;
  margin: 0 auto;
}
.card h2 { margin-top: 0; }
""", CARD_HTML),
    checks=[
        C("box-sizing is border-box", "getComputedStyle(document.querySelector('.card')).boxSizing === 'border-box'"),
        C("The card is exactly 320px wide", "Math.round(document.querySelector('.card').getBoundingClientRect().width) === 320"),
        C("Padding is 24px on all sides", "(c => [c.paddingTop, c.paddingRight, c.paddingBottom, c.paddingLeft].every(p => p === '24px'))(getComputedStyle(document.querySelector('.card')))"),
        C("The border is 2px solid on all sides", "(c => ['Top', 'Right', 'Bottom', 'Left'].every(s => c['border' + s + 'Width'] === '2px' && c['border' + s + 'Style'] === 'solid'))(getComputedStyle(document.querySelector('.card')))"),
        C("Corners have a 12px radius", "getComputedStyle(document.querySelector('.card')).borderTopLeftRadius === '12px' && getComputedStyle(document.querySelector('.card')).borderBottomRightRadius === '12px'"),
        C("The card is centred horizontally", "(r => Math.abs((r.left + r.right) / 2 - document.documentElement.clientWidth / 2) < 1.5)(document.querySelector('.card').getBoundingClientRect())"),
    ],
    guide=dict(
        prereqs="Content, padding, border, margin and `box-sizing`. See *The box model*.",
        intuition="With the default `content-box`, `width: 320px` describes only the content, so 24px of padding and a 2px border on each side would make the visible card 372px wide. `border-box` makes the declared width include padding and border. Automatic left and right margins then share the remaining space equally, which centres the card.",
        hints=[
            "Add `box-sizing: border-box;` so the padding and border fit inside the 320px.",
            "A border needs a style to be visible: `border: 2px solid <colour>`.",
            "`margin: 0 auto;` centres a block that has a width. `border-radius: 12px;` rounds the corners.",
        ],
        approach="1. `box-sizing: border-box;`\n2. Keep `width: 320px; padding: 24px;`.\n3. `border: 2px solid #90a4ae;`\n4. `border-radius: 12px;`\n5. `margin: 0 auto;`\n6. Check the box diagram in developer tools: content 272, padding 24, border 2, total 320.",
        pitfalls="- Forgetting `box-sizing`: the card measures 372px.\n- `border: 2px #90a4ae` with no style draws nothing.\n- `margin: auto` centres only horizontally in normal flow, and only when the block has a width.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-button-states", title="Button with hover, focus and disabled states", difficulty="Medium", pattern="Component styling", kind="web",
    description=r"""
Design the `.btn` component with all of its interactive states.

Requirements:

- **Base:** `background-color` `rgb(21, 101, 192)`, white text, **no border** (`border-style: none` or width 0), `border-radius` 8px, `cursor: pointer`, and at least 8px of vertical padding.
- **Hover:** a rule whose selector contains `.btn:hover` sets a different `background-color`.
- **Keyboard focus:** a rule whose selector contains `.btn:focus-visible` sets a visible `outline` (a style other than `none`, at least 2px wide).
- **Disabled:** a disabled `.btn` has `cursor: not-allowed` and an `opacity` below 1.
- **Motion:** the base rule transitions `background-color` over a duration greater than 0.
""",
    starter=page("Button", """
body { font-family: system-ui, sans-serif; display: flex; gap: 1rem; padding: 1rem; }
.btn {
  font: inherit;
  /* your code */
}
""", BUTTON_HTML),
    solution=page("Button", """
body { font-family: system-ui, sans-serif; display: flex; gap: 1rem; padding: 1rem; }
.btn {
  font: inherit;
  font-weight: 600;
  background-color: rgb(21, 101, 192);
  color: white;
  border: 0;
  border-radius: 8px;
  padding: 10px 18px;
  cursor: pointer;
  transition: background-color 0.15s ease-out;
}
.btn:hover {
  background-color: rgb(13, 71, 161);
}
.btn:focus-visible {
  outline: 3px solid rgb(255, 179, 0);
  outline-offset: 2px;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
""", BUTTON_HTML),
    checks=[
        C("Base colours: blue background, white text", "(c => c.backgroundColor === 'rgb(21, 101, 192)' && c.color === 'rgb(255, 255, 255)')(getComputedStyle(document.querySelector('.btn:not(:disabled)')))"),
        C("No border, 8px radius, pointer cursor", "(c => (c.borderTopStyle === 'none' || c.borderTopWidth === '0px') && c.borderTopLeftRadius === '8px' && c.cursor === 'pointer')(getComputedStyle(document.querySelector('.btn:not(:disabled)')))"),
        C("At least 8px vertical padding", "parseFloat(getComputedStyle(document.querySelector('.btn')).paddingTop) >= 8 && parseFloat(getComputedStyle(document.querySelector('.btn')).paddingBottom) >= 8"),
        C("A .btn:hover rule changes the background colour", RULES + ".some(r => r.selectorText && r.selectorText.includes('.btn:hover') && !!r.style.backgroundColor && r.style.backgroundColor !== 'rgb(21, 101, 192)')"),
        C("A .btn:focus-visible rule sets a visible outline", RULES + ".some(r => r.selectorText && r.selectorText.includes('.btn:focus-visible') && !!r.style.outlineStyle && r.style.outlineStyle !== 'none' && parseFloat(r.style.outlineWidth) >= 2)"),
        C("The disabled button has not-allowed cursor and reduced opacity", "(c => c.cursor === 'not-allowed' && parseFloat(c.opacity) < 1)(getComputedStyle(document.querySelector('.btn:disabled')))"),
        C("The base rule transitions background-color", "(r => !!r && r.style.transitionProperty.includes('background-color') && parseFloat(r.style.transitionDuration) > 0)(" + RULES + ".find(r => r.selectorText === '.btn'))"),
    ],
    guide=dict(
        prereqs="Pseudo-classes `:hover`, `:focus-visible`, `:disabled`; `outline`; transitions. See *Styling lists, tables and forms* and *Transitions, transforms and animations*.",
        intuition="A button is a small state machine: resting, pointed at, focused by keyboard, pressed, unavailable. Each state needs its own visual cue so that every kind of user knows what is happening. Hover alone leaves out keyboard and touch users, which is why the focus ring matters as much as the hover colour.",
        hints=[
            "Write the base rule first: colours, `border: 0`, radius, padding, `cursor: pointer`.",
            "Add three more rules: `.btn:hover` (a darker background), `.btn:focus-visible` (an `outline` such as `3px solid` in a contrasting colour, plus `outline-offset`), `.btn:disabled` (`opacity` and `cursor: not-allowed`).",
            "Put `transition: background-color 0.15s;` on the base rule, not on `:hover`, so the change animates in both directions.",
        ],
        approach="1. Base: `background-color: rgb(21, 101, 192); color: white; border: 0; border-radius: 8px; padding: 10px 18px; cursor: pointer; transition: background-color .15s;`\n2. `.btn:hover { background-color: rgb(13, 71, 161); }`\n3. `.btn:focus-visible { outline: 3px solid rgb(255, 179, 0); outline-offset: 2px; }`\n4. `.btn:disabled { opacity: .5; cursor: not-allowed; }`",
        pitfalls="- `outline: none` with no replacement removes the only indicator keyboard users have.\n- Putting `transition` only on `:hover`, so the return snaps.\n- A hover rule that also restyles the disabled button; `.btn:hover:not(:disabled)` or ordering the disabled rule last avoids that.\n- Signalling the disabled state by colour alone: keep the `disabled` attribute so assistive technology knows too.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-pricing-table", title="Three-plan pricing layout", difficulty="Medium", pattern="Component styling", kind="web",
    description=r"""
Lay out the three mooring plans side by side. The HTML is complete; write the CSS.

Requirements (checked in the 1024px-wide frame):

- `.pricing` is a **grid** with three **equal-width** columns and a **24px** gap, so the three `.plan` cards sit in one row.
- Each `.plan` has a 2px solid border; the featured plan (`.plan--featured`) has border colour `rgb(0, 105, 92)`.
- The plans contain different numbers of list items, but the **call-to-action links (`.cta`) must all line up along the bottom** of the cards. (Make each plan a flex column and push the link down.)
- `.cta` is displayed as a block with a background colour, so the whole rectangle is clickable.
""",
    starter=page("Mooring plans", """
* { box-sizing: border-box; }
body { font-family: system-ui, sans-serif; margin: 0; padding: 24px; }
.plan { padding: 20px; border-radius: 12px; }
.plan ul { padding-left: 1.2rem; }
.price { font-size: 1.4rem; font-weight: 700; }

/* your code */
""", PRICING_HTML),
    solution=page("Mooring plans", """
* { box-sizing: border-box; }
body { font-family: system-ui, sans-serif; margin: 0; padding: 24px; }
.plan { padding: 20px; border-radius: 12px; }
.plan ul { padding-left: 1.2rem; }
.price { font-size: 1.4rem; font-weight: 700; }

.pricing {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.plan {
  display: flex;
  flex-direction: column;
  border: 2px solid rgb(207, 216, 220);
}
.plan--featured {
  border-color: rgb(0, 105, 92);
}
.cta {
  display: block;
  margin-top: auto;
  padding: 10px;
  text-align: center;
  background-color: rgb(0, 105, 92);
  color: white;
  border-radius: 8px;
  text-decoration: none;
}
""", PRICING_HTML),
    checks=[
        C(".pricing is a grid", "getComputedStyle(document.querySelector('.pricing')).display === 'grid'"),
        C("The three plans sit in one row, left to right", "(r => r.length === 3 && r.every(x => Math.abs(x.top - r[0].top) < 1) && r[0].left < r[1].left && r[1].left < r[2].left)([...document.querySelectorAll('.plan')].map(e => e.getBoundingClientRect()))"),
        C("The three columns are equally wide", "(r => r.length === 3 && Math.abs(r[0].width - r[1].width) < 1 && Math.abs(r[1].width - r[2].width) < 1 && r[0].width > 200)([...document.querySelectorAll('.plan')].map(e => e.getBoundingClientRect()))"),
        C("The gap between columns is 24px", "(r => Math.round(r[1].left - r[0].right) === 24 && Math.round(r[2].left - r[1].right) === 24)([...document.querySelectorAll('.plan')].map(e => e.getBoundingClientRect()))"),
        C("Each plan has a 2px solid border; the featured one is teal", "[...document.querySelectorAll('.plan')].every(p => getComputedStyle(p).borderTopWidth === '2px' && getComputedStyle(p).borderTopStyle === 'solid') && getComputedStyle(document.querySelector('.plan--featured')).borderTopColor === 'rgb(0, 105, 92)' && getComputedStyle(document.querySelector('.plan:not(.plan--featured)')).borderTopColor !== 'rgb(0, 105, 92)'"),
        C("The call-to-action links line up along the bottom", "(b => b.length === 3 && b.every(x => Math.abs(x - b[0]) < 1))([...document.querySelectorAll('.plan .cta')].map(e => e.getBoundingClientRect().bottom))"),
        C(".cta is a block with a background colour", "(c => c.display === 'block' && c.backgroundColor !== 'rgba(0, 0, 0, 0)')(getComputedStyle(document.querySelector('.cta')))"),
    ],
    guide=dict(
        prereqs="Grid columns with `repeat()` and `fr`, `gap`, flex columns and auto margins. See *CSS Grid in depth* and *Flexbox in depth*.",
        intuition="Two layout tools cooperate here. Grid handles the outside: three equal tracks, and because grid items stretch by default the cards are all as tall as the tallest. Flexbox handles the inside of each card: as a column, with `margin-top: auto` on the link, the spare height in the shorter cards is absorbed above the link, pinning it to the bottom.",
        hints=[
            "On `.pricing`: `display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;`.",
            "On `.plan`: `display: flex; flex-direction: column;` and a `2px solid` border. Override only `border-color` on `.plan--featured`.",
            "On `.cta`: `display: block; margin-top: auto;` plus a background and padding.",
        ],
        approach="1. Make `.pricing` a three-column grid with a 24px gap.\n2. Give `.plan` a border and turn it into a flex column.\n3. Set the featured border colour with the modifier class, written after `.plan`.\n4. Style `.cta` as a block-level button and add `margin-top: auto`.\n5. Verify that the three links share one baseline even though the lists have 3, 5 and 4 items.",
        pitfalls="- `align-items: start` on the grid would stop the cards stretching, and the links would no longer line up.\n- Using percentages (`33.33%`) with a gap overflows; `fr` accounts for the gap.\n- Writing `.plan--featured` before `.plan`, so the base border colour wins the tie.\n- Leaving `.cta` inline: its padding would not enlarge the clickable area properly and `margin-top: auto` would have no effect outside a flex container.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-bem-card", title="Refactor a card to BEM", difficulty="Medium", pattern="CSS architecture", kind="web",
    description=r"""
The product cards below are styled with ids, tag selectors and location-dependent chains. Refactor the HTML class names and the CSS to the **BEM** convention.

Requirements:

- Each card's root element has the class `product` (two cards).
- Inside each card there are elements with the classes `product__title`, `product__price` and `product__button`.
- The second card is a sale item: it has **both** `product` and `product--sale`.
- No element in a card has an `id`.
- In the CSS, every selector other than `body` starts with `.product` and contains no id.
- The normal price is `rgb(31, 35, 40)`; the price inside the sale card is `rgb(198, 40, 40)`.
""",
    starter=page("Products", """
body { font-family: system-ui, sans-serif; display: flex; gap: 16px; padding: 16px; }
#shop div.box { border: 1px solid #cfd8dc; border-radius: 10px; padding: 16px; width: 200px; }
#shop div.box h3 { margin: 0 0 8px; }
#shop div.box p { color: rgb(31, 35, 40); font-weight: 700; }
#shop div.box button { font: inherit; }
#sale-item p { color: rgb(198, 40, 40) !important; }
""", """
<div id="shop" style="display: contents">
  <div class="box">
    <h3>Rope, 10 m</h3>
    <p>14.00</p>
    <button type="button">Add</button>
  </div>
  <div class="box" id="sale-item">
    <h3>Fender</h3>
    <p>9.50</p>
    <button type="button">Add</button>
  </div>
</div>
"""),
    solution=page("Products", """
body { font-family: system-ui, sans-serif; display: flex; gap: 16px; padding: 16px; }
.product { border: 1px solid #cfd8dc; border-radius: 10px; padding: 16px; width: 200px; }
.product__title { margin: 0 0 8px; }
.product__price { color: rgb(31, 35, 40); font-weight: 700; }
.product__button { font: inherit; }
.product--sale .product__price { color: rgb(198, 40, 40); }
""", """
<article class="product">
  <h3 class="product__title">Rope, 10 m</h3>
  <p class="product__price">14.00</p>
  <button class="product__button" type="button">Add</button>
</article>
<article class="product product--sale">
  <h3 class="product__title">Fender</h3>
  <p class="product__price">9.50</p>
  <button class="product__button" type="button">Add</button>
</article>
"""),
    checks=[
        C("There are two .product blocks", "document.querySelectorAll('.product').length === 2"),
        C("Each block has title, price and button elements", "document.querySelectorAll('.product').length === 2 && [...document.querySelectorAll('.product')].every(p => !!p.querySelector('.product__title') && !!p.querySelector('.product__price') && !!p.querySelector('.product__button'))"),
        C("Exactly one block also has the product--sale modifier", "document.querySelectorAll('.product.product--sale').length === 1 && document.querySelectorAll('.product--sale').length === 1"),
        C("No card element has an id", "document.querySelectorAll('.product').length === 2 && !document.querySelector('.product[id], .product [id]')"),
        C("Every selector except body starts with .product and has no id", "(s => s.length >= 4 && s.every(x => !x.includes('#') && (x === 'body' || x.startsWith('.product'))))(" + RULES + ".filter(r => r.selectorText).flatMap(r => r.selectorText.split(',').map(x => x.trim())))"),
        C("No declaration uses !important", "!" + RULES + ".some(r => r.style && [...r.style].some(p => r.style.getPropertyPriority(p) === 'important'))"),
        C("Normal price is dark, sale price is red", "(n => !!n && getComputedStyle(n).color === 'rgb(31, 35, 40)')(document.querySelector('.product:not(.product--sale) .product__price')) && (s => !!s && getComputedStyle(s).color === 'rgb(198, 40, 40)')(document.querySelector('.product--sale .product__price'))"),
    ],
    guide=dict(
        prereqs="BEM naming (`block`, `block__element`, `block--modifier`) and flat specificity. See *CSS architecture: BEM, utilities, modules and layers*.",
        intuition="The starter's selectors describe *where* things are (`#shop div.box p`), so they break when the markup moves and need `!important` to override. BEM names describe *what* things are. Every part gets one unique class, every selector has the same low specificity, and a variant is a modifier class added next to the block class.",
        hints=[
            "Name the block `product`. Its parts become `product__title`, `product__price` and `product__button`: put those classes on the `h3`, `p` and `button`.",
            "Replace `id=\"sale-item\"` with the modifier: `class=\"product product--sale\"`. Remove the `#shop` wrapper or at least its id.",
            "Rewrite each rule with a single class selector. The sale colour is the one place a two-class selector is normal: `.product--sale .product__price`. It needs no `!important` because (0,2,0) beats (0,1,0).",
        ],
        approach="1. HTML: add the block, element and modifier classes; delete the ids and the inline style wrapper.\n2. CSS: `.product { ... }`, `.product__title { ... }`, `.product__price { ... }`, `.product__button { ... }`.\n3. Variant: `.product--sale .product__price { color: rgb(198, 40, 40); }`.\n4. Delete `!important`.",
        pitfalls="- Using the modifier alone (`class=\"product--sale\"`): the card loses all its base styles.\n- Nesting element names (`product__body__title`): BEM elements are named after the block only.\n- Keeping a tag in the selector (`h3.product__title`), which raises specificity for no benefit.",
    ),
),
]
