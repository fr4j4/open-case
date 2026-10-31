// The transport settings, in one place. Deciding which transport to use (F0's result) means
// changing this file and nothing else. See docs/web-network-test.md for the decision rules.
//
// Until there is field data this is option 2 of the plan: WebRTC first (Trystero over Nostr)
// and the relay bus (messages encrypted and passed through the same public relays) as backup.

export const CONFIG = {
  // Transport used first, and the one the app falls back to when a peer does not connect in time.
  // Names: 'trystero-nostr', 'trystero-mqtt', 'trystero-torrent', 'relay', 'broadcast'.
  primary: 'trystero-nostr',
  fallback: 'relay',

  // How long to wait for the other side before calling a connection failed (ms).
  connectTimeoutMs: 10000,

  trystero: {
    // Rooms are scoped by this id, so tests never meet other apps that use Trystero.
    appId: 'open-case-p2p-v1',
    // Empty = the relays the library ships for each strategy.
    relayUrls: [],
    // Extra STUN/TURN servers for rtcConfig (empty = the library's defaults).
    iceServers: [],
  },

  relay: {
    // Empty = the public Nostr relays Trystero ships. Anything starting with wss:// works.
    urls: [],
    // How many relays to keep open at the same time.
    redundancy: 4,
    // Ephemeral event kind (20000 to 29999 are not stored by relays).
    kind: 21487,
  },

  // The layer on top of every transport: ids, acknowledgements, retries and order.
  reliability: {
    retryMs: 700,        // first retry; each next one waits 1.5 times more
    maxTries: 8,         // after this many sends without an ack the message fails
    gapMs: 4000,         // a missing message is skipped after this long, so one loss does not freeze the rest
    readyMs: 10000,      // send() waits this long for the peer to say hello before failing
    helloMs: 2000,       // while nobody is known, say hello this often
    keepAliveMs: 5000,   // once known, say hello this often (also how peers on a shared bus notice each other)
    peerTtlMs: 16000,    // a peer on a shared bus that sent nothing for this long has left
  },
};

// Names the lab (and the app) can ask for.
export const TRANSPORTS = ['trystero-nostr', 'trystero-mqtt', 'trystero-torrent', 'relay', 'broadcast'];
