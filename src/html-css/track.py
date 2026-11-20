TRACK = dict(
    id="html-css",
    title="HTML & CSS",
    icon="🎨",
    color="#e8590c",
    group="Web",
    blurb="Build accessible, responsive pages from first principles: semantic HTML, the cascade, the box model, "
          "Flexbox, Grid, modern CSS and the browser rendering pipeline, with live editable examples and auto-checked exercises.",
    sources=["Duckett, HTML & CSS: Design and Build Websites, ch. 1-19", "MDN Web Docs (developer.mozilla.org)", "WCAG 2.2"],
    modules=[
        dict(
            id="html-foundations",
            title="HTML foundations",
            summary="How pages reach the browser, the DOM, text markup, lists and links.",
            lessons=[
                dict(id="how-pages-work", title="How web pages work: elements, attributes and the DOM", file="01-structure.md"),
                dict(id="text-markup", title="Marking up text: headings, paragraphs and inline meaning", file="02-text.md"),
                dict(id="lists-links", title="Lists and links", file="03-lists-links.md"),
            ],
            problems=["web-headings-lists", "web-links-images"],
        ),
        dict(
            id="media-tables",
            title="Images, tables and media",
            summary="Alt text and responsive images, data tables, video, audio and embeds.",
            lessons=[
                dict(id="images", title="Images: formats, alt text and responsive delivery", file="04-images.md"),
                dict(id="tables", title="Tables for tabular data", file="05-tables.md"),
                dict(id="media-embeds", title="Video, audio and embedded content", file="06-media.md"),
            ],
            problems=["web-figure-caption", "web-data-table", "web-aspect-ratio-box"],
        ),
        dict(
            id="forms",
            title="Forms",
            summary="Controls, labels, submission, validation and accessible error handling.",
            lessons=[
                dict(id="forms", title="Forms: collecting input", file="07-forms.md"),
                dict(id="form-validation", title="Form validation and accessible error handling", file="08-form-validation.md"),
            ],
            problems=["web-accessible-form", "web-form-validation"],
        ),
        dict(
            id="semantics-a11y",
            title="Semantics and accessibility",
            summary="Ids and classes, the document head, landmarks, the outline, ARIA, focus and contrast.",
            lessons=[
                dict(id="ids-classes-meta", title="Ids, classes, generic containers and the document head", file="09-extra-markup.md"),
                dict(id="semantic-structure", title="Semantic page structure: landmarks and the document outline", file="10-semantic-layout.md"),
                dict(id="accessibility", title="Accessibility: names, focus, contrast and ARIA", file="11-accessibility.md"),
            ],
            problems=["web-semantic-skeleton", "web-details-summary", "web-visually-hidden", "web-skip-link"],
        ),
        dict(
            id="css-foundations",
            title="CSS foundations",
            summary="Rules and selectors, the cascade and specificity, colour and typography.",
            lessons=[
                dict(id="css-intro", title="Introducing CSS: rules, selectors and where styles live", file="12-intro-css.md"),
                dict(id="cascade", title="The cascade, specificity and inheritance", file="13-cascade.md"),
                dict(id="color", title="Colour: notations, transparency and contrast", file="14-color.md"),
                dict(id="typography", title="Typography: fonts, sizes, spacing and units", file="15-typography.md"),
            ],
            problems=["web-specificity-fix", "web-pseudo-elements", "web-zebra-table", "web-typography-rem"],
        ),
        dict(
            id="boxes-styling",
            title="Boxes and visual styling",
            summary="The box model, styling lists, tables and forms, backgrounds and image sizing.",
            lessons=[
                dict(id="box-model", title="The box model: content, padding, border and margin", file="16-box-model.md"),
                dict(id="lists-tables-forms-css", title="Styling lists, tables and forms", file="17-lists-tables-forms-css.md"),
                dict(id="backgrounds-images", title="Backgrounds, gradients and sizing images with CSS", file="18-backgrounds-images.md"),
            ],
            problems=["web-card-box-model", "web-button-states", "web-pricing-table"],
        ),
        dict(
            id="layout",
            title="Layout",
            summary="Normal flow, positioning and stacking, Flexbox and Grid in depth.",
            lessons=[
                dict(id="display-positioning", title="Normal flow, display, positioning and stacking", file="19-display-positioning.md"),
                dict(id="flexbox", title="Flexbox in depth", file="20-flexbox.md"),
                dict(id="grid", title="CSS Grid in depth", file="21-grid.md"),
            ],
            problems=["web-center-flex", "web-navbar", "web-positioned-badge", "web-z-index-stack", "web-sticky-header",
                      "web-footer-bottom", "web-two-column-grid", "web-holy-grail", "web-modal-layout"],
        ),
        dict(
            id="responsive-modern",
            title="Responsive and modern CSS",
            summary="Media and container queries, fluid sizing, custom properties, transitions and animations.",
            lessons=[
                dict(id="responsive", title="Responsive design: viewport, media queries, fluid sizing and container queries", file="22-responsive.md"),
                dict(id="custom-properties", title="Custom properties and theming", file="23-custom-properties.md"),
                dict(id="transitions-animations", title="Transitions, transforms and animations", file="24-transitions-animations.md"),
            ],
            problems=["web-auto-fit-cards", "web-custom-props-theme", "web-transition-hover", "web-css-animation"],
        ),
        dict(
            id="professional-practice",
            title="Professional practice",
            summary="CSS architecture, rendering and performance, process, SEO and hosting, and interview review.",
            lessons=[
                dict(id="css-architecture", title="CSS architecture: BEM, utilities, modules and layers", file="25-css-architecture.md"),
                dict(id="rendering-performance", title="How browsers render pages, and how to make them fast", file="26-rendering-performance.md"),
                dict(id="process-seo-hosting", title="From idea to live site: process, design, SEO, analytics and hosting", file="27-process-seo-hosting.md"),
                dict(id="interview-essentials", title="HTML & CSS interview essentials", file="28-interview-essentials.md"),
            ],
            problems=["web-bem-card", "web-seo-head"],
        ),
    ],
)
