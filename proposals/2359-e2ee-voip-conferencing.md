
# E2E Encrypted SFU VoIP conferencing via Matrix


## Background

Matrix has experimented with many different VoIP conferencing approaches over the years:

* Using FreeSWITCH as an MCU (multipoint conferencing unit - i.e. mixer) via
  matrix-appservice-verto, where Riot would place a normal Matrix 1:1 VoIP call
  to an endpoint on the MCU derived from the conf room ID where the conf call
  was being triggered, with the existence of the ongoing conf call tracked in
  the conf room’s room state.  This predated Matrix E2EE, and suffered due to
  problems with tuning FreeSWITCH to handle low bandwidth connections, as well
  as suffered bad UX relative to an SFU, and was removed from Riot in ~2017. 

* Using Jitsi as an SFU (stream forwarding unit) via widgets augmented by native
  support.  This provides a much better UX, but doesn’t provide E2EE.  It’s
  fiddly to get working (particularly screensharing) on Riot/Desktop though, and
  the React/Native dependencies on Riot/Mobile end up being quite a pain to
  maintain. Jitsi occasionally adds unwanted analytics dependencies &
  functionalities too.  It’s also a bit of a shame to rely on embedding a random
  “out of band” centralised focal point for conferencing via a widget, rather
  than leveraging Matrix as a data transport or signalling layer.

* Using full mesh VoIP calls, where all the clients in a given room initiate
  1:1 VoIP calls in DMs in order to establish a conf call.  This was done as a
  quick hack for
  [vrdemo](https://github.com/matrix-org/matrix-vr-demo/blob/master/src/js/components/structures/FullMeshConference.js)
  and worked surprisingly well - but has not been evolved due to lack of
  braincycles (and because Jitsi was working well enough, with a nice UX). It
  provides decentralised E2EE conferencing out of the box, but consumes
  significant bandwidth & CPU/GPU/power to handle all the simultaneous 1:1
  calls.

This proposal is a sketch of a 4th type of conferencing, providing SFU
semantics but leveraging Matrix’s E2EE to stop the SFU being able to intercept
call media.


## Overview

* You start off with a normal E2EE matrix room
* All members start a VoIP 1:1 call in a DM with the SFU
  * However, the SRTP keys for the media RTP (not RTCP) streams are
    deliberately stripped from the SDP of the m.call.invite and m.call.answer
    by the clients, so the SFU can’t decrypt the call media. The call
    signalling negotiates typical SFU srtp streams for:
    * Sending audio (if not muted)
    * Sending thumbnail video (if not muted)
    * Sending full-res video (if requested by the SFU and not muted)
    * Receiving 1-n multiplexed audio streams
    * Receiving 1-n multiplexed video streams (mix of thumbnail & full-res)
  * The 1:1 rooms could/should be E2EE to protect metadata, although this
    isn’t strictly necessary to protect the call media.
* The members exchange the SRTP keys via timeline events (ideally state
  events, but they’re not E2EE yet) in the main conference rooms, so the
 clients can decrypt the forwarded SRTP streams.
* The SFU itself:
  * Looks at the bandwidth of the media streams being received from the
    various clients, and uses REMB or TMMBR or whatever RTCP congestion
    control mechanism to request that the sending client’s full-res bitrate is
    clamped to the lowest receive bitrate determined from the clients which
    are currently trying to view the full-res streams.
    * (Particularly slow receiving clients could be ignored and be forced to
      (use the thumbnail rather than the full-res stream instead)
  * Tracks which clients are trying to view the full-res streams (via
    datachannel?) and forwards the full-res streams to the clients in question
    (requesting them via datachannel from the client if needed).
    * The SFU could also use the datachannel to determine who’s currently
      claiming to talk, to let users control the conference focus.
  * Does the same for thumbnails too. (Could assume that everyone wants a copy
    of the thumbnail streams).
  * Relays the audio streams to everyone.
* We use the datachannel for the SFU control rather than Matrix to minimise
  latency (which is really important when rapidly switching focus based on
  voice detection in a call).
* This consciously leaks metadata about who was talking and when, but at least
  the call data isn’t leaked.
* The fact the SFU can’t decrypt the streams means that some tricks aren’t
  available:
  * We can’t framedrop when sending to slow clients, as we don’t know where
    the frames are.  (Unless we provide some custom RTP headers or RTCP
    packets outside the SRTP payloads to identify the frame types, but WebRTC
    doesn’t support this afaik?)
  * We also can’t downsample for slow clients, obviously.  We could however
    negotiate multiple send streams from the clients to try to support a
    slower clients better.
  * SVC (which is patent encumbered anyway) probably is ruled out, as
    exploiting spatial redundancy between the low & high res send streams is
    probably impossible between the separated streams.
* However, some tricks are still available?
  * We can however forward keyframe requests from clients via RTCP.
* This has been written without reference to perc, so is probably missing insights
  from there.

TL;DR: it works like a normal SFU, except the SRTP keys for the media streams
are exchanged in the megolm room where the conference was initiated, so the
SFU can never decrypt the media - but can still do rate control and forward
the streams around intelligently.

## Details

Need to specify:

* matrix timeline events for advertising the SRTP keys for the various streams in the conf room
* matrix state events for announcing the existence of a conf call in the conf room
* DataChannel API for SFU floor control (or perhaps we could start off with Matrix to keep things a bit simpler?)
* resolution/fps of the pyramid of send streams? ability to let the SFU dynamically negotiate the send stream resolution/fps?
* TMMBR or REMB or whatever folks use for CC these days?

