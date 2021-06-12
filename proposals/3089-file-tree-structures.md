# MSC3089: File trees

Files are currently shared by uploading them to the media repo and putting a reference to that content
in a room message. This is fine for most use cases, such as sharing screenshots or short-lived documents,
however longer term, collaborative, structures are not quite possible.

This MSC defines an approach for defining data trees in Matrix, using a document hierarchy as an example
for how it could be applied.

Reading material:
* [MSC1772 - Spaces + Room types](https://github.com/matrix-org/matrix-doc/pull/1772)
* [MSC3088 - Room subtyping](https://github.com/matrix-org/matrix-doc/pull/3088)
* [MSC1767 - Extensible events](https://github.com/matrix-org/matrix-doc/pull/1767)

Optional but useful reading:
* [MSC1840 - Alternative room types](https://github.com/matrix-org/matrix-doc/pull/1840)
* [MSC2326 - Label-based filtering ("threading")](https://github.com/matrix-org/matrix-doc/pull/2326)
* [MSC2674 - Event relationships](https://github.com/matrix-org/matrix-doc/pull/2674)
* [MSC2676 - Message editing](https://github.com/matrix-org/matrix-doc/pull/2676)
* [MSC2946 - Spaces summary](https://github.com/matrix-org/matrix-doc/pull/2946)
* [MSC2962 - Space group access control](https://github.com/matrix-org/matrix-doc/pull/2962)
* [MSC2753 - Proper peeking](https://github.com/matrix-org/matrix-doc/pull/2753)
* [Spec - Withholding encryption keys](https://spec.matrix.org/unstable/client-server-api/#reporting-that-decryption-keys-are-withheld)

## Proposal

*Author's note: This proposal assumes the reader is familiar with the terminology of the reading
materials mentioned above.*

We introduce a new room subtype, `m.data_tree`, to be applied to spaces to denote that they are
data-driven trees. The subtype only needs to be applied to a parent space to affect all subspaces
of that space. For a file hierarchy, the room name for the spaces are the directory names. Note
that this subtype is *optional* and serves only to hide the tree from conversation-focused clients.

Spaces used in a tree-like way (with the `m.data_tree` subtype or not) are called "tree spaces" in
this proposal.

The context of the tree space denotes what it is representing. The 3 major expected types are:

1. A standalone data tree. This should be annotated with the `m.data_tree` subtype, and would represent
   a shared directory of sorts, possibly shared publicly. This is similar to sending a share link
   to a directory in a file syncing service (ie: Dropbox).
2. A data tree as part of a space, but not mirroring the structure of that space. This would also
   have the `m.data_tree` subtype, and would best represent a shared drive within that space.
3. The space itself with no subtyping. This usually indicates that the space is structured such that
   people can browse files uploaded anywhere for easier exploration. This is expected to be used
   in conjunction with case 2. This case would end up potentially replacing the "Files" panel in
   many conversational clients.

A limited example of what this would look like is (📂 denotes `m.data_tree` space, `📄` denotes a
file/leaf (described later), and `+` denotes a Space):

```
+ Acme Co.
  + Sales Team
    + 📂 Quarterly objectives
      + 📂 Q1 2021
        - 📄 Targets
        - 📄 End of quarter report
      + 📂 Q2 2021
        - 📄 Targets
      + 📂 Q3 2021
      + 📂 Q4 2021
  + HR
    - 📄 WIP: Time off requests v2
    + 📂 Personnel files
    + 📂 Policies
      - 📄 Time off requests
    + 📂 Contract templates
```

In the example, the sales team has set up a subspace to hold all of their files and folders ("case 2"
from above). Access control would likely be a subset of Acme Co.'s members, limited to the sales team
space specifically. The HR space has a similar structure, though has decided to use a room which is *not*
subtyped to `m.data_tree` to upload some work-in-progress policies. The HR team also has a shared drive
which would almost certainly have space-defined access control.

In both team's cases, clients would not render the 📂 trees as browseable in a room list (typically). The
client would likely expose a "View files" button which then takes the user to a file browser of sorts
for the user to explore. The WIP policies would likely show up in the "Files" panel of the client, where
a link to explore the 📂 trees.

Tree spaces may contain non-space rooms under them to help perform access control. For example:

```
+ My Folder
  - Regular room 1
  - Regular room 2
  + 📂 Subfolder 1
```

When this happens, the rooms are treated effectively as more buckets under that parent node. In the above
example this would mean that anything posted to either "Regular room" would be listed under "My Folder"
instead. This is expected to be a rare choice of data structure, though can theoretically be used to
group files within a directory for simpler access control. Note that the "My Folder" space does not need
to be subtyped to have this happen.

Files are represented as room events either in the tree room (or in any non-space room under that tree
space). This is done by exposing a generic `m.leaf` type which is purely intended to be used to encourage
proper rendering within the extensible events scheme.

This intentionally does not use state events to represent each leaf as encrypted state events are not possible
currently. Other MSCs may wish to optimize the lookup of regular room events, though for now the intention
is that clients would parse events themselves.

A file would look something like this (when using extensible events):

```json5
{
  "type": "m.file",
  "content": {
    "m.text": "targets.docx (12 KB)",
    "m.file": {
      "url": "mxc://example.org/abc123",
      "name": "targets.docx",
      "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": 12000
    },
    "m.leaf": {}
  }
}
```

Note that this would allow non-file types to be included in the tree. Clients would filter out anything
that doesn't make sense for their use case, such as ignoring text-only events. Events missing the `m.leaf`
description would be excluded as non-leaf events. No content for `m.leaf` is currently defined - clients
can interpret labels for files/other types through the extensible events format.

The `m.leaf` type is intentionally not used as the event type as fundamentally the user is uploading a file,
not a leaf. The leaf is essentially metadata on the event to describe how it could be rendered by clients
behaving in a suitable way. Otherwise, it's deliberate that the event shows up as a regular file upload in
the room.

Events can be edited to add the `m.leaf` metadata, adding them to the tree.

Since room events can be encrypted, it can mean that the `m.leaf` metadata gets encrypted too. This could
potentially make it harder on clients/servers to find *just* leaf events. As a workaround, clients can
include the `m.leaf` metadata to the encrypted `content` so it can be found by servers. Clients MUST still
include an encrypted copy in the event content, which clients MUST prefer over the plaintext version. As
an example, this could look like (keys will not be accurate):

```json5
// Encrypted event
{
  "type": "m.file",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "Awga...oEkC",
    "device_id": "UCCUUHBQQM",
    "sender_key": "Vn+E+aPjvlbf14j1OWCIe5IlkTLZ4Zft628Mw8RysG4",
    "session_id": "uXWJgrndwkutoKQVqsTsdamRDKqBAkgBawjeqaB+81s",
    "m.leaf": {}
  }
}
```

```json5
// Decrypted copy of event
{
  "type": "m.file",
  "content": {
    "m.text": "targets.docx (12 KB)",
    "m.file": {
      "url": "mxc://example.org/abc123",
      "name": "targets.docx",
      "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": 12000
    },
    "m.leaf": {
      "com.example.custom_field": true
    }
  }
}
```

Note how the encrypted event excludes the custom field but the decrypted copy does not. This is to ensure
there is no unnecessary disclosure of information. Clients MUST NOT trust the `m.leaf` in the encrypted
event and must only consider the decrypted copy's `m.leaf`. This is to ensure that an `m.leaf` is *always*
present on an event that needs it, as some clients might optimize out the `m.leaf` without carrying it over.

**TODO: Decide on index versus the above (`m.leaf` accessible by server). Index is below.**

The client is expected to maintain a "branch" structure in the room state, denoting the active files and
where to find those files. This is done through a `m.branch` state event, where the state key is the event
ID of the file. An `m.branch` event looks like this:

```json5
{
  "type": "m.branch",
  "state_key": "$event",
  "content": {
    "active": true
  }
}
```

When `active` is not exactly `true`, the file is considered invalid/inactive. Clients should ignore inactive
files. Clients should take reasonable efforts to resolve the latest version of a file: an edited file event
shouldn't need `m.branch` switching.

For some common operations:
* Deleting a file would mean redacting the event.
* Updating a file could mean editing it, or redacting and re-sending.
* Changing view file permissions could mean using an encrypted room and withholding keys.
* Changing upload permissions would mean altering power levels.
* Renaming a file would mean editing the label.
* Moving a file would mean redacting and re-sending in the right tree.
* Comments/notes on a file could be threads off the file.
* Anonymous browsing would be peeking into the various rooms.

Implementation-wise, the following may be useful:
* Using space summaries to render the directory structure.
* Peeking to get file listings.
* Group access controls to control who can (and can't) upload/view files.
* Encryption to protect files and get finer control over visibility.
* History visibility and join rules to manage publicity of the files.
* Room directory for discovering public file shares.

## Potential issues

***TODO***

## Alternatives

***TODO***

## Security considerations

***TODO***

## Unstable prefix

While this MSC is not in a stable version of the specification, implementations should
use `org.matrix.msc3089.` in place of `m.` - this means, for example, `org.matrix.msc3089.leaf`
as an identifier.
