---
title: Incy VPN setup: how to add a subscription in 2026 (iPhone, Android, PC)
description: How to set up the Incy VPN app on iPhone, Android, computer and TV: add a subscription link, allow the VPN, and what to do if Incy won't connect or left the App Store.
date: 2026-11-25
slug: incy-vpn-kak-nastroit
---
<p class="lead"><b>In short:</b> Incy is a free VPN client with no servers of its own. After you install it, the server list is empty, and that's normal. Copy the subscription link from your VPN service, open Incy, tap "From clipboard", allow it to add a VPN configuration and connect. Steps for every device and fixes for common problems are below.</p>

## What is Incy

Incy is a client built on the Xray core for Windows, macOS, Linux, iPhone, Android and Android TV, with a version for Apple TV too. It supports the protocols that currently get through Russian blocking best, including VLESS with Reality and XHTTP, and imports a subscription in one tap. It also has a kill switch: if the VPN drops, internet access is blocked so your traffic doesn't leak outside the VPN.

Incy only connects. The servers and the key come from your VPN service. So "Incy isn't working" almost always means the subscription or a server isn't working, not the app itself.

## How to set up Incy: 4 steps

1. **Install Incy.** Android and Android TV: Google Play or an .apk file. Windows and macOS: the version from the developer's site or the Mac App Store (everything about computers is in <a href="/en/blog/vpn-na-kompyuter/">VPN on a computer</a>). iPhone: the App Store (there's a catch with a Russian Apple ID, see below).
2. **Copy the subscription link** from your VPN service. In a Telegram bot, one tap on the link is enough.
3. **Open Incy and tap "From clipboard"** («Из буфера» in the Russian interface). The subscription is added and a list of locations appears.
4. **Allow the VPN and connect.** On iPhone you'll be asked to allow adding a VPN configuration: tap Allow and confirm with Face ID or your passcode. Pick a location and tap Connect.

Step-by-step instructions for each device, with download buttons, are on the <a href="/en/podklyuchenie/">how to connect page</a>. If you prefer video, there's a <a href="/en/video/">one-minute video guide</a>.

## Incy won't connect: what to do

1. **Refresh the subscription** in the app. If the service changed its servers, the old list stops working.
2. **Switch locations.** Some servers are blocked harder than others.
3. **Check that your subscription is active.** After it expires, servers still show up but won't connect.
4. **Check the network without the VPN.** If nothing works without the VPN either, it's not Incy. Look at the <a href="/en/status/">outage status</a> for your region.
5. **Only failing on mobile data?** Most likely it's whitelist mode. Check it in 5 seconds with our <a href="/en/check/">internet check</a>, and see <a href="/en/blog/vpn-s-belymi-spiskami/">VPN with whitelists</a> for what to do.
6. **Telegram doesn't work with Incy on?** Refresh the subscription and try another location. Full guide: <a href="/en/blog/telegram-ne-podklyuchaetsya/">Telegram not connecting even with a VPN</a>.
7. **Banks and Gosuslugi won't open with Incy?** Many Russian services don't like foreign IP addresses. The fix is in <a href="/en/blog/vpn-i-bankovskie-prilozheniya/">banking apps and VPN</a>.

## Incy was removed from the App Store: what now

On 27 October 2026 Incy was removed from the Russian App Store.

- **Already installed?** Don't delete it. The app keeps working, just without updates.
- **Need to install it again?** You'll need an Apple ID from another country: sign out of the App Store only under "Media & Purchases", sign in with the other account, download Incy, then switch back. iCloud, photos and contacts aren't affected.
- **Didn't work out?** Paste the same subscription into another compatible client, such as <a href="/en/blog/happ-vpn-kak-nastroit/">Happ</a> or V2RayTun.

## FAQ

### Is Incy VPN free?

The app is free. To connect, you need a subscription or a key from a VPN service.

### Why is the server list in Incy empty?

You haven't added a subscription yet. Copy the link from your service and tap "From clipboard".

### What's the difference between Incy and Happ?

Both are clients without their own servers and work with the same subscriptions. Incy focuses on a simple interface and a stable connection, Happ on flexible settings and routing. Install whichever you can download.

### Does Incy work on a TV?

Yes. There's a version for Android TV in Google Play and as an .apk, plus a version for Apple TV. The subscription is the same as on your phone.
