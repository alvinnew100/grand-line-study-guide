"""HTML-focused web problems: structure, text, links, images, tables, forms, semantics, accessibility, metadata."""


def page(title, css, body, head_extra=""):
    style = ("<style>\n" + css.strip("\n") + "\n</style>\n") if css.strip() else ""
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>' + title + "</title>\n"
            + head_extra + style + "</head>\n<body>\n" + body.strip("\n") + "\n</body>\n</html>\n")


def C(name, test):
    return {"name": name, "test": test}


RULES = "[...document.styleSheets].flatMap(s => [...s.cssRules])"
PIC = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 180'%3E%3Crect width='320' height='180' fill='%2390caf9'/%3E"
       "%3Ccircle cx='250' cy='50' r='26' fill='%23fff59d'/%3E%3Cpath d='M0 180 90 70 150 130 200 95 320 180Z' fill='%232e7d32'/%3E%3C/svg%3E")
LINE = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 10'%3E%3Cpath d='M0 5h200' stroke='%23999' stroke-width='2' "
        "stroke-dasharray='6 6'/%3E%3C/svg%3E")

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="web-headings-lists", title="Headings and lists for a recipe", difficulty="Easy", pattern="HTML structure", kind="web",
    description=r"""
A recipe page has been typed as plain paragraphs with bold text and line breaks. Rewrite the **body** so the structure is expressed with real HTML elements.

Requirements:

- Exactly **one** `<h1>` (the recipe name), and it must come before any `<h2>`.
- At least **two** `<h2>` headings ("Ingredients" and "Method").
- The ingredients are an **unordered list** with at least three items.
- The method is an **ordered list** with exactly four steps (do not type the numbers yourself).
- No `<br>` elements and no `<b>` elements remain.
""",
    starter=page("Flatbread", "body { font-family: system-ui, sans-serif; max-width: 34rem; }", """
<p><b>Quick flatbread</b></p>
<p><b>Ingredients</b><br>
- 250 g plain flour<br>
- 150 g yoghurt<br>
- a pinch of salt</p>
<p><b>Method</b><br>
1. Mix everything into a dough.<br>
2. Divide into four balls.<br>
3. Roll each ball flat.<br>
4. Cook in a dry pan for two minutes per side.</p>
"""),
    solution=page("Flatbread", "body { font-family: system-ui, sans-serif; max-width: 34rem; }", """
<h1>Quick flatbread</h1>
<h2>Ingredients</h2>
<ul>
  <li>250 g plain flour</li>
  <li>150 g yoghurt</li>
  <li>a pinch of salt</li>
</ul>
<h2>Method</h2>
<ol>
  <li>Mix everything into a dough.</li>
  <li>Divide into four balls.</li>
  <li>Roll each ball flat.</li>
  <li>Cook in a dry pan for two minutes per side.</li>
</ol>
"""),
    checks=[
        C("There is exactly one h1", "document.querySelectorAll('h1').length === 1"),
        C("There are at least two h2 headings", "document.querySelectorAll('h2').length >= 2"),
        C("The h1 comes before the first h2", "(a => a[0] && a[1] && !!(a[0].compareDocumentPosition(a[1]) & 4))([document.querySelector('h1'), document.querySelector('h2')])"),
        C("Ingredients are a ul with at least three li", "document.querySelectorAll('ul > li').length >= 3"),
        C("The method is an ol with exactly four li", "document.querySelectorAll('ol > li').length === 4"),
        C("Step numbers are not typed by hand", "[...document.querySelectorAll('ol > li')].every(li => !/^\\s*\\d/.test(li.textContent))"),
        C("No br or b elements remain", "document.querySelectorAll('br, b').length === 0"),
    ],
    guide=dict(
        prereqs="Headings `h1`-`h6`, `ul`, `ol` and `li`. See the lessons *Marking up text* and *Lists and links*.",
        intuition="Bold text and line breaks only *look* like headings and lists. A screen reader, a search engine or a style sheet cannot tell that `- 250 g flour` is a list item. Real elements carry that meaning: a heading joins the page outline, and a list reports how many items it has.",
        hints=[
            "Start with the title: which heading level names the whole page?",
            "Each bold label (\"Ingredients\", \"Method\") introduces a section of the page, so it is a second-level heading, not a paragraph.",
            "Replace each `- item<br>` line with `<li>item</li>` inside a `<ul>`. For the steps use `<ol>` and delete the typed `1.`, `2.` prefixes: the browser numbers them.",
        ],
        approach="1. Change the first paragraph to `<h1>Quick flatbread</h1>`.\n2. Turn each bold label into an `<h2>`.\n3. Wrap the three ingredients in `<ul>`, one `<li>` each, and remove the dashes.\n4. Wrap the four steps in `<ol>`, one `<li>` each, and remove the numbers.\n5. Delete every `<br>` and `<b>`: the block elements already start on new lines.",
        pitfalls="- Leaving `1.` inside the `<li>` produces \"1. 1. Mix...\".\n- Putting text or a `<p>` directly inside `<ul>`: only `<li>` may be a child of a list.\n- Choosing `<h3>` for the section labels because it looks smaller. Level expresses structure; size is a CSS matter.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-links-images", title="Links and images with alt text", difficulty="Easy", pattern="HTML structure", kind="web",
    description=r"""
Finish the markup of a small walking-club page.

Requirements:

- A `<nav>` containing exactly **three** links, each with an `href`.
- One of the nav links jumps within the page: its `href` is `#contact`, and an element with `id="contact"` exists.
- An **external** link whose `href` starts with `https://` opens in a new tab (`target="_blank"`) and has `rel="noopener"`.
- The photo (`<img class="photo">`) has meaningful `alt` text of at least five characters, plus `width` and `height` attributes.
- The decorative divider (`<img class="divider">`) has an **empty** `alt` attribute (present, but `""`).
""",
    starter=page("Hill Walkers", "body { font-family: system-ui, sans-serif; max-width: 36rem; } img { max-width: 100%; height: auto; }", """
<nav>
  <a>Home</a>
  <a>Walks</a>
</nav>
<h1>Hill Walkers</h1>
<img class="photo" src="%s">
<p>We follow the route notes published by <a href="https://example.org/routes">the national trail office</a>.</p>
<img class="divider" src="%s">
<h2>Contact</h2>
<p>Email the secretary to join a walk.</p>
""" % (PIC, LINE)),
    solution=page("Hill Walkers", "body { font-family: system-ui, sans-serif; max-width: 36rem; } img { max-width: 100%; height: auto; }", """
<nav>
  <a href="index.html">Home</a>
  <a href="walks.html">Walks</a>
  <a href="#contact">Contact</a>
</nav>
<h1>Hill Walkers</h1>
<img class="photo" src="%s" alt="Green hills under a pale sun" width="320" height="180">
<p>We follow the route notes published by <a href="https://example.org/routes" target="_blank" rel="noopener">the national trail office (opens in a new tab)</a>.</p>
<img class="divider" src="%s" alt="">
<h2 id="contact">Contact</h2>
<p>Email the secretary to join a walk.</p>
""" % (PIC, LINE)),
    checks=[
        C("The nav holds exactly three links with href", "document.querySelectorAll('nav a[href]').length === 3 && document.querySelectorAll('nav a').length === 3"),
        C("A link points to #contact and that id exists", "!!document.querySelector('nav a[href=\"#contact\"]') && !!document.getElementById('contact')"),
        C("The external link opens in a new tab with rel=noopener", "(a => !!a && a.target === '_blank' && a.relList.contains('noopener'))(document.querySelector('a[href^=\"https://\"]'))"),
        C("The photo has descriptive alt text", "(i => !!i && i.alt.trim().length >= 5)(document.querySelector('img.photo'))"),
        C("The photo has width and height attributes", "(i => !!i && i.hasAttribute('width') && i.hasAttribute('height'))(document.querySelector('img.photo'))"),
        C("The divider has an empty alt attribute", "(i => !!i && i.hasAttribute('alt') && i.getAttribute('alt') === '')(document.querySelector('img.divider'))"),
    ],
    guide=dict(
        prereqs="The `<a>` element, relative and fragment URLs, `<img>` and its `alt`, `width` and `height` attributes. See *Lists and links* and *Images*.",
        intuition="A link without `href` is not a link: it cannot be focused or followed. An image without `alt` is a mystery to anyone who cannot see it. Decorative images still need the attribute, set to an empty string, to say \"skip me\".",
        hints=[
            "Give every `<a>` in the nav an `href`, and add the missing third link.",
            "A fragment link has the form `href=\"#some-id\"`; the target needs the matching `id`. The Contact heading is a natural target.",
            "For the external link add both `target=\"_blank\"` and `rel=\"noopener\"`. For the divider write `alt=\"\"`, which is different from leaving `alt` out.",
        ],
        approach="1. Add `href` values to Home and Walks and a third link `<a href=\"#contact\">Contact</a>`.\n2. Put `id=\"contact\"` on the Contact heading.\n3. Add `target=\"_blank\" rel=\"noopener\"` to the https link and say in its text that it opens a new tab.\n4. Describe the photo in `alt` and state its intrinsic size with `width=\"320\" height=\"180\"`.\n5. Add `alt=\"\"` to the divider.",
        pitfalls="- `alt=\"image\"` or `alt=\"photo\"` describes nothing.\n- Omitting `alt` on the divider makes some screen readers read the file name.\n- Forgetting the `#` in the fragment link, which would request a file called `contact`.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-figure-caption", title="Figure with a caption", difficulty="Easy", pattern="HTML structure", kind="web",
    description=r"""
A chart is followed by a loose paragraph acting as its caption. Tie them together properly.

Requirements:

- The image is inside a `<figure>` element, together with a `<figcaption>` holding the caption text.
- The `<figcaption>` is a direct child of the `<figure>`.
- The image keeps a non-empty `alt` that is **not identical** to the caption text.
- The figure has **no outer margin** (browsers add 40px at the sides by default).
- The image never overflows its container: its computed `max-width` is `100%`.
""",
    starter=page("Rainfall", "body { font-family: system-ui, sans-serif; max-width: 30rem; }", """
<h1>Rainfall report</h1>
<img src="%s" alt="">
<p>Figure 1. The hills were wettest in the west.</p>
<p>The eastern slopes stayed dry for most of the month.</p>
""" % PIC),
    solution=page("Rainfall", """
body { font-family: system-ui, sans-serif; max-width: 30rem; }
figure { margin: 0; }
figure img { display: block; max-width: 100%; height: auto; }
figcaption { font-size: .9rem; color: #555; margin-top: .4rem; }
""", """
<h1>Rainfall report</h1>
<figure>
  <img src="%s" alt="Map of green hills with the sun over the eastern side" width="320" height="180">
  <figcaption>Figure 1. The hills were wettest in the west.</figcaption>
</figure>
<p>The eastern slopes stayed dry for most of the month.</p>
""" % PIC),
    checks=[
        C("The image is inside a figure", "!!document.querySelector('figure img')"),
        C("The figure has a figcaption child with text", "(c => !!c && c.textContent.trim().length > 0)(document.querySelector('figure > figcaption'))"),
        C("The image has non-empty alt text", "(i => !!i && i.alt.trim().length > 0)(document.querySelector('figure img'))"),
        C("The alt text differs from the caption", "(f => !!f && !!f.querySelector('img') && !!f.querySelector('figcaption') && f.querySelector('img').alt.trim() !== f.querySelector('figcaption').textContent.trim())(document.querySelector('figure'))"),
        C("The figure has no side margins", "(f => !!f && getComputedStyle(f).marginLeft === '0px' && getComputedStyle(f).marginRight === '0px')(document.querySelector('figure'))"),
        C("The image has max-width: 100%", "(i => !!i && getComputedStyle(i).maxWidth === '100%')(document.querySelector('figure img'))"),
    ],
    guide=dict(
        prereqs="`<figure>`, `<figcaption>`, alt text and fluid images. See *Images*.",
        intuition="A paragraph placed under a picture is a caption only to the eye. `<figure>` groups an illustration with its `<figcaption>` so that software knows they belong together. The caption adds context for everyone; the `alt` replaces the picture for people who cannot see it. They do different jobs, so they should not repeat each other.",
        hints=[
            "Wrap the `<img>` and the caption sentence in one `<figure>`.",
            "Change the caption's `<p>` to `<figcaption>`; it must sit directly inside the figure.",
            "Reset the browser default with `figure { margin: 0; }` and make the image fluid with `max-width: 100%; height: auto;`.",
        ],
        approach="1. Add `<figure>` around the image and caption.\n2. Replace the caption paragraph with `<figcaption>`.\n3. Write `alt` text that says what the picture shows, in words different from the caption.\n4. In the CSS, remove the figure's margin and give the image `max-width: 100%` and `height: auto`.",
        pitfalls="- Copying the caption into `alt`, so a screen reader hears it twice.\n- Putting the `<figcaption>` outside the `<figure>`.\n- Forgetting that `figure` has a default 40px side margin.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-data-table", title="Accessible data table", difficulty="Medium", pattern="Tables", kind="web",
    description=r"""
The opening hours below are marked up with only `<tr>` and `<td>`. Turn them into an accessible data table.

Requirements:

- The table has a `<caption>` (first child of the table) with text.
- A `<thead>` contains one row of **three** column headers: `<th scope="col">`.
- A `<tbody>` contains **three** rows; the first cell of each is a row header `<th scope="row">`, followed by two `<td>` cells (six `<td>` in total in the body).
- A `<tfoot>` contains exactly one row.
- Borders are collapsed: the table's computed `border-collapse` is `collapse`.
""",
    starter=page("Opening hours", """
body { font-family: system-ui, sans-serif; }
td { border: 1px solid #999; padding: .4rem .8rem; }
""", """
<p><b>Library opening hours</b></p>
<table>
  <tr><td>Day</td><td>Opens</td><td>Closes</td></tr>
  <tr><td>Weekdays</td><td>09:00</td><td>19:00</td></tr>
  <tr><td>Saturday</td><td>10:00</td><td>16:00</td></tr>
  <tr><td>Sunday</td><td>Closed</td><td>Closed</td></tr>
  <tr><td>Bank holidays</td><td colspan="2">See the notice board</td></tr>
</table>
"""),
    solution=page("Opening hours", """
body { font-family: system-ui, sans-serif; }
table { border-collapse: collapse; }
caption { font-weight: 700; text-align: left; padding-bottom: .4rem; }
th, td { border: 1px solid #999; padding: .4rem .8rem; text-align: left; }
thead th { background: #eceff1; }
""", """
<table>
  <caption>Library opening hours</caption>
  <thead>
    <tr><th scope="col">Day</th><th scope="col">Opens</th><th scope="col">Closes</th></tr>
  </thead>
  <tbody>
    <tr><th scope="row">Weekdays</th><td>09:00</td><td>19:00</td></tr>
    <tr><th scope="row">Saturday</th><td>10:00</td><td>16:00</td></tr>
    <tr><th scope="row">Sunday</th><td>Closed</td><td>Closed</td></tr>
  </tbody>
  <tfoot>
    <tr><th scope="row">Bank holidays</th><td colspan="2">See the notice board</td></tr>
  </tfoot>
</table>
"""),
    checks=[
        C("The table starts with a caption that has text", "(t => !!t && !!t.firstElementChild && t.firstElementChild.tagName === 'CAPTION' && t.firstElementChild.textContent.trim().length > 0)(document.querySelector('table'))"),
        C("thead has three th with scope=col", "document.querySelectorAll('thead th[scope=\"col\"]').length === 3 && document.querySelectorAll('thead tr').length === 1"),
        C("tbody has three rows", "document.querySelectorAll('tbody tr').length === 3 && document.querySelectorAll('tbody').length === 1"),
        C("Each body row starts with th scope=row", "document.querySelectorAll('tbody tr').length > 0 && [...document.querySelectorAll('tbody tr')].every(r => !!r.firstElementChild && r.firstElementChild.matches('th[scope=\"row\"]'))"),
        C("The body has six td data cells", "document.querySelectorAll('tbody td').length === 6"),
        C("tfoot has exactly one row", "document.querySelectorAll('tfoot tr').length === 1"),
        C("Borders are collapsed", "getComputedStyle(document.querySelector('table')).borderCollapse === 'collapse'"),
    ],
    guide=dict(
        prereqs="`caption`, `thead`, `tbody`, `tfoot`, `th` and the `scope` attribute; `border-collapse`. See *Tables for tabular data*.",
        intuition="A data cell such as \"19:00\" only means something with its two labels: the row (\"Weekdays\") and the column (\"Closes\"). Marking labels as `<th>` with a `scope` lets a screen reader announce them as the user moves through the grid. The caption names the whole table.",
        hints=[
            "Move the bold paragraph's text into a `<caption>` placed immediately after `<table>`.",
            "The first row holds column labels: wrap it in `<thead>` and change its cells to `<th scope=\"col\">`. In the other rows only the first cell is a label: `<th scope=\"row\">`.",
            "Wrap the three day rows in `<tbody>` and the bank-holiday row in `<tfoot>`. Add `table { border-collapse: collapse; }` and extend the border rule to `th` as well as `td`.",
        ],
        approach="1. Replace the paragraph with `<caption>Library opening hours</caption>` inside the table.\n2. Create `<thead>` with the header row and three `th scope=\"col\"`.\n3. Create `<tbody>` with the Weekdays, Saturday and Sunday rows, each starting with `th scope=\"row\"`.\n4. Create `<tfoot>` with the bank-holiday row.\n5. Style: `border-collapse: collapse` on the table and borders/padding on `th, td`.",
        pitfalls="- Leaving the heading as a separate paragraph: it is not connected to the table.\n- Using `scope=\"col\"` on the row headers.\n- Putting the bank-holiday row in `tbody`, which makes four body rows.\n- Styling only `td`, so the new `th` cells lose their borders.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-aspect-ratio-box", title="A 16:9 media box", difficulty="Easy", pattern="Images and media", kind="web",
    description=r"""
A video thumbnail must keep a widescreen shape at every width, and its picture must fill the box without being stretched.

Write the CSS for `.media` and for the image inside it.

Requirements:

- `.media` is as wide as its container but never wider than **640px**.
- `.media` has an `aspect-ratio` of **16 / 9** (so its height follows its width).
- The `<img>` fills the box exactly (same width and height as `.media`).
- The image uses `object-fit: cover`, so it is cropped instead of distorted.
- Do not set a fixed `height` in pixels on `.media`.
""",
    starter=page("Media box", """
body { font-family: system-ui, sans-serif; margin: 16px; }
.media {
  background: #263238;
  /* your code */
}
.media img {
  /* your code */
}
""", """
<div class="media">
  <img src="%s" alt="Green hills under a pale sun">
</div>
<p>Episode 4: crossing the ridge</p>
""" % PIC.replace("0 0 320 180", "0 0 320 320").replace("height='180'", "height='320'")),
    solution=page("Media box", """
body { font-family: system-ui, sans-serif; margin: 16px; }
.media {
  background: #263238;
  width: 100%;
  max-width: 640px;
  aspect-ratio: 16 / 9;
}
.media img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
""", """
<div class="media">
  <img src="%s" alt="Green hills under a pale sun">
</div>
<p>Episode 4: crossing the ridge</p>
""" % PIC.replace("0 0 320 180", "0 0 320 320").replace("height='180'", "height='320'")),
    checks=[
        C(".media is 640px wide in this 1024px frame", "Math.round(document.querySelector('.media').getBoundingClientRect().width) === 640"),
        C(".media has aspect-ratio 16 / 9", "getComputedStyle(document.querySelector('.media')).aspectRatio.replace(/\\s/g, '') === '16/9'"),
        C("The box is rendered in a 16:9 shape", "(r => Math.abs(r.width / r.height - 16 / 9) < 0.02)(document.querySelector('.media').getBoundingClientRect())"),
        C("The image fills the box exactly", "((b, i) => Math.abs(b.width - i.width) < 1 && Math.abs(b.height - i.height) < 1)(document.querySelector('.media').getBoundingClientRect(), document.querySelector('.media img').getBoundingClientRect())"),
        C("The image uses object-fit: cover", "getComputedStyle(document.querySelector('.media img')).objectFit === 'cover'"),
    ],
    guide=dict(
        prereqs="`max-width`, `aspect-ratio` and `object-fit`. See *Backgrounds, gradients and sizing images with CSS*.",
        intuition="`aspect-ratio` lets a box derive its height from its width, so the shape survives any resize. The picture inside is square, so forcing it into a 16:9 box would squash it. `object-fit: cover` scales it until the box is covered and crops the overflow.",
        hints=[
            "Give `.media` `width: 100%` and cap it with `max-width: 640px`.",
            "Add `aspect-ratio: 16 / 9;` and do not write any `height` on `.media`.",
            "Make the image take the whole box with `width: 100%; height: 100%;` and choose the cropping behaviour with `object-fit: cover`. `display: block` removes the inline gap under the image.",
        ],
        approach="1. `.media { width: 100%; max-width: 640px; aspect-ratio: 16 / 9; }`\n2. `.media img { display: block; width: 100%; height: 100%; object-fit: cover; }`\n3. Check: at 640px wide the box is 360px tall, and the square picture is cropped top and bottom.",
        pitfalls="- Setting `height: 360px`: the shape breaks as soon as the width changes.\n- Forgetting `height: 100%` on the image, so it keeps its own square shape and overflows the box.\n- Leaving the default `object-fit: fill`, which stretches the picture.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-accessible-form", title="An accessible sign-up form", difficulty="Medium", pattern="Forms", kind="web",
    description=r"""
The sign-up form below shows text next to its controls, but nothing is connected. Repair it.

Requirements:

- The `<form>` submits with the **post** method.
- Every visible control (`input`, `select`, `textarea`) has a programmatically associated `<label>` (wrap it, or use `for` + `id`), and every control has a `name`.
- The control with `id="name"` is required.
- The control with `id="email"` has `type="email"` and is required.
- The three membership options are radio buttons that share **one** `name`, grouped in a `<fieldset>` that has a `<legend>`.
- The form has a submit button.
""",
    starter=page("Join", """
body { font-family: system-ui, sans-serif; }
form { display: grid; gap: .8rem; max-width: 22rem; }
input, select, textarea, button { font: inherit; }
""", """
<form>
  <div>Full name <input id="name"></div>
  <div>Email <input id="email" type="text"></div>
  <div>Membership
    <input type="radio" name="m1" value="solo"> Solo
    <input type="radio" name="m2" value="family"> Family
    <input type="radio" name="m3" value="student"> Student
  </div>
  <div>Branch <select id="branch"><option>North</option><option>South</option></select></div>
  <div>Anything we should know? <textarea id="notes"></textarea></div>
  <div onclick="alert('sent')">Join</div>
</form>
"""),
    solution=page("Join", """
body { font-family: system-ui, sans-serif; }
form { display: grid; gap: .8rem; max-width: 22rem; }
input, select, textarea, button { font: inherit; }
label { display: block; }
""", """
<form action="/join" method="post">
  <div><label for="name">Full name</label> <input id="name" name="name" required autocomplete="name"></div>
  <div><label for="email">Email</label> <input id="email" name="email" type="email" required autocomplete="email"></div>
  <fieldset>
    <legend>Membership</legend>
    <label><input type="radio" name="membership" value="solo" checked> Solo</label>
    <label><input type="radio" name="membership" value="family"> Family</label>
    <label><input type="radio" name="membership" value="student"> Student</label>
  </fieldset>
  <div><label for="branch">Branch</label> <select id="branch" name="branch"><option>North</option><option>South</option></select></div>
  <div><label for="notes">Anything we should know?</label> <textarea id="notes" name="notes"></textarea></div>
  <button type="submit">Join</button>
</form>
"""),
    checks=[
        C("The form uses method post", "document.querySelector('form').method === 'post'"),
        C("Every control has an associated label", "(c => c.length >= 7 && c.every(e => e.labels && e.labels.length > 0))([...document.querySelectorAll('form input, form select, form textarea')])"),
        C("Every control has a name", "[...document.querySelectorAll('form input, form select, form textarea')].every(e => e.name.length > 0)"),
        C("#name is required", "(e => !!e && e.required)(document.getElementById('name'))"),
        C("#email is type=email and required", "(e => !!e && e.type === 'email' && e.required)(document.getElementById('email'))"),
        C("The three radios share one name inside a fieldset with a legend", "(f => !!f && !!f.querySelector('legend') && f.querySelector('legend').textContent.trim().length > 0 && f.querySelectorAll('input[type=radio]').length === 3 && new Set([...f.querySelectorAll('input[type=radio]')].map(r => r.name)).size === 1)(document.querySelector('form fieldset'))"),
        C("There is a real submit button", "!!document.querySelector('form button[type=\"submit\"], form button:not([type]), form input[type=\"submit\"]')"),
    ],
    guide=dict(
        prereqs="`form`, `label`, `name`, input types, radio groups, `fieldset`/`legend`, `required`. See *Forms: collecting input*.",
        intuition="Text beside a field is not a label until the two are linked. The link is what makes a screen reader announce \"Email, edit text\" and what makes a click on the words focus the field. Radio buttons exclude one another only when they share a `name`, and a group of them needs a `legend` to say what question they answer.",
        hints=[
            "For the text fields, wrap the visible words in `<label for=\"...\">` using the control's existing `id`.",
            "Give all three radios the same `name`, wrap each one in its own `<label>`, and wrap the whole group in `<fieldset>` with `<legend>Membership</legend>`.",
            "Add `name` to every control, `required` where asked, change the email field's `type`, set `method=\"post\"` on the form, and replace the clickable `div` with `<button type=\"submit\">`.",
        ],
        approach="1. `<form action=\"/join\" method=\"post\">`.\n2. Name field: `<label for=\"name\">` + `name=\"name\" required`.\n3. Email field: `type=\"email\" name=\"email\" required` with a label.\n4. Radios: one shared `name`, each wrapped in a label, inside `fieldset` + `legend`.\n5. Select and textarea: labels and names.\n6. Replace the `div onclick` with a real submit button.",
        pitfalls="- A `placeholder` is not a label.\n- A `for` value that does not exactly match an `id` connects nothing.\n- Different radio names allow all three to be selected at once.\n- A `div` with a click handler cannot be reached by keyboard and does not submit on Enter.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-form-validation", title="Validation attributes", difficulty="Medium", pattern="Forms", kind="web",
    description=r"""
Add built-in validation to the registration form using **HTML attributes only** (no JavaScript).

Requirements:

- `#username`: required, between **3** and **12** characters, and only lowercase letters and digits are valid (use `pattern`).
- `#age`: a number input, required, minimum **18**, maximum **99**.
- `#website`: a URL input that is **optional**.
- `#password`: a password input, required, at least **8** characters.
- `#terms`: a checkbox that must be ticked.
- The form must **not** have the `novalidate` attribute.
""",
    starter=page("Register", """
body { font-family: system-ui, sans-serif; }
form { display: grid; gap: .7rem; max-width: 22rem; }
label { display: grid; gap: .2rem; }
input, button { font: inherit; }
input:user-invalid { border: 2px solid #c62828; }
""", """
<form action="/register" method="post" novalidate>
  <label>Username <input id="username" name="username"></label>
  <label>Age <input id="age" name="age"></label>
  <label>Website (optional) <input id="website" name="website"></label>
  <label>Password <input id="password" name="password"></label>
  <label style="display:block"><input id="terms" name="terms" type="checkbox"> I accept the terms</label>
  <button type="submit">Register</button>
</form>
"""),
    solution=page("Register", """
body { font-family: system-ui, sans-serif; }
form { display: grid; gap: .7rem; max-width: 22rem; }
label { display: grid; gap: .2rem; }
input, button { font: inherit; }
input:user-invalid { border: 2px solid #c62828; }
""", """
<form action="/register" method="post">
  <label>Username <input id="username" name="username" required minlength="3" maxlength="12" pattern="[a-z0-9]+" autocomplete="username"></label>
  <label>Age <input id="age" name="age" type="number" min="18" max="99" required></label>
  <label>Website (optional) <input id="website" name="website" type="url"></label>
  <label>Password <input id="password" name="password" type="password" required minlength="8" autocomplete="new-password"></label>
  <label style="display:block"><input id="terms" name="terms" type="checkbox" required> I accept the terms</label>
  <button type="submit">Register</button>
</form>
"""),
    checks=[
        C("Username is required with length 3 to 12", "(u => u.required && u.minLength === 3 && u.maxLength === 12)(document.getElementById('username'))"),
        C("Username pattern rejects 'Bad Name' and accepts 'walker42'", "(u => { u.value = 'Bad Name'; const bad = u.validity.patternMismatch; u.value = 'walker42'; const good = !u.validity.patternMismatch; u.value = ''; return bad && good; })(document.getElementById('username'))"),
        C("Age is a required number from 18 to 99", "(a => a.type === 'number' && a.required && a.min === '18' && a.max === '99')(document.getElementById('age'))"),
        C("Age 17 is out of range, 18 is valid", "(a => { a.value = '17'; const low = a.validity.rangeUnderflow; a.value = '18'; const ok = a.validity.valid; a.value = ''; return low && ok; })(document.getElementById('age'))"),
        C("Website is an optional URL field", "(w => w.type === 'url' && !w.required)(document.getElementById('website'))"),
        C("Password is required with at least 8 characters", "(p => p.type === 'password' && p.required && p.minLength === 8)(document.getElementById('password'))"),
        C("The terms checkbox is required", "(t => t.type === 'checkbox' && t.required)(document.getElementById('terms'))"),
        C("The form does not disable validation", "!document.querySelector('form').noValidate"),
    ],
    guide=dict(
        prereqs="Constraint attributes: `required`, `minlength`, `maxlength`, `min`, `max`, `pattern`, and input types. See *Form validation and accessible error handling*.",
        intuition="The browser can enforce common rules itself if you declare them on the controls. Each rule is one attribute. The input `type` matters too: `min` and `max` only mean something on a number (or date) input, and `type=\"url\"` brings its own format check.",
        hints=[
            "Remove `novalidate` from the form first; while it is present the browser skips every check.",
            "The username needs four attributes: `required`, `minlength`, `maxlength` and a `pattern`. A character class such as `[a-z0-9]+` describes \"one or more lowercase letters or digits\"; the pattern must match the whole value.",
            "Set `type=\"number\"` with `min`/`max` on age, `type=\"url\"` on website (and nothing else, so it stays optional), `type=\"password\"` with `minlength=\"8\"` on password, and `required` on the checkbox.",
        ],
        approach="1. Delete `novalidate`.\n2. `#username`: `required minlength=\"3\" maxlength=\"12\" pattern=\"[a-z0-9]+\"`.\n3. `#age`: `type=\"number\" min=\"18\" max=\"99\" required`.\n4. `#website`: `type=\"url\"`.\n5. `#password`: `type=\"password\" required minlength=\"8\"`.\n6. `#terms`: `required`.\n7. Try submitting bad values to see the browser's messages.",
        pitfalls="- `pattern` is ignored on an empty value, so it does not replace `required`.\n- Writing anchors is unnecessary: the pattern is matched against the entire value automatically.\n- `min`/`max` on a text input do nothing.\n- Adding `required` to the optional website field.\n- Remember that the server must repeat every check; attributes help users, they do not provide security.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-semantic-skeleton", title="Semantic page skeleton", difficulty="Easy", pattern="Semantic HTML", kind="web",
    description=r"""
This page is built entirely from `<div>` elements with ids. Replace them with semantic elements. The text can stay as it is.

Requirements:

- `<html>` has a `lang` attribute.
- `<body>` has exactly one `<header>` child and exactly one `<footer>` child, and **no** `<div>` children.
- There is a `<nav>` with a non-empty `aria-label` containing at least three links.
- There is exactly one `<main>`.
- Inside `<main>` there is an `<article>` containing the page's only `<h1>`.
- There is an `<aside>` for the related links.
""",
    starter="""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Tide Times</title>
<style>
body { font-family: system-ui, sans-serif; margin: 0; }
body > * { padding: .8rem 1rem; }
</style>
</head>
<body>
<div id="header">
  <div class="logo">Tide Times</div>
  <div id="nav"><a href="/">Home</a> <a href="/today">Today</a> <a href="/week">This week</a></div>
</div>
<div id="main">
  <div class="post">
    <div class="title">Spring tides explained</div>
    <p>Twice a month the sun and moon line up and the tidal range is at its greatest.</p>
  </div>
  <div id="sidebar">
    <div class="title">Related</div>
    <a href="/neap">Neap tides</a>
  </div>
</div>
<div id="footer">Data from the harbour office.</div>
</body>
</html>
""",
    solution="""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Tide Times</title>
<style>
body { font-family: system-ui, sans-serif; margin: 0; }
body > * { padding: .8rem 1rem; }
</style>
</head>
<body>
<header>
  <p class="logo">Tide Times</p>
  <nav aria-label="Main"><a href="/">Home</a> <a href="/today">Today</a> <a href="/week">This week</a></nav>
</header>
<main>
  <article>
    <h1>Spring tides explained</h1>
    <p>Twice a month the sun and moon line up and the tidal range is at its greatest.</p>
  </article>
  <aside>
    <h2>Related</h2>
    <a href="/neap">Neap tides</a>
  </aside>
</main>
<footer>Data from the harbour office.</footer>
</body>
</html>
""",
    checks=[
        C("html has a lang attribute", "document.documentElement.lang.trim().length >= 2"),
        C("body has one header and one footer child", "document.querySelectorAll('body > header').length === 1 && document.querySelectorAll('body > footer').length === 1"),
        C("body has no div children", "document.querySelectorAll('body > div').length === 0"),
        C("A labelled nav holds at least three links", "(n => !!n && (n.getAttribute('aria-label') || '').trim().length > 0 && n.querySelectorAll('a[href]').length >= 3)(document.querySelector('nav'))"),
        C("There is exactly one main", "document.querySelectorAll('main').length === 1"),
        C("The only h1 is inside an article in main", "document.querySelectorAll('h1').length === 1 && !!document.querySelector('main article h1')"),
        C("There is an aside", "!!document.querySelector('aside')"),
    ],
    guide=dict(
        prereqs="`header`, `nav`, `main`, `article`, `aside`, `footer`, landmarks and the `lang` attribute. See *Semantic page structure*.",
        intuition="An `id` such as `header` helps you, the author, but tells the browser nothing. The matching element creates a landmark that assistive technology can jump to and that reader modes and search engines can use. Each `div` here already has an obvious role in its name: swap the generic element for the specific one.",
        hints=[
            "Map the ids directly: `#header` to `<header>`, `#nav` to `<nav>`, `#main` to `<main>`, `#footer` to `<footer>`.",
            "The post could be published on its own, so it is an `<article>`; its title is the page's `<h1>`. The sidebar is loosely related content: `<aside>`, with an `<h2>` for its title.",
            "Add `lang=\"en\"` to `<html>` and an `aria-label` such as `Main` to the `<nav>`.",
        ],
        approach="1. Add `lang` to the root element.\n2. Replace the outer three `div`s with `header`, `main`, `footer`.\n3. Turn the link group into `<nav aria-label=\"Main\">`.\n4. Turn `.post` into `<article>` and its title into `<h1>`.\n5. Turn `#sidebar` into `<aside>` and its title into `<h2>`.",
        pitfalls="- Confusing `<header>` (a visible region) with `<head>` (metadata).\n- Using two `<h1>` elements: the sidebar title is a lower level.\n- Writing \"Main navigation\" as the label: the role already says \"navigation\", so the screen reader would say it twice.\n- More than one `<main>`.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-details-summary", title="FAQ with details and summary", difficulty="Easy", pattern="Semantic HTML", kind="web",
    description=r"""
Build a three-question FAQ that expands and collapses **without JavaScript**.

Requirements:

- Exactly three `<details>` elements.
- In each one the **first child** is a `<summary>` (the question), followed by at least one more element (the answer).
- The **first** item is open when the page loads; the other two are closed.
- All three have `name="faq"`, so that opening one closes the others.
- The `<summary>` shows a pointer cursor (`cursor: pointer`).
""",
    starter=page("FAQ", """
body { font-family: system-ui, sans-serif; max-width: 30rem; }
.q { font-weight: 700; }
""", """
<h1>Ferry questions</h1>
<div class="item">
  <p class="q">Can I bring a bicycle?</p>
  <p>Yes, bicycles travel free on every sailing.</p>
</div>
<div class="item">
  <p class="q">Are dogs allowed?</p>
  <p>Dogs are welcome on the outer deck.</p>
</div>
<div class="item">
  <p class="q">Is there a cafe on board?</p>
  <p>Hot drinks are served on sailings longer than thirty minutes.</p>
</div>
"""),
    solution=page("FAQ", """
body { font-family: system-ui, sans-serif; max-width: 30rem; }
details { border: 1px solid #cfd8dc; border-radius: 8px; padding: .5rem .8rem; margin-bottom: .5rem; }
summary { font-weight: 700; cursor: pointer; }
""", """
<h1>Ferry questions</h1>
<details name="faq" open>
  <summary>Can I bring a bicycle?</summary>
  <p>Yes, bicycles travel free on every sailing.</p>
</details>
<details name="faq">
  <summary>Are dogs allowed?</summary>
  <p>Dogs are welcome on the outer deck.</p>
</details>
<details name="faq">
  <summary>Is there a cafe on board?</summary>
  <p>Hot drinks are served on sailings longer than thirty minutes.</p>
</details>
"""),
    checks=[
        C("There are exactly three details elements", "document.querySelectorAll('details').length === 3"),
        C("Each details starts with a summary", "document.querySelectorAll('details').length > 0 && [...document.querySelectorAll('details')].every(d => !!d.firstElementChild && d.firstElementChild.tagName === 'SUMMARY' && d.firstElementChild.textContent.trim().length > 0)"),
        C("Each details has answer content after the summary", "document.querySelectorAll('details').length > 0 && [...document.querySelectorAll('details')].every(d => d.children.length >= 2)"),
        C("Only the first item is open", "(d => d.length === 3 && d[0].open && !d[1].open && !d[2].open)([...document.querySelectorAll('details')])"),
        C("All three share name=faq", "document.querySelectorAll('details[name=\"faq\"]').length === 3"),
        C("The summary has cursor: pointer", "(s => !!s && getComputedStyle(s).cursor === 'pointer')(document.querySelector('summary'))"),
    ],
    guide=dict(
        prereqs="`<details>`, `<summary>`, the `open` and `name` attributes. See *Semantic page structure*.",
        intuition="A disclosure widget is built into HTML. `<details>` hides its content until its `<summary>` is activated, works with the keyboard, and reports its expanded state to screen readers. Giving several of them the same `name` turns them into an accordion in which only one can be open.",
        hints=[
            "Replace each `div.item` with `<details>` and each question paragraph with `<summary>`.",
            "The boolean attribute `open` on the first `<details>` makes it start expanded.",
            "Add `name=\"faq\"` to all three, and `summary { cursor: pointer; }` in the CSS.",
        ],
        approach="1. Convert the three wrappers to `<details name=\"faq\">`.\n2. Convert each `.q` paragraph to `<summary>` and keep it as the first child.\n3. Add `open` to the first one only.\n4. Style the summary with `cursor: pointer` (and anything else you like).",
        pitfalls="- Putting the `<summary>` after the answer: it must come first.\n- Writing `open=\"false\"` on the others: any `open` attribute means open.\n- Hiding the answers with `display: none` yourself: the element already does that.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-visually-hidden", title="Visually hidden text for an icon button", difficulty="Medium", pattern="Accessibility", kind="web",
    description=r"""
The button below shows only a magnifying-glass icon, so a screen reader announces "button" and nothing else. Give it a name that is hidden from sight but available to assistive technology.

Requirements:

- Inside the button, add a `<span class="sr-only">` containing the text for the button (for example "Search").
- Write the `.sr-only` class so that the span:
  - is taken out of the layout with `position: absolute`,
  - occupies at most **1px by 1px**,
  - hides its overflow (`overflow: hidden`),
  - does not wrap (`white-space: nowrap`),
  - is **not** hidden with `display: none` (that would hide it from screen readers too).
- The decorative `<svg>` has `aria-hidden="true"`.
""",
    starter=page("Icon button", """
body { font-family: system-ui, sans-serif; }
button { padding: .5rem; border-radius: 8px; border: 2px solid #37474f; background: white; }
svg { width: 24px; height: 24px; display: block; }
.sr-only {
  /* your code */
}
""", """
<button type="button">
  <svg viewBox="0 0 24 24"><circle cx="10" cy="10" r="6" fill="none" stroke="currentColor" stroke-width="2.5"/><path d="M15 15l6 6" stroke="currentColor" stroke-width="2.5"/></svg>
</button>
"""),
    solution=page("Icon button", """
body { font-family: system-ui, sans-serif; }
button { padding: .5rem; border-radius: 8px; border: 2px solid #37474f; background: white; }
svg { width: 24px; height: 24px; display: block; }
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  border: 0;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
""", """
<button type="button">
  <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="10" r="6" fill="none" stroke="currentColor" stroke-width="2.5"/><path d="M15 15l6 6" stroke="currentColor" stroke-width="2.5"/></svg>
  <span class="sr-only">Search</span>
</button>
"""),
    checks=[
        C("The button contains .sr-only text", "(s => !!s && s.textContent.trim().length >= 3)(document.querySelector('button .sr-only'))"),
        C(".sr-only is position: absolute with overflow: hidden", "(e => !!e && getComputedStyle(e).position === 'absolute' && getComputedStyle(e).overflow === 'hidden')(document.querySelector('.sr-only'))"),
        C(".sr-only is at most 1px by 1px", "(e => !!e && e.getBoundingClientRect().width <= 1.5 && e.getBoundingClientRect().height <= 1.5)(document.querySelector('.sr-only'))"),
        C(".sr-only does not wrap", "(e => !!e && getComputedStyle(e).whiteSpace === 'nowrap')(document.querySelector('.sr-only'))"),
        C(".sr-only is not display: none", "(e => !!e && getComputedStyle(e).display !== 'none')(document.querySelector('.sr-only'))"),
        C("The svg is hidden from assistive technology", "(s => !!s && s.getAttribute('aria-hidden') === 'true')(document.querySelector('button svg'))"),
    ],
    guide=dict(
        prereqs="Accessible names, `aria-hidden`, the difference between `display: none` and visual hiding. See *Accessibility: names, focus, contrast and ARIA*.",
        intuition="`display: none` and `visibility: hidden` remove content for everybody, including screen readers. To hide text only from the eye, keep it rendered but shrink it to a single clipped pixel and lift it out of the flow so it does not disturb the layout. The icon, meanwhile, adds nothing for a non-visual user, so it is marked as hidden from the accessibility tree.",
        hints=[
            "Add `<span class=\"sr-only\">Search</span>` inside the `<button>`, after the icon.",
            "The class needs `position: absolute; width: 1px; height: 1px; overflow: hidden;`.",
            "Finish with `white-space: nowrap` (so the text is not squeezed into a tall column), `clip-path: inset(50%)`, `margin: -1px`, `padding: 0`, `border: 0`, and add `aria-hidden=\"true\"` to the `<svg>`.",
        ],
        approach="1. Insert the span with the button's name.\n2. Write the clipping class: absolute position, 1px box, overflow hidden, no wrapping, clip-path.\n3. Mark the icon `aria-hidden=\"true\"`.\n4. Inspect the button in the accessibility pane of developer tools: its name is now \"Search\".",
        pitfalls="- Using `display: none` or `visibility: hidden`: the name disappears for screen readers.\n- Using `width: 0; height: 0`: some screen readers skip zero-sized content.\n- Forgetting `position: absolute`, so the 1px box still nudges the layout.\n- Leaving the icon exposed, which can be announced as an unlabelled image.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-skip-link", title="Skip to main content link", difficulty="Medium", pattern="Accessibility", kind="web",
    description=r"""
Keyboard users have to tab through the whole menu on every page. Add a **skip link**.

Requirements:

- The **first focusable element** in the body is `<a class="skip-link" href="#main">` with visible text.
- The `<main>` element has `id="main"` and `tabindex="-1"` (so it can receive focus when the link is followed).
- `.skip-link` is `position: absolute` and, when not focused, lies completely **off screen** (above the top edge or left of the left edge of the viewport).
- A rule whose selector contains `.skip-link:focus` (or `.skip-link:focus-visible`) moves the link back on screen by setting `top`, `left`, `inset`, `transform` or `translate`.
- Do not hide the link with `display: none` or `visibility: hidden` (it could never receive focus).
""",
    starter=page("Skip link", """
body { font-family: system-ui, sans-serif; margin: 0; }
nav { background: #263238; padding: .8rem 1rem; }
nav a { color: white; margin-right: 1rem; }
main { padding: 1rem; }
.skip-link {
  /* your code */
}
""", """
<nav aria-label="Main">
  <a href="/">Home</a><a href="/routes">Routes</a><a href="/tickets">Tickets</a><a href="/help">Help</a>
</nav>
<main>
  <h1>Timetable</h1>
  <p>Buses run every ten minutes.</p>
</main>
"""),
    solution=page("Skip link", """
body { font-family: system-ui, sans-serif; margin: 0; }
nav { background: #263238; padding: .8rem 1rem; }
nav a { color: white; margin-right: 1rem; }
main { padding: 1rem; }
main:focus { outline: none; }
.skip-link {
  position: absolute;
  left: 8px;
  top: -100px;
  padding: .5rem .8rem;
  background: #ffb300;
  color: #111;
  border-radius: 6px;
}
.skip-link:focus {
  top: 8px;
}
""", """
<a class="skip-link" href="#main">Skip to main content</a>
<nav aria-label="Main">
  <a href="/">Home</a><a href="/routes">Routes</a><a href="/tickets">Tickets</a><a href="/help">Help</a>
</nav>
<main id="main" tabindex="-1">
  <h1>Timetable</h1>
  <p>Buses run every ten minutes.</p>
</main>
"""),
    checks=[
        C("The first focusable element is a.skip-link pointing to #main", "(a => !!a && a.matches('a.skip-link[href=\"#main\"]') && a.textContent.trim().length > 3)(document.body.querySelector('a[href], button, input, select, textarea, [tabindex]'))"),
        C("main has id=main and tabindex=-1", "(m => !!m && m.tagName === 'MAIN' && m.getAttribute('tabindex') === '-1')(document.getElementById('main'))"),
        C(".skip-link is position: absolute", "(a => !!a && getComputedStyle(a).position === 'absolute')(document.querySelector('.skip-link'))"),
        C("The link is off screen when not focused", "(a => !!a && (a.getBoundingClientRect().bottom <= 0 || a.getBoundingClientRect().right <= 0))(document.querySelector('.skip-link'))"),
        C("The link is not display:none or visibility:hidden", "(a => !!a && getComputedStyle(a).display !== 'none' && getComputedStyle(a).visibility !== 'hidden')(document.querySelector('.skip-link'))"),
        C("A .skip-link:focus rule brings it back on screen", RULES + ".some(r => r.selectorText && r.selectorText.includes('.skip-link:focus') && !!(r.style.top || r.style.left || r.style.inset || r.style.transform || r.style.translate))"),
    ],
    guide=dict(
        prereqs="Keyboard focus order, `tabindex`, fragment links, `position: absolute` and the `:focus` pseudo-class. See *Accessibility* and *Normal flow, display, positioning and stacking*.",
        intuition="Tab order follows the order of the HTML, so a link placed first in the body is the first thing a keyboard user reaches. Moving it off screen keeps the design clean for mouse users, and a `:focus` rule slides it into view at the moment it is needed. It must stay rendered: an element with `display: none` cannot be focused.",
        hints=[
            "Add `<a class=\"skip-link\" href=\"#main\">Skip to main content</a>` as the very first element in `<body>`, and give `<main>` the attributes `id=\"main\" tabindex=\"-1\"`.",
            "Park the link above the viewport: `position: absolute; top: -100px; left: 8px;`.",
            "Bring it back with `.skip-link:focus { top: 8px; }`. Give it a solid background and padding so it is readable over the menu.",
        ],
        approach="1. Insert the link before the `<nav>`.\n2. Add `id` and `tabindex=\"-1\"` to `<main>`.\n3. Style `.skip-link` as an absolutely positioned box with a negative `top`.\n4. Add the `:focus` rule that sets `top` to a positive value.\n5. Test: click in the page, press Tab once, then Enter.",
        pitfalls="- Hiding the link with `display: none`: it leaves the tab order.\n- Placing it after the navigation, which defeats the purpose.\n- Forgetting `tabindex=\"-1\"` on `main`: in some browsers focus then stays at the top and the next Tab returns to the menu.\n- Using a positive `tabindex` to force it first; source order is the right tool.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="web-seo-head", title="A complete document head", difficulty="Easy", pattern="Metadata and SEO", kind="web",
    description=r"""
The page below has an almost empty `<head>`. Add the metadata that browsers, search engines and social networks rely on.

Requirements:

- `<html>` has a `lang` attribute.
- The **first element** in `<head>` is `<meta charset="utf-8">`.
- A viewport meta tag whose content includes `width=device-width`.
- A `<title>` between **10 and 60** characters long.
- A `<meta name="description">` whose content is between **50 and 160** characters.
- A `<link rel="canonical">` whose `href` is an absolute `https://` URL.
- An Open Graph title: `<meta property="og:title" content="...">` with non-empty content.
- The body contains exactly one `<h1>`.
""",
    starter="""<!doctype html>
<html>
<head>
<title>Home</title>
</head>
<body>
<h2>Tideway Pool</h2>
<p>Adult swimming lessons every Tuesday evening. Small groups, friendly teachers.</p>
</body>
</html>
""",
    solution="""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Adult Swimming Lessons | Tideway Pool</title>
<meta name="description" content="Eight-week adult swimming courses for beginners and improvers at Tideway Pool. Small groups on Tuesday evenings. Book online.">
<link rel="canonical" href="https://tidewaypool.example/lessons/adults">
<meta property="og:title" content="Adult Swimming Lessons at Tideway Pool">
<meta property="og:description" content="Small-group evening courses for beginners and improvers.">
</head>
<body>
<h1>Adult swimming lessons</h1>
<p>Adult swimming lessons every Tuesday evening. Small groups, friendly teachers.</p>
</body>
</html>
""",
    checks=[
        C("html has a lang attribute", "document.documentElement.lang.trim().length >= 2"),
        C("meta charset=utf-8 is the first element in head", "(m => !!m && m.tagName === 'META' && (m.getAttribute('charset') || '').toLowerCase() === 'utf-8')(document.head.firstElementChild)"),
        C("A viewport meta tag uses width=device-width", "(m => !!m && m.content.replace(/\\s/g, '').includes('width=device-width'))(document.querySelector('meta[name=\"viewport\"]'))"),
        C("The title is 10 to 60 characters", "(t => t.length >= 10 && t.length <= 60)(document.title.trim())"),
        C("The meta description is 50 to 160 characters", "(m => !!m && m.content.trim().length >= 50 && m.content.trim().length <= 160)(document.querySelector('meta[name=\"description\"]'))"),
        C("The canonical link is an absolute https URL", "(l => !!l && (l.getAttribute('href') || '').startsWith('https://'))(document.querySelector('link[rel=\"canonical\"]'))"),
        C("An og:title meta tag has content", "(m => !!m && (m.getAttribute('content') || '').trim().length > 0)(document.querySelector('meta[property=\"og:title\"]'))"),
        C("The body has exactly one h1", "document.querySelectorAll('h1').length === 1"),
    ],
    guide=dict(
        prereqs="The elements of `<head>`: `meta charset`, viewport, `title`, description, canonical and Open Graph tags. See *Ids, classes, generic containers and the document head* and *From idea to live site*.",
        intuition="Nothing in the head is drawn on the page, yet it decides how the page appears everywhere else: the browser tab, a search result, a link pasted into a chat. A search result is made of the title and (often) the description, so a page titled \"Home\" gives nobody a reason to click.",
        hints=[
            "Put `<meta charset=\"utf-8\">` on the first line inside `<head>`, before the title, and add `lang` to `<html>`.",
            "Write a specific title (page topic, then site name) and a one- or two-sentence description; count the characters against the limits.",
            "Add `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">`, a `<link rel=\"canonical\" href=\"https://...\">`, an `og:title` meta tag, and change the page's main heading to `<h1>`.",
        ],
        approach="1. `<html lang=\"en\">`.\n2. Charset first, then viewport.\n3. Replace \"Home\" with a descriptive title of 10-60 characters.\n4. Add a description of 50-160 characters that would make sense as a search snippet.\n5. Add the canonical link with a full https URL.\n6. Add `og:title` (and ideally `og:description` and `og:image`).\n7. Promote the `<h2>` to the single `<h1>`.",
        pitfalls="- Using `name=\"og:title\"`: Open Graph tags use the `property` attribute.\n- A relative canonical URL.\n- The same title on every page of a site.\n- Putting charset after the title, where the browser may already have guessed an encoding.",
    ),
),
]
