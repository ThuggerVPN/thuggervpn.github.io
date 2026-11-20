---
title: VPN not working on mobile data in Russia: what to do in 2026
description: Step by step: why VPNs drop on MTS, Beeline, MegaFon and T2, and how to get access back in a couple of minutes.
date: 2026-11-19
slug: ne-rabotaet-vpn-na-mobilnom
---
<p class="lead"><b>In short:</b> it's usually not your phone or the app - it's restrictions on the mobile network. First figure out which case you have; that decides what will help.</p>

## Step 1. Find out what exactly broke

| Symptom | Cause | What helps |
|---|---|---|
| Nothing opens, not even Gosuslugi or Yandex | Mobile internet is fully shut down | Only Wi-Fi or home internet |
| Gosuslugi and Yandex open, nothing else does, VPN won't connect | Whitelist mode | Wi-Fi or a VPN with whitelist bypass |
| Everything opens except what you used the VPN for | Your VPN's server or protocol is blocked | Change server, protocol or service |
| VPN "connected" but pages don't load | The hosting subnet is blocked | Change server - or better, the VPN provider |

## Step 2. Quick fixes

1. **Toggle airplane mode.** The phone re-registers on the network - sometimes that's enough.
2. **Change the VPN server.** Specific addresses get blocked, not the whole VPN. Another country or server often works right away.
3. **Refresh the configuration.** Update the subscription in the app. Good services push new settings within an hour of a new blocking wave.
4. **Try Wi-Fi.** If it works on Wi-Fi but not on mobile, the problem is carrier restrictions, not the VPN.

## Step 3. If nothing helped

Your service is probably not keeping up with the blocks. In 2026 WireGuard, OpenVPN, some VLESS configurations and whole hosting subnets got restricted. The services that survive:

- use modern protocols that disguise traffic;
- change servers and update configurations quickly;
- have live support that replies within an hour.

Keep two VPNs: a main one and a backup. How to choose - see [how to choose a VPN in 2026](/en/blog/kak-vybrat-vpn-2026/).

## FAQ

### Why did my VPN stop working on MTS but still works on Wi-Fi?
Filtering is stricter on mobile networks, and during restrictions a whitelist mode is switched on. Home internet isn't affected by whitelists, so the same VPN keeps working on Wi-Fi.

### Will reinstalling the VPN app help?
Rarely. The problem is almost always the network or a blocked server, not the app. Change the server and refresh the configuration first.

### Should I switch VPNs if it's down for a day?
Not necessarily. If the service recovers within a few hours, that's normal. If outages repeat every week and support stays silent, it's time for a replacement.
