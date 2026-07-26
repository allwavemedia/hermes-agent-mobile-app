# UX Flows

## Information architecture

The app is computer-first:

```text
Lock
└── Computers
    ├── Add computer
    └── Computer
        ├── Sessions
        ├── Devices & security
        └── Connection & retention
            └── Session
                ├── Conversation
                ├── Activity / requests
                └── Terminal / files (only when advertised)
```

The selected computer name, connection state, and session title remain visible on every action surface. Switching computers exits the current action composer to prevent cross-target confusion.

## First launch and pairing

1. Explain that Hermes runs on the computer and that the relay may process content; offer a link to retention details.
2. Require device credential/biometric app lock setup.
3. User chooses scan, manual code, or verified link.
4. App validates payload locally, displays computer name, relay origin, expiry countdown, and requested trust.
5. Phone proves possession; both surfaces display the same six-word phrase.
6. User confirms on both surfaces.
7. Computer appears with online state, retention mode, host key fingerprint, and no session selected.

Expired, consumed, changed-origin, pin-change, or phrase-mismatch flows discard all transient pairing state and require a new offer. They do not expose a “continue anyway.”

## Computer and session catalog

Computer cards show online/reconnecting/offline, last seen, temporary/zero retention, direct availability, and attention count while the app is open. Session rows show title, project display name, status, last activity, remote-enabled state, and current model. Disabled sessions show “Enable on computer”; the app cannot override that default.

“New session” is present only when the host is online and advertises `session.create`. The flow selects one advertised project and model and confirms the target computer. Arbitrary paths, environment variables, and shell options are absent.

## Shared session

Conversation merges historical snapshot and live events. Streaming text is visibly provisional. Activity cards show tool name, normalized safe summary, status, elapsed time, and bounded output. Local activity from Desktop/TUI appears identically; Android commands carry an “Android” actor label.

Reconnect banner distinguishes:

- “Reconnecting — actions paused”;
- “Catching up from event N”;
- “History window expired — refreshing session”;
- “Computer offline.”

Typed prompts remain local in memory. They are not sent until connected unless the explicit five-minute low-risk offline option is available and selected.

## Approval

1. Activity tab and session banner show pending request.
2. Detail shows computer, session, tool, exact normalized action summary, risk reason, expiry countdown, and whether local confirmation is also required.
3. User selects “Approve once” or “Deny.”
4. High risk invokes biometric step-up.
5. App signs the displayed digest and submits.
6. UI remains pending until host receipt; stale/resolved/mismatch becomes a non-retryable explanation and refresh.

There is no “always allow” in MVP. A generic failure never appears as success. Secret/sudo requests say “Complete on your computer.”

## Clarification

Clarification displays the originating assistant/tool context, question, answer controls, and expiry. Sending binds to the displayed request. If another surface answers first, the app closes the composer and shows “Answered elsewhere.”

## Interrupt and steering

Interrupt is available only for the displayed active run. It requires a confirmation tap but no biometric unless host risk policy elevates it. Steering labels that it affects the in-progress run and includes the active run identity. On run replacement, unsent steering is discarded.

## Attachments

Android’s system picker supplies a URI. App displays filename, size, MIME type, destination session, retention behavior, and the fact that Hermes mediates final use. Hashing/upload can be cancelled. Zero-retention computers disable relay-staged upload; a direct live path may be offered only if host capability permits.

No host filesystem browser is exposed. Files returned by Hermes are downloaded only through an advertised attachment manifest and opened with Android’s content-sharing protections.

## Device and emergency controls

Computer security screen shows paired devices, public-key fingerprint, paired/last-seen time, and revoke. “Revoke this phone” warns that re-pairing is required. Host Desktop/CLI offers “Revoke all devices” and “Rotate host identity,” with the latter explicitly destructive to pairings.

## Foreground notifications

While open, the app presents in-app banners for approval/clarification, run completion/failure, reconnect, and host offline. The app does not imply notification delivery while closed and requests no notification permission in MVP.

## Accessibility/error copy rules

Actions use verbs and targets. Risk is text, not color-only. Screen readers announce completed semantic chunks, not every token. Error copy includes: what happened, whether anything executed, safe next action, and whether retry is permitted. Identifiers/fingerprints have copy/read grouping; credentials and pairing capability never do.
