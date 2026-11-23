---
title: VPN not working on iPhone in Russia: why it won't connect and fixes
description: VPN on your iPhone won't turn on, keeps disconnecting or shows connected but loads nothing in Russia. Causes and a step-by-step checklist for iOS.
date: 2026-11-23
slug: vpn-na-iphone-ne-rabotaet
---
<p class="lead"><b>In short:</b> when a VPN on your iPhone won't connect in Russia, or connects but nothing loads, it's usually one of five things: an old or broken VPN profile in iOS settings, an outdated subscription link in the app, Low Power Mode, whitelist mode on mobile data, or a clash with another VPN profile. Below is a checklist in order. It takes 5-10 minutes.</p>

## Figure out what's actually wrong

| What you see | Most likely |
|---|---|
| The VPN toggle won't stay on | broken VPN profile in iOS or two profiles clashing |
| VPN icon is shown, but pages don't load | dead server or outdated subscription |
| Works on Wi-Fi, fails on mobile data | whitelist mode or carrier restrictions |
| Drops when the phone is locked | Low Power Mode or iOS killing the app |
| The app is gone from the App Store | removed from the Russian store, an installed copy usually keeps working |

## What to do: 7 steps

1. **Check the internet without the VPN.** Turn the VPN off and open any website. If nothing loads without it either, the problem is the network, not the VPN. Check the [outage status page](/en/status/) to see if there's a shutdown in your region right now.
2. **Look at VPN profiles in Settings.** Go to Settings → General → VPN & Device Management → VPN. If you see several configurations left over from old apps, delete the extra ones (tap "i" next to a profile → Delete VPN). An iPhone can't run two VPNs at once, and an old profile sometimes grabs the connection.
3. **Refresh the subscription in your app.** In clients like Happ, Streisand or V2Box, servers come from a subscription link. If the provider changed servers or protocols, the old link stops working. Tap update in the app or paste the link from the bot again. The full setup is in our [connection guide](/en/podklyuchenie/).
4. **Switch server or protocol.** If the subscription is fresh but still no connection, try another country. A specific server or type of traffic can be blocked harder than others.
5. **Turn off Low Power Mode.** In this mode iOS closes background apps more aggressively, and the VPN may drop when the screen goes dark. Check Settings → Battery. If your client has Connect On Demand, switch it on.
6. **Reset network settings.** If nothing else helps: Settings → General → Transfer or Reset iPhone → Reset → Reset Network Settings. This wipes saved Wi-Fi passwords and VPN profiles, but also any stuck settings. Add the subscription to your app again afterwards.
7. **Update iOS and the app.** Old client versions sometimes don't support newer protocols the server uses.

## If the app was removed from the App Store

Apple removes VPN clients from the Russian App Store at the request of Roskomnadzor, Russia's internet regulator. At the end of March 2026, Streisand, V2Box, v2RayTun and Happ - Proxy Utility disappeared from it, and on 27 October 2026 Incy was removed. According to Apple's own data, 1,213 apps were taken down from the Russian store at the authorities' request in 2025.

If the app is already on your phone, it keeps working but stops getting updates, according to the Russian tech outlet Kod Durova. So don't delete a working client just to test something: you may not be able to download it again from a Russian Apple account. If you live abroad and use a non-Russian Apple account, these apps are usually still available there.

## If it fails only on mobile data

During restrictions, Russian mobile data often opens only whitelisted services: banks, Gosuslugi, marketplaces. A regular VPN may not connect at all in this mode, and your iPhone isn't broken. Switch to Wi-Fi or wait until the restriction is lifted. More in our guide [VPN not working on mobile data in Russia](/en/blog/ne-rabotaet-vpn-na-mobilnom/).

## FAQ

### Why does my iPhone VPN turn on and immediately turn off?
Usually it's a broken or conflicting VPN profile in iOS settings. Delete extra configurations under VPN & Device Management and connect again from the app.

### Why does the VPN disconnect when my iPhone is locked?
Most likely iOS is unloading the app from memory, especially in Low Power Mode. Turn that mode off and enable Connect On Demand in the client if it has one.

### Will an app removed from the App Store still work?
According to media reports, apps already installed keep working, just without updates. There's no guarantee, so it's better not to delete a client that works.

### How do I know the VPN is really working?
Open the [connection check](/en/check/) with the VPN on. If it shows a Russian IP, your traffic is going around the tunnel.
