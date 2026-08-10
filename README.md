<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./portrait-dark.svg">
    <img src="./portrait.svg" width="460" alt="An ASCII portrait that types itself out, one row at a time">
  </picture>
</p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./hd-whoami-dark.svg">
  <img src="./hd-whoami.svg" width="860" alt="whoami">
</picture>

> Everything on this page is drawn by this repository. No third-party widgets,<br>
> no image host that can rate-limit or go dark, nothing here that stops working<br>
> because somebody else's free tier ran out.

REWRITE ME. Two or three lines about what you actually work on, hard-wrapped at<br>
about 76 characters so the measure stays readable. Full-width paragraphs on<br>
GitHub run to roughly 110 characters, which is a genuinely bad line length.

<samp>python · typescript · c++ · html</samp>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./hd-signal-dark.svg">
  <img src="./hd-signal.svg" width="860" alt="signal">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./stats-dark.svg">
  <img src="./stats.svg" width="860" alt="Contribution totals for the last 365 days, with a weekly sparkline">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./streak-dark.svg">
  <img src="./streak.svg" width="860" alt="Current streak, longest streak, and active days">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./year-dark.svg">
  <img src="./year.svg" width="860" alt="The last 365 days, one character per day">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./hd-stack-dark.svg">
  <img src="./hd-stack.svg" width="860" alt="stack">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./langs-dark.svg">
  <img src="./langs.svg" width="860" alt="Languages by bytes written across public repositories">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./hd-contact-dark.svg">
  <img src="./hd-contact.svg" width="860" alt="contact">
</picture>

<samp>
  <a href="mailto:YOUR-EMAIL">email</a> ·
  <a href="https://YOUR-SITE">site</a> ·
  <a href="https://www.linkedin.com/in/YOUR-HANDLE">linkedin</a>
</samp>

<details>
  <summary><samp>how this page works</samp></summary>

<br>

The portrait is one SVG. Each row of characters sits in a `clipPath` whose
rectangle animates from zero width to full, with a small block riding the wipe
edge as a cursor. Rows stagger top to bottom, and every animation is
`fill="freeze"`, so it prints once and stops.

The four graphics below it are redrawn every night by a scheduled action that
queries the GitHub GraphQL API and commits the result, but only when a number
actually changed. The generator uses nothing outside the Python standard
library.

Both carry their own font, base64-inlined, because an SVG loaded through an
`img` tag cannot fetch a subresource. Without that, the portrait grid would
shear on any machine whose default monospace is not exactly 0.600 em wide.

Code is in `scripts/`. Take any of it.

</details>
