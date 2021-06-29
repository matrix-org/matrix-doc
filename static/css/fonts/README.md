# Fonts

## Inter.css

`Inter.css` is a local copy of
https://fonts.googleapis.com/css?family=Inter:300,300i,400,400i,700,700i, modified to pull
font files (`.woff2`) from local sources. It was created
using `download_google_fonts_css.py`.
  
## download_google_fonts_css.py

`download_google_fonts_css.py` is a script that takes a google fonts CSS URL, downloads
the file and linked fonts, then saves the fonts locally along with a modified CSS file to
load them. Example call:

```sh
python3 download_google_fonts_css.py \
  "https://fonts.googleapis.com/css?family=Inter:300,300i,400,400i,700,700i" \
  ../../fonts \
  ../../fonts 
```
  
Which would pop out a `Inter.css` file that should be `@import url("Inter.css")`d
somewhere in the site's SCSS (currently in
[/assets/scss/_variables_project.scss](/assets/scss/_variables_project.scss)).

Re-running the script and committing any new files is only necessary when a desired 
font updates (not very often), or we want to change the font we're using. In that case,
remove the existing font files at `/static/fonts/*.woff2` and re-run the script with a
different URL.
