# Video, audio and embedded content

> **Before this lesson:** you should know how images are embedded and described ([Images](#/lesson/html-css/images)) and how URLs work ([Lists and links](#/lesson/html-css/lists-links)).

## In plain words

**Media** here means anything on a page that plays or moves: video, audio, an embedded map, an interactive chart. Modern HTML has elements that play video and sound directly and an element, `<iframe>`, that shows another web page inside a rectangle of yours.

Think of a living-room wall. A framed photograph is like an image. A television on the same wall is like a `<video>`: it needs controls, it may have subtitles, and it should not start blaring when someone walks in. A window in the wall, through which you see a neighbour's garden, is like an `<iframe>`: you can look at it, but it belongs to someone else and you do not control what is in it.

Video is a large share of all internet traffic, and most sites embed something from a third party. You need to know how to offer several file formats, how to provide captions for people who cannot hear the sound, and how to embed other people's content without creating security or performance problems.

## Why it is worth learning properly

For most of the web's first two decades, a browser could not play a video by itself. Sound and moving pictures needed a plug-in, and the dominant one was Adobe Flash: a separate program that drew inside a rectangle on the page. It powered early video sites, games and animated adverts, but it was closed, power-hungry, a constant source of security holes, invisible to search engines and screen readers, and it never ran on the iPhone. Browsers removed it completely at the end of 2020.

What replaced it is built into HTML itself: the `<video>` and `<audio>` elements, plus `<iframe>` for embedding other pages, and `<canvas>` and SVG for graphics. You will still find old tutorials describing `<object>`, `<embed>` and Flash detection scripts. Treat those as history. This lesson teaches the modern toolkit and the accessibility duties that come with it.

> The examples here cannot download real media files, so they demonstrate the markup, the controls and the fallback behaviour. Substitute your own file URLs to see playback.

## The `video` element

The smallest useful video is one line:

```html
<video src="tour.mp4" controls width="640" height="360"></video>
```

Unlike `<img>`, `<video>` has a closing tag, because it can contain alternative sources, text tracks and fallback content.

| Attribute | Effect |
|---|---|
| `controls` | Show the browser's play, seek, volume and fullscreen controls |
| `width`, `height` | Reserve space with the right aspect ratio (CSS pixels) |
| `poster` | Image shown before playback starts |
| `preload` | `none`, `metadata` or `auto`: how much to fetch in advance |
| `autoplay` | Start playing when ready (browsers only allow it when muted) |
| `muted` | Start with the sound off |
| `loop` | Restart at the end |
| `playsinline` | On iOS, play inside the page instead of going fullscreen |

`controls`, `autoplay`, `muted`, `loop` and `playsinline` are boolean attributes.

```html-run
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Video element</title>
<style>
  video { max-width: 100%; height: auto; background: #111; border-radius: 8px; }
</style></head>
<body>
  <video controls width="480" height="270" preload="none"
         poster="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 480 270'%3E%3Crect width='480' height='270' fill='%23263238'/%3E%3Ccircle cx='240' cy='135' r='44' fill='%23ffffff' opacity='.85'/%3E%3Cpath d='M226 112v46l38-23z' fill='%23263238'/%3E%3C/svg%3E">
    <source src="tour.webm" type="video/webm">
    <source src="tour.mp4" type="video/mp4">
    <p>Your browser cannot play this video.
       <a href="tour.mp4">Download the MP4</a> instead.</p>
  </video>
  <p>The poster image and native controls appear even though no file is available.</p>
</body>
</html>
```

### Multiple sources and codecs

A video file is a **container** (MP4, WebM) holding streams compressed with **codecs** (H.264, VP9, AV1 for pictures; AAC, Opus for sound). No single combination is ideal everywhere, so you can list several `<source>` children. The browser reads them top to bottom and plays the first whose `type` it supports, without downloading the others.

| Container / codec | Support | Character |
|---|---|---|
| MP4 with H.264 + AAC | Universal | The safe fallback |
| WebM with VP9 + Opus | All current browsers | Smaller files, royalty-free |
| MP4 or WebM with AV1 | Most current browsers | Smallest files, slow to encode |

List the most efficient format first and the most compatible last. Anything inside `<video>` that is not a `source` or `track` is **fallback content**, shown only by browsers that do not understand the element at all; a download link is the usual choice.

### Autoplay rules

Browsers block audible autoplay because users hate it. A video will start by itself only if it is `muted` (and, on iOS, `playsinline`). That combination is what makes decorative background loops possible:

```html
<video autoplay muted loop playsinline poster="waves.jpg">
  <source src="waves.webm" type="video/webm">
  <source src="waves.mp4" type="video/mp4">
</video>
```

> [!WARNING]
> Motion that starts automatically and lasts more than five seconds must have a way to pause or stop it (WCAG 2.2.2). Movement can trigger nausea or distract people with attention difficulties. Provide a pause button, and consider not autoplaying at all when the user has asked for reduced motion (`@media (prefers-reduced-motion: reduce)`).

## Captions, subtitles and descriptions: `<track>`

A video without captions excludes deaf and hard-of-hearing viewers, and also anyone watching on a train with the sound off. The `<track>` element attaches timed text stored in a **WebVTT** file.

```html
<video controls>
  <source src="talk.mp4" type="video/mp4">
  <track kind="captions"  src="talk.en.vtt" srclang="en" label="English" default>
  <track kind="subtitles" src="talk.es.vtt" srclang="es" label="Español">
</video>
```

| `kind` | Contains | Audience |
|---|---|---|
| `subtitles` | Translation of the dialogue | Viewers who can hear but do not know the language |
| `captions` | Dialogue *and* significant sounds ("door slams", "music fades") | Viewers who cannot hear the audio |
| `descriptions` | Text describing what happens visually | Viewers who cannot see the video |
| `chapters` | Titles for navigation points | Everyone |
| `metadata` | Data for scripts | Not displayed |

A WebVTT file is plain text:

```text
WEBVTT

00:00:01.000 --> 00:00:04.000
Welcome to the harbour tour.

00:00:04.500 --> 00:00:07.000
[seagulls calling]
```

`srclang` is required for subtitles, `label` is what appears in the caption menu, and `default` switches a track on initially. For content with no accompanying text track, publish a **transcript** on the page; it also makes the content searchable.

## The `audio` element

`<audio>` works the same way minus the picture. Always include `controls`; without it nothing is displayed at all.

```html-run
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Audio element</title>
<style> figure { margin: 0; } figcaption { font-weight: bold; margin-bottom: .4rem; } </style></head>
<body>
  <figure>
    <figcaption>Episode 12: Tide tables explained</figcaption>
    <audio controls preload="metadata">
      <source src="episode-12.opus" type="audio/ogg; codecs=opus">
      <source src="episode-12.mp3" type="audio/mpeg">
      <a href="episode-12.mp3">Download episode 12 (MP3)</a>
    </audio>
  </figure>
  <p><a href="#transcript">Read the transcript</a></p>
</body>
</html>
```

MP3 plays everywhere. AAC (in an `.m4a` file) and Opus give better quality at the same size. As with video, a transcript is the accessible alternative.

### Choosing `preload`

| Value | Browser behaviour | Good for |
|---|---|---|
| `none` | Fetch nothing until the user presses play | Pages with many players; saving mobile data |
| `metadata` | Fetch only enough to know duration and dimensions | The sensible default |
| `auto` | May download the whole file | The one item the visitor certainly came to play |

It is a hint; browsers may ignore it on metered connections.

## Embedding other pages: `<iframe>`

An **inline frame** displays a separate HTML document inside a rectangle of your page. This is how maps, hosted videos, payment forms and code playgrounds are embedded. In fact the live examples on this page each run in a sandboxed iframe.

```html-run
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>iframe</title>
<style>
  iframe { border: 2px solid #5e35b1; border-radius: 8px; width: 100%; max-width: 420px; height: 150px; }
</style></head>
<body>
  <p>The purple box below is a complete, separate document:</p>
  <iframe title="Mini weather widget" loading="lazy"
    srcdoc="<body style='font-family:sans-serif;background:#ede7f6;margin:1rem'><h3 style='margin:0'>Harbour weather</h3><p>12°C, light breeze from the west.</p></body>">
  </iframe>
</body>
</html>
```

Key attributes:

| Attribute | Purpose |
|---|---|
| `src` | URL of the document to embed |
| `srcdoc` | Inline HTML to use instead of a URL |
| `title` | **Required for accessibility**: describes the frame's content |
| `width`, `height` | Size in CSS pixels (defaults to 300 by 150) |
| `loading="lazy"` | Defer loading until the frame nears the viewport |
| `allow` | Permissions policy: `allow="fullscreen; geolocation"` |
| `sandbox` | Restrict what the framed page may do |
| `referrerpolicy` | Control what referrer information is sent |

The framed document has its own DOM, its own styles and its own scripts. Your CSS does not reach inside it, and (for a different origin) neither does your JavaScript.

### Security

Embedding third-party content means running someone else's code inside your page, so apply the principle of least privilege.

- **`sandbox`** with no value applies every restriction: no scripts, no forms, no pop-ups, and the content is treated as a unique origin. Add back only what is needed, for example `sandbox="allow-scripts allow-forms"`. Avoid combining `allow-scripts` with `allow-same-origin` for content you do not control, because together they let the frame remove its own sandbox.
- **`allow`** grants powerful features (camera, microphone, geolocation, fullscreen) explicitly.
- In the other direction, a site can forbid *being* framed, using the HTTP response header `Content-Security-Policy: frame-ancestors 'none'`. That is the defence against **clickjacking**, where an attacker overlays your page invisibly and tricks users into clicking it.

> [!INTERVIEW]
> "What are the costs of an iframe?" Each one is a whole extra document: its own network requests, memory and script execution. It is opaque to your CSS, awkward to size responsively, and a security boundary you must configure with `sandbox` and `allow`. Add `loading="lazy"` and a `title` every time.

### Making embeds responsive

Hosted video players typically hand you an iframe with fixed pixel dimensions. The CSS `aspect-ratio` property keeps the shape as the width changes:

```html-run
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Responsive embed</title>
<style>
  .embed { width: 100%; max-width: 480px; aspect-ratio: 16 / 9; border: 0; border-radius: 10px;
           background: linear-gradient(135deg, #00838f, #1a237e); }
  .wrap { resize: horizontal; overflow: auto; border: 1px dashed #999; padding: 6px; width: 70%; }
</style></head>
<body>
  <p>Resize the dashed box; the frame keeps its 16:9 shape.</p>
  <div class="wrap">
    <iframe class="embed" title="Placeholder for a hosted video player"
      srcdoc="<body style='margin:0;display:grid;place-items:center;height:100vh;color:white;font-family:sans-serif'>16 : 9 player</body>"></iframe>
  </div>
</body>
</html>
```

The same `aspect-ratio` rule works on `<video>` and on any placeholder box.

## Drawing surfaces: `canvas` and SVG

Two technologies took over the graphics work once done in Flash.

| | `<canvas>` | SVG |
|---|---|---|
| Model | A bitmap you paint on with JavaScript | A tree of shape elements |
| After drawing | Pixels only; nothing to select | Each shape is a DOM node you can style and listen to |
| Scales | Blurs unless redrawn | Perfectly |
| Best for | Games, image processing, thousands of moving points | Icons, logos, charts, diagrams |
| Accessibility | Needs fallback content or ARIA | Text is real text; add `<title>` or `aria-label` |

```html-run
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Canvas and SVG</title>
<style> canvas, svg { border: 1px solid #bbb; vertical-align: top; } </style></head>
<body>
  <canvas id="c" width="200" height="120">A sine wave drawn in blue.</canvas>
  <svg width="200" height="120" viewBox="0 0 200 120" role="img" aria-label="Three overlapping circles">
    <circle cx="70" cy="60" r="40" fill="#ef5350" opacity=".7"/>
    <circle cx="100" cy="60" r="40" fill="#42a5f5" opacity=".7"/>
    <circle cx="130" cy="60" r="40" fill="#66bb6a" opacity=".7"/>
  </svg>
  <script>
    const ctx = document.getElementById('c').getContext('2d');
    ctx.strokeStyle = '#1565c0'; ctx.lineWidth = 3; ctx.beginPath();
    for (let x = 0; x <= 200; x++) ctx.lineTo(x, 60 + 40 * Math.sin(x / 16));
    ctx.stroke();
  </script>
</body>
</html>
```

The text between the `<canvas>` tags is fallback content, exposed to assistive technology and shown where canvas is unsupported.

## How the browser chooses what to play

```mermaid
flowchart TD
    A[Parse video element] --> B{src attribute present?}
    B -- yes --> C[Try that file]
    B -- no --> D[Read first source child]
    D --> E{Can play this type?}
    E -- yes --> C
    E -- no --> F{Another source?}
    F -- yes --> D
    F -- no --> G[Show poster with error state]
    C --> H{preload setting}
    H -- none --> I[Wait for user to press play]
    H -- metadata --> J[Fetch duration and size only]
    H -- auto --> K[Buffer ahead]
```

> [!TIP]
> Before publishing a video, watch it once with the sound off and the captions on. If you cannot follow it, neither can a deaf viewer or anyone in a quiet office.

## Pitfalls

- **No `controls` on audio.** The element is invisible and unusable.
- **Expecting autoplay with sound.** It is blocked. Use `muted` or wait for a user gesture.
- **Missing `type` on `<source>`.** The browser must begin downloading each file to find out whether it can play it.
- **Only one format.** Offer a modern codec first and H.264/MP4 as the fallback.
- **No captions or transcript.** A legal as well as an ethical problem for public sites.
- **Animated GIFs for video.** A muted, looping `<video>` is often a tenth of the size.
- **Iframe without `title`.** Screen readers announce only "frame".
- **Third-party iframe with no `sandbox` or `allow` consideration.** You have handed over more capability than necessary.
- **Fixed-size embeds.** They overflow on phones; use `width: 100%` and `aspect-ratio`.
- **Following obsolete advice.** `<object>`, `<embed>`, `<applet>` and Flash fallbacks are no longer needed for media.

## Cheat sheet

| Goal | Markup |
|---|---|
| Play a video | `<video controls width height poster>` + `<source>` list |
| Silent looping background clip | `autoplay muted loop playsinline` (and a pause control) |
| Captions | `<track kind="captions" src srclang label default>` |
| Play audio | `<audio controls>` + `<source>` list |
| Save data | `preload="none"` or `"metadata"` |
| Embed a page | `<iframe src title loading="lazy">` |
| Restrict an embed | `sandbox`, `allow`, `referrerpolicy` |
| Keep 16:9 shape | `aspect-ratio: 16 / 9; width: 100%` |
| Scriptable bitmap | `<canvas>` with fallback text |
| Scalable shapes | Inline `<svg>` with `role="img"` and a label |

## Summary

Plug-ins are gone; media is native. `<video>` and `<audio>` take a list of `<source>` files so each browser can pick a codec it supports, expose built-in controls, and accept `<track>` elements for captions and subtitles. Autoplay works only when muted, and moving content needs a pause mechanism. `<iframe>` embeds another document and must be titled, sized responsively and locked down with `sandbox` and `allow`. For graphics, choose `canvas` when you need to paint many pixels quickly and SVG when you want resolution-independent shapes that live in the DOM.

## Glossary

| Term | Meaning |
|---|---|
| Plug-in | Separate software, such as the retired Flash Player, that browsers once needed to play media |
| `<video>` / `<audio>` | Elements that play media files natively in the browser |
| Container format | The file type that holds the media streams, such as MP4 or WebM |
| Codec | The method used to compress and decompress video or audio, such as H.264 or Opus |
| `<source>` | A child element offering one of several alternative media files |
| Fallback content | What is shown when the browser cannot use the main content |
| Autoplay | Starting playback without the user asking; allowed only when muted |
| Captions | On-screen text of the speech and significant sounds, for people who cannot hear |
| Subtitles | A translation of the dialogue for people who can hear but do not know the language |
| WebVTT | The plain-text file format for timed captions and subtitles |
| Transcript | The full text of a recording, published alongside it |
| `<iframe>` | An element that displays another HTML document inside the page |
| Sandbox | A set of restrictions limiting what embedded content may do |
| Clickjacking | An attack that tricks users into clicking a hidden framed page |
| `<canvas>` | A blank drawing surface that JavaScript paints on |

## Check yourself

```quiz
[
  {"q": "A video has two source children: WebM first, MP4 second. A browser supports both. What does it do?", "options": ["Downloads both and plays the smaller", "Plays the WebM and never requests the MP4", "Plays the MP4 because it is more compatible", "Shows the fallback content"], "answer": 1,
   "explain": "Sources are tried in order and the first playable one wins; later sources are not downloaded."},
  {"q": "Which attribute combination allows a video to start automatically in current browsers?", "options": ["autoplay", "autoplay controls", "autoplay muted", "autoplay loop"], "answer": 2,
   "explain": "Audible autoplay is blocked by policy. Muted autoplay is permitted (iOS also needs playsinline to stay in the page)."},
  {"q": "What is the difference between kind='captions' and kind='subtitles'?", "options": ["They are synonyms", "Captions include non-speech sounds for viewers who cannot hear; subtitles translate dialogue for those who can", "Subtitles are burned into the video", "Captions are only for audio elements"], "answer": 1,
   "explain": "Captions assume the audio is unavailable and so describe sound effects and music as well as speech."},
  {"q": "What does this render? <audio src='song.mp3'></audio>", "options": ["A player with default controls", "Nothing visible", "A download link", "The file name"], "answer": 1,
   "explain": "Without the controls attribute an audio element has no visual presence."},
  {"q": "Which iframe attribute is essential for screen-reader users?", "options": ["name", "title", "frameborder", "scrolling"], "answer": 1,
   "explain": "The title gives the frame an accessible name so users know what it contains before entering it."},
  {"q": "What does sandbox (with an empty value) do to an iframe?", "options": ["Nothing", "Applies all restrictions: no scripts, forms, pop-ups, and a unique origin", "Makes it load lazily", "Prevents it from being resized"], "answer": 1,
   "explain": "An empty sandbox is the most restrictive setting; you then opt back in to individual capabilities with tokens like allow-scripts."},
  {"q": "You must draw 20,000 animated particles sixty times a second. Which technology suits best?", "options": ["Inline SVG with one element per particle", "canvas", "A table with coloured cells", "An animated GIF"], "answer": 1,
   "explain": "Canvas paints pixels directly with no per-shape DOM overhead, which is what large, fast-changing scenes need."}
]
```

> **Source:** Duckett, *HTML & CSS*, ch. 9 (Flash, Video & Audio) and the iframe section of ch. 8. MDN: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/video · https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/track · https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe · https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay
