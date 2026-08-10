# Setup

Everything in this folder is the contents of your GitHub profile repository.
The repo has to be named exactly your GitHub username, and it has to be public.

Current state: the headings and a **placeholder portrait** are built and
committed. The four data graphics are not, because they contain real numbers
and inventing those would be worse than a missing image. Step 4 creates them.

---

## 1. Create the repo

```bash
gh repo create <your-username> --public --clone
```

Copy everything in this folder into it. Then:

```bash
cd <your-username>
git add . && git commit -m "profile: initial"
```

Do not push yet.

---

## 2. Replace the placeholder portrait

`portrait.svg` currently shows a synthetic test shape, generated to prove the
pipeline runs. Replace it with yours.

```bash
pip install pillow numpy opencv-python-headless rembg onnxruntime
python3 scripts/make_portrait.py photo/you.jpg
```

The first run downloads a background-removal model, about 176 MB. Once, then
cached.

**The photo decides everything.** No amount of parameter tuning rescues a bad
input, because ASCII draws with shadow, not detail, and there are only 13
brightness levels to work with.

| Do | Why |
| --- | --- |
| Side light, a window at roughly 45 degrees, everything else off | Flat frontal light gives one uniform mid-tone and the face renders as a hole |
| Crop tight, chin to just above the hair | At 90 columns a face filling 30% of the frame gets about 30 characters across, and the eyes will not resolve |
| 1200px or larger | Thin features like glasses frames get averaged away when a small source is downscaled |
| Plain background | Anything busy survives the cut-out as noise |
| Slight angle, not dead-on | Gives the nose and jaw a shadow edge |

The script prints an ink density. Below about 20% the portrait is washed out,
above about 62% it is a blob. Fix either with `--gamma`:

```bash
python3 scripts/make_portrait.py photo/you.jpg --gamma 2.1   # washed out
python3 scripts/make_portrait.py photo/you.jpg --gamma 1.4   # too dark
```

Look at the result before moving on. Open `portrait.svg` in a browser directly;
it will type itself out once and stop.

---

## 3. Optional: swap in JetBrains Mono

The subsets in `assets/fonts/subsets/` are currently built from Noto Sans Mono,
which is OFL and has exactly the 0.600 em advance the portrait grid assumes. If
you would rather use JetBrains Mono:

```bash
bash scripts/fetch_fonts.sh
python3 scripts/build_fonts.py
python3 scripts/make_portrait.py photo/you.jpg     # re-render with the new font
python3 scripts/make_headings.py
```

`build_fonts.py` measures the advance width and warns you if the font is wrong.
Ubuntu Mono is 0.560 and Consolas is about 0.55; either would show your
portrait roughly 7% narrower than you see it.

---

## 4. Generate the real stats

Two ways. Either works, and both produce identical bytes.

A word on what gets counted. The workflow's built-in `GITHUB_TOKEN` is
repo-scoped, so the totals cover **public contributions only**. Turning on
"Include private contributions on my profile" in GitHub settings does not change
this: that setting governs what your profile page displays, while the token
governs what the API will hand over. Measured on this account, the profile
showed 124 contributions for the year while the workflow reported 68.

If you want private work counted, create a classic personal access token with
the `repo` scope, save it as a repository secret named `STATS_TOKEN`, and the
workflow uses it automatically. That buys accuracy at the cost of a credential
to rotate, which is why it is opt-in.

**Locally**, to see them before anyone else does:

```bash
export GH_LOGIN=<your-username>
export GITHUB_TOKEN=$(gh auth token)
python3 scripts/generate_stats.py
```

**Or in Actions**, after pushing: Actions tab, "refresh stats", Run workflow.

---

## 5. Fill in the identity bits

`README.md` has four placeholders. Search for them:

- `YOUR-EMAIL`
- `YOUR-SITE`
- `YOUR-HANDLE`

and the two prose paragraphs under `whoami`, which are written as a plausible
default rather than as your actual sentences. Rewrite them.

If you change the section names, edit `WORDS` in `scripts/make_headings.py` and
`HEADING_CHARS` in `scripts/build_fonts.py` together, then rebuild both. The
heading subset only contains the letters those words use, so a new word with a
new letter renders as a missing glyph.

---

## 6. Check, then push

```bash
python3 scripts/verify.py
```

This checks that every SVG parses, that none of them reaches out to the network,
that every embedded font decodes as real woff2, that no animation loops, and
that the README only uses markup GitHub's sanitiser keeps.

```bash
git add . && git commit -m "profile: real content" && git push
```

---

## What GitHub actually allows

This dictated every decision above. Established by posting markdown to GitHub's
own rendering endpoint (`POST /markdown`) and reading back what survived.

```
STRIPPED
  <style> blocks        style=" " attributes      class=" "
  inline <svg>          <font>   <small>   <big>

KEPT
  <sub>  <sup>  <kbd>  <samp>  <blockquote>  <details>  <hr>  <picture>
  align=" "     width=" " on <img> and <td>
```

