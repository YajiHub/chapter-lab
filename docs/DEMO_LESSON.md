# Demo lesson: Web rendering approaches

Use this original sample for the first generation request and live demo.

Client-side rendering sends the browser a basic page and JavaScript. The browser builds the interface and may fetch data after loading. This can suit a signed-in dashboard with frequent interaction, especially after its initial load.

Server-side rendering generates HTML when a request arrives. It can present current content in the initial response. It requires server work for each request unless a cache handles the request.

Static site generation prepares HTML at build time. Requests can receive already generated files without rendering each page on demand. A public guide that rarely changes is a good fit. Content changes appear after a rebuild or another supported refresh mechanism.

Hydration attaches client-side event handlers to HTML already rendered by the server or build process. A page may display its content before JavaScript makes some controls interactive.

For a stable help page, a developer should consider static generation. For a public page displaying information that must be current when requested, server-side rendering is a better fit under those assumptions. For a frequently used interactive dashboard behind sign-in, client-side rendering can be a reasonable choice.

## Evaluation anchors

A good question should distinguish when HTML is generated, match a scenario to a suitable approach, or explain why already visible content can briefly have inactive controls. A citation should point directly to the paragraph that supports that particular answer.
