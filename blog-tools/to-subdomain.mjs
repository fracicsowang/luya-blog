import fs from "fs";
import path from "path";

// 1) source files: /blog/ -> /, fix base concatenations for base="/"
const srcFiles = [];
(function walk(d) {
  for (const f of fs.readdirSync(d)) {
    const p = d + "/" + f;
    if (fs.statSync(p).isDirectory()) walk(p);
    else if (/\.(astro|ts)$/.test(f)) srcFiles.push(p);
  }
})("site-src/src");
for (const p of srcFiles) {
  let s = fs.readFileSync(p, "utf8");
  const o = s
    .replaceAll("/blog/", "/")
    .replaceAll('import.meta.env.BASE_URL + "/"', '"/"')
    .replaceAll('base + "/"', '"/"');
  if (o !== s) { fs.writeFileSync(p, o); console.log("src:", path.basename(p)); }
}

// 2) drafts: image paths, internal links to root, main-site links absolute
let n = 0;
for (const f of fs.readdirSync("blog-drafts").filter((f) => f.endsWith(".md"))) {
  let s = fs.readFileSync("blog-drafts/" + f, "utf8");
  let o = s
    .replaceAll("/blog/img/", "/img/")
    .replaceAll("](/how-it-works)", "](https://luyaxyz.com/how-it-works)")
    .replaceAll("](/)", "](https://luyaxyz.com/)")
    .replaceAll("](/blog/", "](/");
  if (o !== s) { fs.writeFileSync("blog-drafts/" + f, o); n++; }
}
console.log("drafts rewritten:", n);

// 3) resolve_internal_links.py: change /blog/<slug>/ matching to /<slug>/
let py = fs.readFileSync("blog-tools/resolve_internal_links.py", "utf8");
py = py.replaceAll("/blog/([a-z0-9-]+)", "/([a-z0-9-]+)");
fs.writeFileSync("blog-tools/resolve_internal_links.py", py);
console.log("patched resolve_internal_links regex");
