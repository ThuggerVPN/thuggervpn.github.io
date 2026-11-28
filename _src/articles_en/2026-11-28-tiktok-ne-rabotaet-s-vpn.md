---
title: TikTok not working in Russia even with a VPN: old feed and how to fix it
description: VPN is on but TikTok in Russia still shows a 2022 feed, won't load videos or says no connection. Why it happens and a step-by-step fix.
date: 2026-11-28
slug: tiktok-ne-rabotaet-s-vpn
cta: VPN on and TikTok still stuck in the past? Test ThuggerVPN on your carrier: 3 days free.
---
<p class="lead"><b>In short:</b> when TikTok doesn't work in Russia even with a VPN, it's usually one of three things. The app still remembers the Russian region (from your SIM card, an old session or the cache), TikTok traffic is bypassing the VPN, or mobile data is in whitelist mode and nothing reaches the VPN at all. Close TikTok completely, turn the VPN on, clear the cache and open the app again. Step by step below.</p>

## What's going on with TikTok in Russia

Russia's regulator Roskomnadzor never blocked TikTok: the app is in the App Store and Google Play and the website opens. The restrictions came from TikTok itself. In March 2022 it stopped new uploads and live streams for users in Russia. That's why, without a VPN, the feed looks like an archive: old clips and almost nothing new.

With a VPN most people get the global feed. That's also where the complaints start: the VPN is on, but the feed is still old, videos won't load, or the app says there's no internet connection.

## Find the cause first

| What you see | Most likely |
|---|---|
| VPN is on, but the feed is as old as without it | TikTok remembers the Russian region: old session, cache or SIM card |
| "No internet connection", while other sites open through the VPN | TikTok bypasses the VPN (app exclusions) or the server is a poor fit |
| Videos keep spinning, especially in the evening | overloaded or distant server |
| On mobile data nothing loads except banks and Gosuslugi | mobile whitelist mode |
| Works on Wi-Fi, not on mobile data | carrier restrictions, not TikTok |

## What to do: 7 steps

1. **Check that the VPN actually works.** Turn it on and open our [connection check](/en/check/). If it shows a Russian IP, traffic is going around the VPN and TikTok isn't the problem.
2. **Turn the VPN on before you open TikTok.** The app picks up the region at launch. Swipe TikTok away from your recent apps, connect the VPN, then open it.
3. **Check the exclusion list in your VPN app.** Many clients let some apps bypass the VPN (split tunneling). If TikTok is on that list, it goes direct. Remove it.
4. **Clear the TikTok cache.** In the app: Profile → menu ☰ → Settings and privacy → Free up space → Cache → Clear. Your account and follows stay. If that doesn't help, reinstall the app.
5. **Switch servers.** If videos stutter, pick another country. Popular servers slow down in the evening and short videos start buffering.
6. **Mind the SIM card.** TikTok decides your region not only by IP but also by SIM card and phone settings. That's why some people with a Russian SIM keep the "Russian" feed even on a VPN, while a tablet without a SIM works fine. This is TikTok's own rule, and a VPN can't always change it.
7. **Sign out and back in.** Log out with the VPN on and log in again. Sometimes that's enough for TikTok to refresh the region.

If nothing opens at all with the VPN on, see [VPN connected but no internet](/en/blog/vpn-podklyuchen-no-net-interneta/). If the VPN keeps dropping on Android, read [VPN on Android disconnects by itself](/en/blog/vpn-na-android-otklyuchaetsya/), and there's [a separate guide for iPhone](/en/blog/vpn-na-iphone-ne-rabotaet/).

## If TikTok only fails on mobile data

During restrictions, Russian mobile internet often works only for a whitelist of approved services: Gosuslugi, VKontakte, Yandex, marketplaces, banks. TikTok isn't on it, and a regular VPN often can't connect in that mode. You can check whether whitelist mode is on with our [internet check](/en/check/#wl). The simplest fix is to switch to home or office Wi-Fi. Fresh outages by region are on the [blocking status page](/en/status/), and we explain the whitelist mode in [VPN with whitelists](/en/blog/vpn-s-belymi-spiskami/).

## FAQ

### Why is my TikTok feed old even with a VPN?
TikTok remembered the Russian region. Close the app fully, turn the VPN on, clear the cache and reopen it. With a Russian SIM card the region may be taken from the SIM.

### Is TikTok blocked in Russia?
No, Roskomnadzor hasn't blocked it. The limits on new videos from Russia were introduced by TikTok itself in 2022.

### Why does TikTok say "No internet connection" with a VPN on?
Usually TikTok is bypassing the VPN or the server is overloaded. Check the exclusion list in your VPN app and switch servers.

### Does TikTok work for travellers in Russia?
Usually yes, through a VPN, but the first day on a foreign SIM can be tricky: see [the 24-hour block on foreign SIM cards](/en/blog/foreign-sim-24-hour-block-russia/).
