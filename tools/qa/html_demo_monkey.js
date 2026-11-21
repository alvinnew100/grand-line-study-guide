async (page) => {
  // Interaction test for html-run demos: use every control in each demo frame, record errors and
  // demos whose controls change nothing. RANGE selects which lessons to run in this call.
  const RANGE = [0, 28];
  const lessons = [["html-css","how-pages-work"],["html-css","text-markup"],["html-css","lists-links"],["html-css","images"],["html-css","tables"],["html-css","media-embeds"],["html-css","forms"],["html-css","form-validation"],["html-css","ids-classes-meta"],["html-css","semantic-structure"],["html-css","accessibility"],["html-css","css-intro"],["html-css","cascade"],["html-css","color"],["html-css","typography"],["html-css","box-model"],["html-css","lists-tables-forms-css"],["html-css","backgrounds-images"],["html-css","display-positioning"],["html-css","flexbox"],["html-css","grid"],["html-css","responsive"],["html-css","custom-properties"],["html-css","transitions-animations"],["html-css","css-architecture"],["html-css","rendering-performance"],["html-css","process-seo-hosting"],["html-css","interview-essentials"],["javascript","callbacks-promises"],["javascript","async-await-generators"],["javascript","event-loop-microtasks"],["javascript","browser-dom-tree"],["javascript","changing-document"],["javascript","event-handling"],["javascript","keys-pointers-timers"],["javascript","canvas-drawing"],["javascript","project-platform-game"],["javascript","http-fetch-forms"],["javascript","project-pixel-editor"],["javascript","interview-async-utilities"],["js-testing","unobtrusive-feature-detection"],["js-testing","dom-client-tdd"],["js-testing","testing-library-playwright"],["nodejs","universal-ssr"],["react","why-react-vite"],["react","jsx-components-props"],["react","lists-keys-events"],["react","usestate"],["react","lifting-controlled"],["react","composition-conditional"],["react","useeffect"],["react","custom-hooks-refs"],["react","class-components"],["react","data-fetching"],["react","usereducer"],["react","forms"],["react","memoization"],["react","styling"],["react","testing"],["react","structure-profiling"],["react","sort-search-paginate"],["react","routing"],["react","context-global-state"],["react","suspense-boundaries-rsc"],["react","virtual-dom"],["react","render-commit"],["react","firebase-setup-auth"],["react","sessions-roles"],["react","firestore-rtdb"],["react","security-rules"],["react","interview-builds"],["behavioural","star-in-depth"],["behavioural","i-data-length"],["behavioural","story-bank"],["behavioural","follow-up-probes"],["behavioural","remote-and-questions"],["behavioural","offers-singapore"],["jira","kanban"],["jira","jql-basics"],["jira","interview-readiness"]];
  const p = await page.context().newPage();
  let cur = ''; const errs = []; const report = [];
  p.on('pageerror', (e) => errs.push(cur + ' | pageerror: ' + String(e).slice(0, 150)));
  p.on('console', (m) => { if (m.type() === 'error') errs.push(cur + ' | console: ' + m.text().slice(0, 150)); });
  p.on('dialog', (d) => d.dismiss().catch(() => {}));
  let demos = 0, withControls = 0;
  try {
    await p.goto('http://localhost:8765/?monkey=' + Date.now(), { waitUntil: 'load' });
    for (const [t, l] of lessons.slice(RANGE[0], RANGE[1])) {
      await p.evaluate((h) => { location.hash = h; }, '#/lesson/' + t + '/' + l);
      await p.waitForTimeout(2200);
      const frames = p.frames().filter((f) => f !== p.mainFrame() && f.url().startsWith('about:srcdoc'));
      for (let fi = 0; fi < frames.length; fi++) {
        const f = frames[fi]; cur = t + '/' + l + '#' + (fi + 1); demos++;
        try {
          const snap = () => f.evaluate(() => document.body ? document.documentElement.outerHTML + ':' + document.body.innerText.slice(0, 3000) + ':' + [...document.querySelectorAll('*')].slice(0, 400).map((e) => { const c = getComputedStyle(e); return c.transform + c.backgroundColor + c.display + c.width; }).join(';') + ':' +
            [...document.querySelectorAll('input,textarea,select')].map((e) => e.value + e.checked).join('|') + ':' +
            [...document.querySelectorAll('canvas')].map((c) => { try { return c.toDataURL().length; } catch (e) { return 0; } }).join(',') : '');
          const before = await snap();
          let acted = 0;
          for (const el of await f.$$('input[type=text],input:not([type]),input[type=number],input[type=search],input[type=email],textarea')) {
            try { await el.fill('42', { timeout: 400 }); await el.press('Enter', { timeout: 400 }); acted++; } catch (e) {}
          }
          for (const el of await f.$$('input[type=range]')) {
            try { await el.evaluate((e) => { e.value = e.max || 10; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }); acted++; } catch (e) {}
          }
          for (const el of await f.$$('select')) {
            try { await el.evaluate((e) => { if (e.options.length > 1) { e.selectedIndex = e.options.length - 1; e.dispatchEvent(new Event('change', { bubbles: true })); } }); acted++; } catch (e) {}
          }
          for (const el of await f.$$('input[type=checkbox],input[type=radio]')) { try { await el.click({ timeout: 400 }); acted++; } catch (e) {} }
          for (const el of (await f.$$('button')).slice(0, 12)) { try { await el.click({ timeout: 400 }); acted++; await f.waitForTimeout(60); } catch (e) {} }
          for (const el of await f.$$('canvas')) { try { await el.click({ timeout: 400 }); acted++; } catch (e) {} }
          if (await f.$('canvas')) { try { for (const k of ['ArrowRight', 'ArrowUp', 'ArrowLeft', ' ']) await p.keyboard.press(k); } catch (e) {} }
          await f.waitForTimeout(500);
          const after = await snap();
          if (acted) { withControls++; if (before === after) report.push(cur + ' | ' + acted + ' controls used, nothing changed'); }
        } catch (e) { report.push(cur + ' | frame error: ' + String(e).slice(0, 100)); }
      }
    }
  } finally { await p.close(); }
  return { range: RANGE, demos, withControls, noChange: report, errors: errs.slice(0, 40), errorCount: errs.length };
}
