---
title: Telegram not connecting in Russia: why it's stuck on "Connecting" and fixes
description: Why Telegram in Russia hangs on "Connecting...", won't load photos or videos, and a step-by-step checklist: network, VPN, proxy, cache.
date: 2026-11-21
updated: 2026-11-28
slug: telegram-ne-podklyuchaetsya
---
<p class="lead"><b>In short:</b> when Telegram won't connect in Russia, it's usually because of the restrictions Roskomnadzor (the Russian telecom regulator) has applied since February 2026, or because of outages and whitelist mode on mobile internet. First check that you have internet at all, then turn on a VPN and switch servers. If that doesn't help, clear the cache and update the app.</p>

## Why Telegram won't connect

There are usually three causes, and each looks different.

| What you see | Most likely cause |
|---|---|
| "Connecting..." at the top, other sites load fine | Telegram is restricted on the network side |
| Text messages go through, photos, videos and voice notes don't | media is being throttled |
| Nothing works except Russian banks and government services | whitelist mode or a mobile internet shutdown |
| Only you have the problem, friends are fine | the app, its cache or your phone settings |

Some background. Telegram and WhatsApp calls have been restricted in Russia since August 2025. On 10 February 2026, according to RBC, Roskomnadzor started throttling Telegram, and the regulator said it would keep restricting the app. Since then many people see slow media and some messages that won't load.

One-off outages happen too. On 20 November 2026, from around 7:15 a.m. Moscow time, users reported that messages wouldn't send, media wouldn't load and calls failed. Most complaints came from Ivanovo, Novosibirsk and Chelyabinsk. No official cause was given. On 27 November the picture was mixed: some users found Telegram suddenly working without a VPN, while for others the app hung on "Updating" and proxies stopped working. We track fresh outages on the [blocking status page](/en/status/). Travelling to Russia? See [Telegram in Russia for tourists](/en/blog/telegram-in-russia-for-tourists/).

## What to do: 6 steps in order

1. **Check the internet without Telegram.** Open any foreign website. If nothing loads except Russian services, the problem is the network, not the app: whitelist mode may be on. Switch to home or hotel Wi-Fi.
2. **Turn on a VPN.** When Telegram is restricted on the network side, it works badly or not at all without one. After connecting, give the app 10-20 seconds to reconnect.
3. **Switch server or protocol.** If Telegram still hangs on "Connecting" with the VPN on, pick another country or another protocol in your VPN app. Sometimes one server gets blocked while the next one works.
4. **Turn off the proxy inside Telegram.** Go to Settings → Data and Storage → Proxy. If an old proxy that has stopped working is still enabled, Telegram will keep trying to use it even with a working VPN. Switch it off.
5. **Clear the cache and update the app.** Settings → Data and Storage → Storage Usage → Clear Cache. Your chats won't disappear, they're stored on Telegram's servers. Then update the app from the store.
6. **Check your phone's clock.** If the date or time zone is wrong, the app may fail to set up a secure connection. Turn on automatic date and time.

If the VPN connects but nothing opens at all, see [VPN connected but no internet](/en/blog/vpn-podklyuchen-no-net-interneta/).

## About free proxies

Telegram has built-in proxy support, and channels regularly hand out "working" addresses. The catch: you don't know who runs that server. Telegram encrypts your messages, but the proxy owner sees your IP address, and these proxies get blocked or overloaded quickly. For everyday use, a VPN you trust is more reliable.

## FAQ

### Why does Telegram work on Wi-Fi but not on mobile data?
Mobile networks see more shutdowns and whitelist mode, and Telegram isn't on the whitelist. Home connections are usually less restricted. If your VPN won't connect on mobile data either, check the [outage status](/en/status/).

### Why do text messages go through but photos and videos don't?
That's what throttling usually looks like: text is light and gets through, heavy files stall. With a VPN, media normally loads fine.

### Will I lose my chats if I reinstall Telegram?
Regular chats live in Telegram's cloud and come back after you log in. Only secret chats are lost, because they're stored on one device.

### Do Telegram calls work in Russia?
Without a VPN, calls have been restricted since August 2025. With a VPN they usually go through, but quality depends on the server and the network.
