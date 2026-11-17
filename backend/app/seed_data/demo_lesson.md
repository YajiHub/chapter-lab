Client-side rendering sends the browser a basic page and JavaScript. The browser builds the interface and may fetch data after loading. This can suit a signed-in dashboard with frequent interaction, especially after its initial load.

Server-side rendering generates HTML when a request arrives. It can present current content in the initial response. It requires server work for each request unless a cache handles the request.

Static site generation prepares HTML at build time. Requests can receive already generated files without rendering each page on demand. A public guide that rarely changes is a good fit. Content changes appear after a rebuild or another supported refresh mechanism.

Hydration attaches client-side event handlers to HTML already rendered by the server or build process. A page may display its content before JavaScript makes some controls interactive.

For a stable help page, a developer should consider static generation. For a public page displaying information that must be current when requested, server-side rendering is a better fit under those assumptions. For a frequently used interactive dashboard behind sign-in, client-side rendering can be a reasonable choice.
