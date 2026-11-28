---
title: YouTube not working in Russia even with a VPN: causes and fixes
description: VPN is on but YouTube in Russia won't load, videos keep buffering or stay at 144p. The common causes and a step-by-step checklist.
date: 2026-11-22
slug: youtube-ne-rabotaet-s-vpn
---
<p class="lead"><b>In short:</b> when YouTube won't load in Russia even with a VPN on, the problem is usually one of three things: the app is bypassing the VPN (split tunneling or a stale DNS setting), the server you picked is overloaded, or mobile data is in whitelist mode and the VPN can't get through at all. Check your IP, switch servers, clear the app cache. Details below.</p>

## What's going on with YouTube in Russia

Russia started slowing YouTube down in late July 2024, and from December 2024 it became practically unwatchable without a workaround. On 10 February 2026 IT experts and media reported that the YouTube domain had disappeared from Russia's national domain name system (NSDI), which local operators are required to use. In plain terms: without a VPN, your phone often can't even find YouTube's servers.

People still watch it, though. According to a Future Lab study reported by Kommersant, YouTube watch time in Russia grew 24% in the first half of 2026, to 99 minutes a day per user.

Ordinary outages happen too. On the evening of 21 November 2026, for example, people across the country reported problems: two thirds of the complaints were about the website, the rest about the app and playback. We track fresh outages on the [blocking status page](/en/status/).

## Find the cause first

| What you see | Most likely |
|---|---|
| Other sites load through the VPN, YouTube doesn't | the app bypasses the VPN or a stale DNS is stuck |
| YouTube opens but plays at 144p or keeps buffering | overloaded or distant server |
| Nothing loads except Russian banks and Gosuslugi | whitelist mode on mobile internet |
| Only the app fails, the browser is fine | app cache or settings |
| Slow in the evening, fine during the day | peak-hour load on the server |

## What to do: 7 steps

1. **Make sure the VPN actually works.** Open our [connection check](/en/check/) with the VPN on. If it shows a Russian IP, your traffic is going around the tunnel and YouTube isn't the problem.
2. **Check split tunneling.** Many VPN apps have a list of apps that skip the tunnel. If YouTube or your browser ended up there by accident, it goes direct and hits the block. Remove it from the list.
3. **Restart YouTube after turning on the VPN.** The app may keep its old connection. Close it fully (swipe it away from recent apps) and open it again.
4. **Switch servers.** If video stutters, pick another country, ideally a closer one. A server that half the country is using will slow down in the evening.
5. **Switch protocols.** If YouTube won't load on any server, try a different protocol in the app. Some traffic types get throttled harder than others.
6. **Clear the app cache.** On Android: Settings → Apps → YouTube → Storage → Clear cache. On iPhone it's easier to delete and reinstall the app. Subscriptions and history live in your Google account and won't be lost.
7. **Check DNS.** If your phone or browser has your provider's DNS set manually, it may return the wrong address for YouTube. In the browser you can turn on Secure DNS; on Android check the Private DNS setting. Normally DNS goes through the tunnel when the VPN is on, but old settings sometimes get in the way.

If nothing at all loads with the VPN on, see [VPN connected but no internet](/en/blog/vpn-podklyuchen-no-net-interneta/). TikTok stuck on an old feed even with a VPN is covered in [TikTok not working in Russia even with a VPN](/en/blog/tiktok-ne-rabotaet-s-vpn/).

## If it only fails on mobile data

During restrictions, mobile internet in Russia often switches to a whitelist: banks, marketplaces, Gosuslugi and other Russian services, around 900 resources according to the Ministry of Digital Development. YouTube isn't on it, and a regular VPN often can't connect in this mode. The simplest fix is to switch to home or office Wi-Fi, where restrictions are usually milder.

## FAQ

### Why does YouTube work in the browser but not in the app?
Most likely the app is excluded from the VPN or holding an old connection. Check the exclusion list in your VPN app and restart YouTube.

### Why is video stuck at low quality?
Usually an overloaded or distant server. Switch country and set the quality manually in the video settings instead of "Auto".

### Why is YouTube slower in the evening?
That's when the most people watch video through the same servers at once. Switching server or protocol helps.

### Is it just me or everyone?
Check the [outage status page](/en/status/): if there are fresh complaints about YouTube or mobile internet in your region, the problem isn't on your side.
