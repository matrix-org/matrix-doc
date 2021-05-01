
This document describes the components of the new spec platform, and the changes that have been made to the old spec content to make it work in the new platform.

## Hugo and Docsy

### Hugo

The spec is built into a web site using [Hugo](https://gohugo.io/). Hugo is a static site generator, distributed as a single Go binary. A Hugo installation typically has the following top-level directories:

* `/assets`: assets that need postprocessing using [Hugo Pipes](https://gohugo.io/hugo-pipes/introduction/). For example, Sass files would go here.

* `/content`: files that will become pages in the site go here. Typically these are Markdown files with some YAML front matter indicating, [among other things](https://gohugo.io/content-management/front-matter/), what layout should be applied to this page. The organization of files under `/content` determines the organization of pages in the built site.

* `/data`: this can contain TOML, YAML, or JSON files. Files kept here are directly available to template code as [data objects](https://gohugo.io/templates/data-templates/), so templates don't need to load them from a file and parse them.

* `/layouts`: this contains [Hugo templates](https://gohugo.io/templates/). Some templates define the overall layout of a page: for example, whether it has header, footer, sidebar, and so on.

    * `/layouts/partials`: these templates can be called from other templates, so they can be used to factor out template code that's used in more than one template. An obvious example here is something like a sidebar, where several different page layouts might all include the sidebar. But also, partial templates can return values: this means they can be used like functions, that can be called by multiple templates to do some common processing.
    * `/layouts/shortcodes`: these templates can be called directly from files in `/content`.


* `/static`: static files which don't need preprocessing. JS or CSS files could live here.

* `/themes`: you can use just Hugo or use it with a theme. Themes primarily provide additional templates, which are supplied in a `/themes/$theme_name/layouts` directory. You can use a theme but customise it by providing your own versions of any of the them layouts in the base `/layouts` directory. That is, if a theme provides `/themes/$theme_name/layouts/sidebar.html` and you provide `/layouts/sidebar.html`, then your version of this template will be used.

It also has the following top-level file:

* `config.toml`: site-wide configuration settings. Some of these are built-in and you can add your own. Config settings defined here are available in templates. All these directories above are configurable via `config.toml` settings.

Running `hugo serve` from the command line builds the site, starts a local server that serves it, and watches files for changes, rebuilding and reloadig pages if they change on disk. Sometimes this watching doesn't seem to work properly and we have to restart Hugo.  Calling `hugo serve --disableFastRender` is supposed to help with this.

What's nice about Hugo:
* fast to render pages
* popular, therefore unlikely to disappear any time soon
* single-binary install

What's not so nice:
* Hugo's templating language is harder to work with than something like Python or JS, and debugging templates is painful.

### Docsy

The spec uses the [Docsy](https://www.docsy.dev/) theme. Docsy is a theme for technical documentation written by Google. It seems well supported and has good documentation. It uses [Bootstrap](https://getbootstrap.com/) and [Font Awesome](https://fontawesome.com/), which get pulled in as Git submodules.

We've ended up not using very much of Docsy, and customising it a fair bit. So it might be worth extracting the bits we use and removing the rest. However I've not done this yet: instead I've used the normal mechanism for overriding the theme, which means we can treat Docsy as a black box.

## Our directory structure

This section lists each top-level directory in the repo and describes what it contains and what it does in the platform.

### /assets-hugo

This is the [Hugo assets](https://gohugo.io/hugo-pipes/introduction/) directory. Note that we're using "assets-hugo" rather than the default "assets": this is because the old spec platform used "assets" for the output of the site build process.

Our assets directory contains:
* the Matrix logo, which we're showing in the site header.
* Sass files we're using to customise the styles provided by our Hugo theme (Docsy):
     * `_variables_project.scss`: overrides some CSS variables and defines a couple of our own
     * `custom.scss`: custom styles for our site, mostly for special page elements things like the ToC and rendered data

### /changelogs

This contains a subdirectory for each API:

* `application_service`
* `client_server`
* `identity_service`
* `push_gateway`
* `server_server`

Under each of these is a `pyproject.toml` configuration file for [Towncrier](https://towncrier.readthedocs.io/en/actual-freaking-docs/index.html), and a `newsfragments` directory containing Towncrier-formatted entries, except written using Markdown rather than RST.

Note that this is almost exactly the same as in the old spec platform. The only differences are that we aren't using the *.rst files directly under `/changelogs`, and the newsfragments are written using Markdown, not RST.

This content is used to render the "Changelog" page of the spec.

### /content

This is where the specification's prose content lives. In Hugo "/content" is the default directory for page content, and by default MD files in here get published as web pages, with the URL structure mirroring the directory structure.

The content here is taken from the `/specification` directory in matrix-doc.
The main changes from the old spec content are:

* all prose is MD, not RST

* batesian template calls are replaced with Hugo template calls

* appendices are maintained in a single file, rather than each appendix getting its own file

* there's a new changelog.md, as the changelog is now its own page

* because Markdown (and HTML for that matter) doesn't support heading levels >6, some places that used H7 and even H8 have been reworked a little (see https://github.com/matrix-org/matrix-doc/pull/3002).

#### Handling client-server modules

As in the old spec (and following the discussion in https://github.com/matrix-org/matrix-doc/issues/2838), we maintain modules in separate files, under "client-server/modules". But I've included "feature_profiles" in the main client-server spec. Also, I've pushed the heading levels for module files down so they match their destination, rather than having to adjust heading levels in the build process.

Note that the arrangement here means that if you edit module files, you have to restart the local Hugo server to see the changes locally. This is unfortunate, and there is probably a better solution here.

### /data

This is where we keep specification data - OpenAPI data, event schemas and examples, and the "server-signatures.yaml" file.

By default, Hugo will let templates access YAML, JSON, or TOML files under "/data" directly as dictionaries, without the templates needing to load them as files: https://gohugo.io/templates/data-templates/. We take advantage of that feature here.

This data is taken from the following places in matrix-doc:

* "/api": OpenAPI specifications
* "/event-schemas": event schemas and examples
* "/schemas": the "server-signatures.yaml" file

I've made a few changes to this data:

* Many files under "/event-schemas" don't have an extension. Hugo complains if files under "/data" don't have an extension. So I've given (YAML) extensions to the data files that didn't have one.

* Because of this, I've had to change "$ref" schema values to include the extension.

* In the old spec, "/api/client-server/definitions" has a symlink to "/event-schemas". This doesn't work with accessing-data-as-objects, so I've removed the symlink and used relative paths in "$ref" values instead.

* In all data files, "description" fields contained RST. I've updated this to MD. Mostly this is a matter of updating links and `code` formatting, and rewriting `... Note` and `... Warning` directives. There are a couple of tables I had to rewrite.

* I've removed all files that aren't /data files. This includes:
    * all the code in "/api/files": that I guess is used to build the API playground? If we still want to support this we will need to find a home for it.

### /data-definitions

This contains only the sas-emoji stuff. I would have put this into "/data" as well, except we are not allowed to move it.

### /layouts

This contains Hugo templates.

There are three directories under "/layouts":

* docs
* partials
* shortcodes

#### /layouts/docs

These templates control the overall layout of our pages.

#### /layouts/partials

Partials are templates that can be called by other templates. The canonical use of them is to make reusable bits of content, like breadcrumbs and sidebars. But they can also be called by shortcodes, and can return values, so we are also using them to factor out common operations into separate modules.

* `alert`: common code for note, rationale, and warning boxes
* `breadcrumbs`, `navbar`, `sidebar-tree`, `version-banner`: partials for various page elements, taken from Docsy but modified for our purposes.
* `hooks/body-end`: this is included in all pages at the end of `<body>`. We use it to include custom JS, which is used to fix up heading IDs and generate the ToC.
* `hooks/head-end`: this is included in all pages at the end of `<head>`. We use it to include the modifications and extensions we've made to the default CSS that is included in Docsy.

Most significantly, partials do most of the work to render content from OpenAPI/Swagger data and event schemas.

* `events/render-event`: renders an event from an event schema object.
* `openapi/*`: various templates to render an HTTP API from OpenAPI data. These call each other as follows:

```
render-api
    -> render-operation
        -> render-request        -> render-object-table
            -> render-parameters -> render-object-table
        -> render-responses      -> render-object-table
```

* `json-schema`: this provides basic support for working with JSON schema and is called by both `render-event` and the `openapi` templates. It includes templates to handle the `$ref` and `allOf` keywords. This is probably the most complicated bit of code here and could definitely use some careful review.

#### /layouts/shortcodes

Shortcodes are templates that can be called directly from content. All the existing Batesian templates should have an analogous shortcode.

* `boxes/note`, `boxes/rationale`, `boxes/warning`: replace Note, Rationale, Warning RST directives.
* `changelog/changelog-changes`, `changelog/description`: used to build changelogs, including generating content from newsfragments.
* `cs-modules`: called from the client-server spec to embed all the modules.
* `definition`: replaces the old {{definition_*}} template.
* `event-fields`: replaces the old {{common_event_fields}} and {{common_room_event_fields}} templates.
* `event-group`: replaces the old {{*_events}} template.
* `event`: replaces the old {{*_event}} template.
* `http-api`: replaces the old {{*_http_api}} template.
* `msgtypes`: replaces the old {{msgtype_events}} template.
* `sas-emojis`: replaces the old {{sas_emoji_table}} template.

### /scripts

**[this section is WIP]**

This directory existed in the old platform, but most of it is redundant in the new one. However, we have added a few new scripts:

* /scripts/check-event-schema-examples.py:
* /scripts/check-swagger-sources.py:
* /scripts/proposals.js:

Also, we are still using some of the old scripts:

**WIP: <list them here>**

### /static

This includes static assets that don't need processing (assets that do need processing, such as SCSS, live in /assets):

* /icons
* /js/toc.js -> client-side JS to implement the table of contents

### /themes

This contains the Docsy theme as a submodule, which in turn pulls in Bootstrap and Font Awesome as submodules. Since we're not using much of these, it might make sense at some point to carve out the bits we are using and discard the rest.

### Significant top-level files

#### config.toml

Hugo config file. This starts with the Docsy config and makes a few changes. Notable things we have added:=

* `params.version.status`: indicates the status of this version, one of "unstable", "current", "historical".
* `params.version.current_version_url`: points to the URL for the  current version.
* `params.version.number`: used to describe the actual version number for this version of the spec. This is generally expected to be something like "1.2", but is treated as an opaque string by the spec platform, with no particular structure or semantics.

#### package.json

We unfortunately apparently have to have a Node dependency, I think for autoprefixing CSS properties.

## Making a spec release

**WIP**

## Cleaning up

**WIP - this section should describe which bits of matrix-doc we can retire once the new specification is published**
