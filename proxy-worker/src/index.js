// Reverse-proxy luyaxyz.com/blog/* -> luya-blog.pages.dev/blog/* (host swap).
// Runs only on the /blog routes; every other path hits the main (Lovable) site.
const ORIGIN = "https://luya-blog.pages.dev";
export default {
  async fetch(request) {
    const url = new URL(request.url);
    // normalize bare /blog -> /blog/
    if (url.pathname === "/blog") {
      return Response.redirect(url.origin + "/blog/", 301);
    }
    const target = ORIGIN + url.pathname + url.search;
    const resp = await fetch(new Request(target, request), { redirect: "manual" });
    return new Response(resp.body, resp);
  },
};
