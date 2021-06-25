# MSC2354 - Device to device streaming file transfers

File transfer in matrix currently works by uploading a file to the server, which is then distributed over
the participating servers in the room, and is available through an HTTP get request to everyone who knows
the URL. By necessity this has a maximum filesize and also results in a more or less permanent availability
of said file. For larger files, and/or files that should only be sent from point-to-point, it may be desirable
to be able to send from device to device. As matrix already implements
[WebRTC signalling for voip](https://matrix.org/docs/spec/client_server/r0.6.0#voice-over-ip), this 
functionality can be replicated for streaming file transfers from device to device. It can even be possible
to send files not between devices of two matrix users, but two matrix devices owned by the same user. For 
this we can use the webrtc datachannel.


## Proposal

To allow the device to device streaming data tranfser we propose to add events mirroring setting up a
WebRTC VoIP session.

To start a file transfer a user first selects the file to be transferred, after which the sending client 
sends an `m.d2dfile.invite` event with:

```
{
    "content": {
        "transfer_id": "12345",
        "lifetime": 60000,
        "filename": "example.doc",
        "info": {
            "mimetype": "application/msword",
            "size": 46144
        },
        "offer": {
            "sdp": "v=0\r\no=- 6584580628695956864 2 IN IP4 127.0.0.1[...]",
            "type": "offer"
        },
        "version": 0
    },
    "event_id": "$Rqnc-F-dvnEYJTyHq_iKxU2bZ1CI92-kuZq3a5lr5Zg",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "sender": "@example:example.org",
    "type": "m.d2dfile.invite",

    "unsigned": {
        "age": 1234
    }
}
```

This triggers other devices in the room to alert the user about the offered transfer, displaying the filename, filetype and filesize.

In order to establish an RTCDataChannel, the sending device can gather candidates. 
This is done following the spec detailing how to find a turnserver by sending an 
authenticated get request to `https://example.org/_matrix/client/r0/voip/turnServer`.
Following the same course as used for setting up a VoIP call, this returns 
the address of the turnserver and a username and password. This turnserver can then be used 
to find the peer to peer candidates and/or a relay. Otherwise the external (possibly local) 
ip address can be used to create a candidate.

These candidates are then sent using: 
`m.d2dfile.candidates` with:
```
{
    "content": {
        "transfer_id": "12345",
        "candidates": [
            {
                "candidate": "candidate:863018703 1 tcp 2122260223 10.9.64.156 43670 typ host generation 0",
                "sdpMLineIndex": 0,
                "sdpMid": "0"
            }
        ],
        "version": 0
    },
    "event_id": "$Rqnc-F-dvnEYJTyHq_iKxU2bZ1CI92-kuZq3a5lr5Zg",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "sender": "@example:example.org",
    "type": "m.d2dfile.candidates",
    "unsigned": {
        "age": 1234
    }
}
```

If a device accepts the filetransfer the device in turn sends an `m.d2dfile.answer` event, containing:

```
{
    "content": {
        "answer": {
            "sdp": "v=0\r\no=- 6584580628695956864 2 IN IP4 127.0.0.1[...]",
            "type": "answer"
        },
        "transfer_id": "12345",
        "lifetime": 60000,
        "version": 0
    },
    "event_id": "$Rqnc-F-dvnEYJTyHq_iKxU2bZ1CI92-kuZq3a5lr5Zg",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "sender": "@example:example.org",
    "type": "m.d2dfile.answer",
    "unsigned": {
        "age": 1234
    }
}
```
The accepting device also sends a `m.d2dfile.candidates` in order to establish the data connection.

To cancel a filetransfer or reject an offer the `m.d2dfile.cancel` event is sent, as follows:

```
{
    "content": {
        "transfer_id": "12345",
        "version": 0
    },
    "event_id": "$Rqnc-F-dvnEYJTyHq_iKxU2bZ1CI92-kuZq3a5lr5Zg",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "sender": "@example:example.org",
    "type": "m.d2dfile.cancel",
    "unsigned": {
        "age": 1234
    }
}
```

## Potential issues
It's tempting to want to use this for device to device transfer in public rooms, 
but an evil homeserver could hijack the webrtc session by pretending to be a device 
for the intended recipient (if that user has an account on the evil server). As such this 
should be limited to private rooms.  
Otherwise the matrix logic is quite simple here, basically following the same flow as 1:1 VoIP calls,
however: most guides (including the synapse github how-to) advice to disable TCP relays in the turnserver,
which may be unwanted for file transfers.

Both sender and reciever need to be online simultaneously for this mode of file transfer
to work, which is unexpected in the context of the existing matrix file transfer.

This file transfer will only send the file once, from one device to another.

While this proposal focusses on streaming file transfer, 
a webrtc datachannel could be used for any generic data transfer, 
for the use of any other application, such as games for instance. 
If such application is wanted, the d2dfile event type may be a poorly chosen name.
For this proposal other uses for a webrtc datachannel is deemed out of scope.

## Alternatives
The current way of sending files is a valid alternative, 
the biggest upside of adding this proposal is that this allows for 
streaming file transfer outside of matrix and is thus not limited in filesize 
and negates the need for the matrix server to host any of the files.  
Since filetransfer over matrix isn't unique with the device to device transfer,
and implementation of filetransfers over webrtc is probably not trivial, 
this feature could be marked as optional.

## Security considerations
Using RTCDataChannel to transfer files could be abused to send malware 
without having the possibility of checking for this in between on the serverside.
This could be mitigated similarly to how DINUM does this,
by sending the file to a virus scanning server first, 
but that negates (some of) the advantage of streaming filetransfers.
