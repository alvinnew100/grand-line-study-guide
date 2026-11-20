// Runs a JavaScript reference solution on test arguments (used by build.py). Input: JSON on stdin.
let s = "";
process.stdin.on("data", (d) => (s += d)).on("end", () => {
  const { code, entry, tests } = JSON.parse(s);
  const quiet = { log() {}, info() {}, warn() {}, error() {}, debug() {}, table() {} };
  let fn;
  try { fn = new Function("console", code + String.fromCharCode(10) + ";return (typeof " + entry + " !== 'undefined') ? " + entry + " : null;")(quiet); }
  catch (e) { console.log(JSON.stringify({ fatal: String(e) })); return; }
  if (typeof fn !== "function") { console.log(JSON.stringify({ fatal: "no function named " + entry })); return; }
  const out = tests.map((a) => {
    try { let g = fn(...JSON.parse(JSON.stringify(a))); if (g === undefined) g = null; return { got: JSON.parse(JSON.stringify(g)) }; }
    catch (e) { return { error: String(e) }; }
  });
  console.log(JSON.stringify(out));
});