Three consequences:

1. **You cannot change the font of README text.** Not with CSS, not with a
   `font` tag, not with inline SVG. Your only choice is GitHub's sans or its
   monospace. Anything in your own typeface has to be an image.
2. **Motion must live inside the SVG, and must never be load-bearing.** Scripts
   are stripped, so animation has to be SMIL, `animate` and `set` elements,
   inside the file. But GitHub renders these SVGs with SMIL halted, at least in
   the blob preview and in a fresh README render, so whatever the base attribute
   says is what the world sees.

   This was established with a probe committed to the repo: a static `clipPath`
   next to an animated one, otherwise identical. The static row drew, the
   animated row did not. `clipPath` survives sanitisation, `<style>` survives,
   the inlined `@font-face` survives; only the animation fails to advance.

   So every animated attribute here has its **finished** value as its base
   value, and the animation only replays it. Open `portrait.svg` directly in a
   browser and it types itself out; put it in a README and it is simply there.
   Anything that animates from zero and has a base of zero is invisible on the
   one page where a blank image is most expensive. `verify.py` now fails on it.
3. **An external font URL cannot work.** These SVGs load through an `img` tag,
   and browsers refuse subresource fetches for image documents. A `@font-face`
   with a base64 data URI does work, which is why every SVG carries its own
   copy of the font.

---

## Why not the usual stats cards

Most profile READMEs pull their graphics from someone else's server. Two things
go wrong with that. They break: `github-readme-stats.vercel.app` has returned
503 for hours at a stretch, and its common replacement answers `ERROR!!! Cards
are temporarily rate limited`. Your profile is the one page where a broken
image is most expensive. And you cannot design them: you get somebody's theme
list, so the page looks like five things instead of one.

---

## Design notes worth keeping

**Columns for daily data, lines for weekly.** The default activity graph is a
line chart over daily counts, which is wrong, because daily contributions are
sparse and discrete. A line through `0, 0, 11, 0, 0, 10` claims values that
never existed. The year grid uses one character per day and an empty day is
empty space. The sparkline aggregates to weeks first, where continuity is
defensible.

**One fill colour.** Per-character rainbow colouring is what makes most ASCII
portraits look like static.

**Two determinism traps**, both handled in `generate_stats.py`, both of which
otherwise produce a commit every single night:

1. The contribution window is pinned to whole UTC days. Left alone,
   `contributionsCollection` measures "the past year" from the moment of the
   request, so two runs minutes apart bucket days into different weeks and shift
   the sparkline by a fraction of a pixel.
2. Repositories are filtered to `privacy: PUBLIC`. Your personal token sees
   private repos and the workflow's token does not, so the language percentages
   would disagree depending on who ran the script.

**Let the action own the generated files.** Once it is running, do not
regenerate `stats.svg` and friends locally as well. Merge conflicts otherwise
are guaranteed near a week boundary.

---

## Gotchas

- **A newly created profile README is cached.** If it does not appear on your
  profile, edit it once through the web UI to force a refresh.
- **Pinned repositories and your bio cannot be set through the API.** No
  GraphQL mutation exists, and the REST call needs a `user` scope your CLI token
  will not have. Both are manual, in the UI.
- **A full-page screenshot restarts SMIL.** If you verify with headless Chrome,
  `fullPage: true` produces blank animated SVGs. Use a tall viewport instead,
  and wait: a 43-row portrait takes about 4.3 s to finish typing.
- **Image headings have no anchor links**, so GitHub's README outline goes
  empty. The `alt` text carries the word for screen readers. That is the trade.
- **The `<picture>` light/dark switch follows your GitHub theme setting.** A
  media query inside an `<img>`-loaded SVG would follow the OS setting instead,
  which is why there are two files per graphic rather than one clever one.

---

## Files

```
README.md                      the profile page
scripts/svgkit.py              shared drawing helpers, palette, font inlining
scripts/build_fonts.py         subset the typeface into four roles
scripts/fetch_fonts.sh         optional, downloads JetBrains Mono
scripts/make_portrait.py       photo -> ASCII -> self-typing SVG
scripts/make_headings.py       section headings as SVG
scripts/generate_stats.py      GraphQL -> four graphics, stdlib only
scripts/preview_mock.py        render everything from fake data
scripts/verify.py              pre-flight checks
.github/workflows/             nightly refresh, commits only on change
assets/fonts/subsets/          the committed woff2 subsets, 12.8 KB total
```

Credit: the portrait pipeline comes from the ASCII Portrait README Guide,
`burly-handstand-0dc.notion.site/ASCII-Portrait-README-Guide-3a3e3f86338481f0b545ec8120bbf604`,
by way of `agreeable-credit-859.notion.site/A-GitHub-profile-that-generates-itself-3abedfe9a65a81e4afc9daed90cb4e7e`.
