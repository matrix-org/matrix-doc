# MSC 2299: Proposal to add m.textfile msgtype

Let's say you are helping someone out with code and just want to look at their code. Currently, you have to save the file
to your desktop and then view it in whichever viewer you want. Or you are helping someone configure something, if they
send the config file, you'll have to save it and view it externally. Instead it would help greatly to display the content
of these files inline. To not clog up vertical space and to save bandwidth a small preview could be attached to text files
in order to pitch the file to the user.  
Furthermore, other networks (such as slack) already do this, which would help bridging networks together.

## Proposal

This proposal adds a new `m.textfile` msgtype to messages with type `m.room.message`. It would accompany the msgtypes
`m.file`, `m.image`, `m.audio` and `m.video` as being uploaded content.

This msgtype has an optional parameter, `preview`, which contains a short preview of the text file sent. If this key is
absent the client could download the file and generate the preview itself, similar to thumbnails in `m.image`.

If interacted with, the preview could expand to the full text file so that you can view it inline within the client, without
needing to save it to the desktop.

The textfile preview could be rendered similarly to this (screenshot from slack):  
![textfile rendering](images/2299-example-slack.png)

All keys include:
 - `msgtype`: "m.textfile"
 - `body`: name of the file uploaded
 - `url`: mxc url of the file
 - `preview`: (optional) A short text preview of the file

### Example
The content of the corresponding `m.room.message` event would look like the following:
```
{
    "msgtype": "m.textfile",
    "body": "myfile.txt",
    "url": "mxc://server/media",
    "preview": "line 1 preview\nline 2 preview\nline 3 preview"
}
```

## Tradeoffs

Clients have to implement yet another msgtype for `m.room.message` message types. If the client developer choses not to
support inline text previews, they could however decide to just offer this file for download, instead of the preview.

## Potential issues

Once this msgtype is introduced and people start uploading textfiles old clients won't be able to see them at all, until
their developer updates to support this msgtype.

## Security considerations

none

## Conclusion

An inline text preview would greatly help with e.g. code reviews, quick config file checking etc. and this PR allows that
easily.
