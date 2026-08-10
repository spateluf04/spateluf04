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

> Junior CS at the University of Florida. Most of what I build starts at the<br>
> hardware or the raw sensor data and ends at something a person can use.

Lately that has meant pulling fingertip trajectories out of smart-glasses<br>
recordings, building a rules engine that decides whether a prescription is safe<br>
before any model is allowed an opinion, and a C++ co-purchase graph that turned<br>
out to be the most interesting part of a data structures course. Currently<br>
poking at energy systems, mobile apps, and open source.

<samp>python · typescript · c++ · react · react native · firebase · fastapi</samp>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./hd-work-dark.svg">
  <img src="./hd-work.svg" width="860" alt="work">
</picture>

**[CleanVision](https://github.com/spateluf04/CleanVision)** &nbsp;<samp>python · pytorch · yolo · mediapipe</samp><br>
Air-writing recognition on Meta Project Aria Gen 1 glasses. Collects fingertip<br>
trajectories from offline VRS recordings, normalises them, trains an LSTM and a<br>
transformer encoder on the result, then runs the winner live against the<br>
headset's RGB stream. Ships a PyQt5 dashboard for capture and review.

**[The Pause Protocol](https://github.com/SamirOrgSWE/The-Pause-Protocol)** &nbsp;<samp>react native · expo · firebase</samp><br>
Mindfulness app that intercepts distracting app launches through iOS Shortcuts<br>
and makes you sit through a breathing countdown first. Firebase auth, a<br>
Firestore-backed quote database, and an admin role system. Team project.

**[DSA E-Commerce Engine](https://github.com/spateluf04/DSAProject2-ECommerce)** &nbsp;<samp>c++ · cmake · graphs</samp><br>
Command-line tool that ingests order, product and customer CSVs, benchmarks<br>
merge sort against quick sort on them, and builds a co-purchase graph from order<br>
history to answer "customers who bought this also bought" by nearest-neighbour<br>
query.

**RoomScan** &nbsp;<samp>python · projectaria_tools · wsl2</samp><br>
Energy-waste scanner on Meta Project Aria smart glasses: identifies appliances<br>
and estimates running cost on a live dashboard, with offline VRS sensor<br>
processing in WSL2. Third place at a UCF hackathon.

**PharmacyDash** &nbsp;<samp>fastapi · react · typescript · claude api</samp><br>
Clinical dashboard for catching over-prescription, built on a deliberate split:<br>
a deterministic rules engine (max dose, duplicate therapy, MME, age) makes every<br>
safety decision, while the model sits in an advisory layer that turns<br>
pharmacists' plain-English protocols into structured rules and explains flags. It<br>
never makes the clinical call. A de-identification boundary means only<br>
tokenised, non-PHI data crosses into the AI layer.

<sub>RoomScan and PharmacyDash have no public repository yet.</sub>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./hd-signal-dark.svg">
  <img src="./hd-signal.svg" width="860" alt="signal">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./stats-dark.svg">
  <img src="./stats.svg" width="860" alt="Contribution totals for the last 365 days, with a weekly sparkline">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./hd-stack-dark.svg">
  <img src="./hd-stack.svg" width="860" alt="stack">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./langs-dark.svg">
  <img src="./langs.svg" width="860" alt="Languages by bytes written across public repositories">
</picture>

<samp>
languages &nbsp;python · javascript / typescript · c++<br>
frameworks &nbsp;react · react native / expo · next.js · node · fastapi<br>
tools &nbsp;git · firebase / firestore · linux / wsl2 · vs code<br>
coursework &nbsp;data structures &amp; algorithms · operating systems · software engineering · linear algebra
</samp>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./hd-contact-dark.svg">
  <img src="./hd-contact.svg" width="860" alt="contact">
</picture>

<samp>
  <a href="mailto:sampatel0803@gmail.com">sampatel0803@gmail.com</a> ·
  <a href="https://github.com/spateluf04">github.com/spateluf04</a>
</samp>

<details>
  <summary><samp>how this page works</samp></summary>

<br>

Every image here is drawn by this repository. No third-party widgets, no image
host that can rate-limit or go dark, nothing that stops working because
somebody else's free tier ran out.

The portrait is one SVG. Each row of characters sits in a `clipPath` whose
rectangle animates from zero width to full, with a small block riding the wipe
edge as a cursor. Open the file directly and it types itself out once, then
stops. GitHub renders these images with SMIL halted, so every animated attribute
here has its finished value as its base value: the animation is an enhancement,
never the thing that makes the picture appear.

The four graphics below it are redrawn every night by a scheduled action that
queries the GitHub GraphQL API and commits the result, but only when a number
actually changed. The generator uses nothing outside the Python standard
library.

Both carry their own font, base64-inlined, because an SVG loaded through an
`img` tag cannot fetch a subresource. Without that, the portrait grid would
shear on any machine whose default monospace is not exactly 0.600 em wide.

Code is in `scripts/`. Take any of it.

</details>
