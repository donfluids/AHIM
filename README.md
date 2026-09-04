# AHIM — Aron HaBrit International Ministries Website

A modern, mobile-friendly, single-page website for **Aron HaBrit International Ministries — Jesus Reigns Worship Center**, a multilingual church (Malayalam, English, Tamil, and Hindi) in Laurel, Maryland.

## What's included

- **`index.html`** — the entire site (HTML, CSS, and a few lines of JavaScript in one file; no build step, no dependencies).
  - Hero led by the church's verse (Isaiah 62:3), with service time and location at a glance
  - About section (church story and values)
  - Our Pastor section (Pastor Monish Stephen)
  - Service times (Sunday Worship, Saturday healing service, Friday prayer gathering, Tuesday/Thursday online prayer)
  - Events gallery built from the church's event flyers (`assets/events/`)
  - Watch Online section with an embedded YouTube service and links to the church's [YouTube channel](https://www.youtube.com/@AronHaBrit.International) and [Facebook page](https://www.facebook.com/AronHaBrit.International/)
  - Ministries overview
  - Plan Your Visit section with an embedded Google Map, address, email, and a Get Directions button
  - Footer with social links and contact details

## Updating content

Everything lives in `index.html` — open it in any text editor:

- **Service times** — search for `Service Times` and edit the `schedule-row` blocks.
- **Events** — each event is an `event` block; drop a new flyer image into `assets/events/` and copy one of the existing blocks.
- **The verse in the hero** — search for `Isaiah 62:3` and update the quote and reference when the church's verse changes.
- **Contact email / address** — search for `aronhabrit.international@gmail.com` or `116 St Marys Pl` and update everywhere they appear.
- **Service videos** — these look after themselves. See *Service videos update themselves* below.
- **Watch Live button** — points at `https://www.youtube.com/@AronHaBrit.International/live`, which YouTube sends straight to the current broadcast when the church is streaming.
- **Colors** — edit the CSS variables at the top of the `<style>` block (`--navy`, `--gold`, etc.).

## Service videos update themselves

The featured player and the three cards in the Watch Online section are not
edited by hand. `scripts/refresh_videos.py` reads the **Sunday Service**
playlist on the church's YouTube channel and rewrites them: the newest service
goes in the player, the next three go on the cards, and a thumbnail for each is
saved into `assets/videos/`. Thumbnails are copied into the repository rather
than linked to YouTube because the page only allows images the site serves
itself.

`.github/workflows/refresh-videos.yml` runs it once a day and commits only when
the playlist has actually moved on. Nothing needs doing after a service beyond
adding the video to the **Sunday Service** playlist as usual.

- **To refresh it right now** — GitHub → **Actions** → *Refresh service videos*
  → **Run workflow**. The site redeploys on its own afterwards.
- **If the videos ever stop updating** — GitHub switches off scheduled jobs in
  repositories that have had no activity for 60 days, and emails a warning
  first. Re-enable it from the Actions tab, or just run it by hand as above.
- **Service dates** come from the upload date, not the video title: services are
  uploaded on the Monday after, so the date shown is the Sunday before.
- **Card names** are taken from the start of each video title, so
  `DELIVERANCE SUNDAY | Pr. Shajan George | ...` becomes "Deliverance Sunday".
  Anything that opens with "Sunday Service" in any of its various spellings
  becomes "Sunday Service".

## Deploying with GitHub Pages (free)

This repo includes `.github/workflows/deploy-pages.yml`, which publishes the
site automatically on every push to `main`. If GitHub Pages has never been
enabled on this repository before, the very first run may need one manual
step:

1. In the GitHub repository, go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Push to `main` (or re-run the workflow from the **Actions** tab).

The site will be live at `https://<username>.github.io/ahim/` within a
couple of minutes. A custom domain (e.g. `aronhabritministries.org`) can be
pointed at GitHub Pages under the same settings page.
