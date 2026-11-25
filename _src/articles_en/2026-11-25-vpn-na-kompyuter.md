---
title: How to set up a VPN on a PC or Mac for Russia: 2-minute guide
description: VPN for Windows and macOS that works in Russia: which app to install, where to paste your subscription link, and what to do if the VPN won't work on your computer.
date: 2026-11-25
slug: vpn-na-kompyuter
---
<p class="lead"><b>In short:</b> to get a VPN working on a computer in Russia you need two things: a client app (Incy, Happ or V2RayTun for Windows and macOS) and a subscription link from a VPN service. Install the client, copy the link from the bot, tap "import from clipboard" in the app and connect. Skip the VPN option built into Windows settings: it uses older protocols that often don't get through in Russia.</p>

## How to set up a VPN on your computer: 4 steps

1. **Download a client.** Incy, Happ and V2RayTun all have Windows and macOS versions. All download links are on the <a href="/en/podklyuchenie/">setup page</a>, which detects your device automatically.
2. **Get your subscription link** from the VPN service. Usually a Telegram bot gives it to you. If the bot is open on your phone, forward the link to your Saved Messages so you can copy it on the computer.
3. **Add the subscription to the app.** Copy the link, open the client and click "+" and then "Import from clipboard" (the wording differs slightly between apps). A list of servers appears.
4. **Connect.** Pick a location and press the connect button. Windows may ask for permission or admin rights. That's normal: the client creates a virtual network adapter.

To check, open a site that didn't load without the VPN. If it opens, you're done.

## Which VPN client to use on a PC or Mac

The client is just a shell. It opens nothing on its own: the servers come from the service. So you choose twice: a convenient app and a VPN service that actually works in Russia.

| Client | Windows | macOS | Why use it |
|---|---|---|---|
| Incy | yes | yes | one button, has a kill switch |
| Happ | yes (x64 and ARM) | yes (App Store and .dmg file) | works with almost any subscription |
| V2RayTun | yes | yes | backup option |

All three support modern protocols such as VLESS with Reality, which currently get through Russian blocking better than older ones. The same subscription link works in any of them, so if one client won't install, just try another. How to pick the service itself: see <a href="/en/blog/kak-vybrat-vpn-2026/">how to choose a VPN for Russia</a>.

## Setting up a VPN on Windows 10 and 11

- Download the installer from the client's official site or from the link on our setup page, not from random download portals.
- If Windows Defender or your antivirus flags the installer, double-check that it came from the official site. These clients change network settings and antivirus tools sometimes react to that.
- After installing, open the client, add the subscription and connect.
- If the client lets you choose between "System proxy" and "VPN" (TUN) mode, choose VPN. In proxy mode mostly the browser goes through the tunnel, while games, Telegram Desktop and other apps may connect directly.

## Setting up a VPN on a Mac

- On macOS the clients come from the App Store or as a .dmg file from the developer's site.
- With a Russian Apple ID you won't find Incy, Happ or V2RayTun in the App Store: they were removed from the Russian store. Download the Mac version from the client's website instead (Happ, for example, offers a .dmg).
- On the first connection macOS asks to add a VPN configuration. Click "Allow" and enter your Mac password.

## VPN not working on your computer: what to do

| What you see | What it means | What to do |
|---|---|---|
| Connected, but sites don't load | server not responding or outdated subscription | refresh the subscription in the client, pick another location |
| Only the browser works | client is in proxy mode | switch the client to VPN (TUN) mode |
| Won't connect at all | antivirus or firewall blocks the client | add the client to your antivirus exceptions |
| Works on home Wi-Fi, fails over a phone hotspot | mobile internet restrictions | check the <a href="/en/status/">outage status</a> and the <a href="/en/check/">connection check</a> |
| Stops working after the laptop wakes up | the tunnel didn't reconnect | turn the VPN off and on again |

If the app says "Connected" but nothing loads, follow the steps in <a href="/en/blog/vpn-podklyuchen-no-net-interneta/">VPN connected but no internet</a>. One simple thing often helps: check the date and time on the computer. If the clock is off, some protocols won't connect.

## FAQ

### Can I use a free VPN client on my PC?

The clients Incy, Happ and V2RayTun are free. You only pay for the servers. Many services offer a trial, so you can test the VPN on your own computer and internet connection before paying.

### Do I need the VPN built into Windows settings?

No. Under Settings, Network and internet, VPN, you have to type in a server by hand and pick an older protocol (PPTP, L2TP, IKEv2). A separate client with a subscription link is easier and more reliable.

### Why does the VPN work in the browser but not in games or Telegram?

The client is most likely running as a system proxy. Switch it to VPN (TUN) mode so all of the computer's traffic goes through the tunnel.

### Can I use one VPN on my phone and my laptop?

Yes, if your plan allows several devices. Add the same subscription link to the client on your computer and the app on your phone. Check how many devices your plan includes.
