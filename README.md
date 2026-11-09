# victor-mobo.github.io

Personal site, built by `build.py` and deployed by GitHub Actions on every push to `main`.

## Updating the site
| To add | Do this |
|---|---|
| Paper | Copy `content/research/_example.md` to `content/research/<name>.md`, edit, drop the PDF in `files/` |
| Course | Same, in `content/teaching/` |
| CV | Replace `files/cv.pdf` |
| Home text | `content/home.md`; name/links in `site.yml` |

Then run `./publish.sh "message"`. Preview first with `make serve`.
Files starting with `_` are ignored; `draft: true` hides an entry.
