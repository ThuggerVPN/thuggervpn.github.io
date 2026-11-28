---
title: Happ VPN setup: how to add a subscription or key in 2 minutes
description: How to set up the Happ VPN app: where to get a key or subscription link, how to add it from the clipboard, and what to do if Happ won't connect or is missing from the App Store.
date: 2026-11-25
slug: happ-vpn-kak-nastroit
---
<p class="lead"><b>In short:</b> Happ is a free client, not a VPN service. It has no servers of its own, which is why the screen is empty after you install it. To make it work you need a key or a subscription link from a VPN service: copy it, tap «Из буфера» (From clipboard) in Happ, allow the VPN configuration and connect. Steps for iPhone, Android and computers are below.</p>

## What Happ is and why it's empty

Happ runs on iPhone, Android, Windows, macOS, Linux and Android TV and supports modern protocols: VLESS with Reality, Trojan, Shadowsocks, Hysteria2. On its own it doesn't unblock anything: think of it as a remote control, while the servers and the key come from a VPN service. An empty list after installing is normal, not an error.

## How to set up Happ in 4 steps

1. **Install Happ.** Android: Google Play or an .apk file. Computer: the Windows or macOS version (details in <a href="/en/blog/vpn-na-kompyuter/">VPN on a computer</a>). iPhone: the App Store (if you have a Russian Apple ID, see the section below).
2. **Get a subscription link** from your VPN service. It usually comes from a Telegram bot: tap the link and it gets copied.
3. **Open Happ and tap «Из буфера» (From clipboard)** or "+" and paste from the clipboard. The subscription appears on the main screen with a list of servers.
4. **Allow the VPN configuration and connect.** On first connect the iPhone asks for permission: tap "Allow" and confirm with Face ID or your passcode. Then pick a location and tap the connect button.

The same steps with screenshots for every device are in our <a href="/en/podklyuchenie/">setup guide</a>.

## Subscription or key: which is better

| | Key (vless://...) | Subscription (https://... link) |
|---|---|---|
| Servers | one | several, the whole list from the service |
| If a server gets blocked | you need a new key | tap "Update" and the servers refresh |
| Best for | a one-off connection | everyday use |

For Happ a subscription is the better choice: when blocks hit, the service swaps servers and you refresh the list with one tap.

## Happ won't connect: what to do

1. **Refresh the subscription.** Pull the list down or tap the refresh icon next to the subscription. The old servers may have been blocked.
2. **Pick another location.** Blocks hit individual servers unevenly.
3. **Check that the subscription is paid.** When it expires, the servers stay in the list but won't connect.
4. **Check whether it's whitelist mode.** If it fails only on mobile data and works on Wi-Fi, run the <a href="/en/check/">connection check</a>. In whitelist mode an ordinary VPN won't connect, more in <a href="/en/blog/vpn-s-belymi-spiskami/">VPN that works with whitelists</a>.
5. **Reinstall the configuration on iPhone.** Settings → General → VPN & Device Management → delete old profiles and connect again in Happ.

Need instructions for another device? Message our [support](https://t.me/ThuggerVPN?direct) and we'll add them.

## Happ was removed from the App Store: how to install it

At the end of March 2026 Happ - Proxy Utility was removed from the Russian App Store. What this means:

- **If Happ is already installed,** don't delete it: it keeps working, it just won't get updates.
- **If you don't have Happ,** you can't download it with a Russian Apple ID. You need an Apple ID from another country: in the App Store sign out of "Media & Purchases" only, sign in with the other account, download the app and switch back. The full step-by-step is in the <a href="/en/podklyuchenie/">setup guide</a>.
- **On Android** you can install Happ from an .apk file if Google Play doesn't open.

## FAQ

### Is Happ VPN free?

The app itself is free. But it doesn't work without a key or subscription, and those come from a VPN service, free or paid.

### Where do I get a key for Happ?

From a VPN service, usually through its Telegram bot. A subscription from a service with a free trial is safer than random free keys from the internet: those get blocked fast, and you don't know who sees your traffic. Here's <a href="/en/blog/probnyj-vpn/">what to test during a trial</a>.

### Why is the Happ screen empty?

Because no subscription has been added yet. Copy the link and tap «Из буфера» (From clipboard).

### Can I use one subscription in both Happ and Incy?

Yes, if the service gives you a standard subscription link: it works in any compatible client.
