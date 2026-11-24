---
title: VPN keeps disconnecting on Android in Russia: causes and fixes
description: Your Android VPN drops when the screen turns off, when switching from Wi-Fi to mobile data or after a few minutes. Why it happens and settings to fix it.
date: 2026-11-24
slug: vpn-na-android-otklyuchaetsya
---
<p class="lead"><b>In short:</b> when a VPN keeps disconnecting on Android, the cause is usually the phone, not the server. The system saves battery by killing apps in the background, and Xiaomi, Samsung, Honor and Realme are especially aggressive about it. Three settings fix most cases: remove battery restrictions for the VPN app, turn on Always-on VPN and allow background activity. If it only drops on mobile data in Russia, network restrictions may be the reason, not your phone.</p>

## When exactly does it drop?

| What happens | Most likely |
|---|---|
| Disconnects 5-15 minutes after you lock the screen | battery optimisation kills the app |
| Drops when you move from Wi-Fi to mobile data | the tunnel doesn't reconnect to the new network in time |
| Disconnects when you clear recent apps | the phone's skin closes the client completely |
| VPN key icon is shown, but nothing loads | server not responding or outdated subscription |
| Works on Wi-Fi, never on mobile data | whitelist mode or a mobile internet shutdown |

## What to do: 6 steps

1. **Remove battery restrictions.** Go to Settings → Apps → your VPN client → Battery and pick Unrestricted (on some phones it's called Don't optimise). This matters most: without it Android will put the VPN to sleep sooner or later.
2. **Turn on Always-on VPN.** Settings → Network & internet (on Samsung: Connections → More connection settings) → VPN → gear icon next to your client → Always-on VPN. The system will then bring the tunnel back after a reboot or a drop. Be careful with Block connections without VPN: if the server is unreachable, you lose internet completely, including banks and whitelisted apps.
3. **Adjust your phone maker's settings.** Stock Android settings are often not enough.
   - Xiaomi and Redmi (MIUI, HyperOS): in the app's settings enable Autostart, and under Battery saver choose No restrictions. In the recent apps screen, pull the VPN card down and lock it so cleanup doesn't close it.
   - Samsung: Battery (or Battery and device care) → Background usage limits. Make sure the client isn't in Sleeping apps or Deep sleeping apps, and add it to Never sleeping apps.
   - Honor, Huawei, Realme, OPPO: look in battery settings for App launch, Background activity or High background power consumption and allow them for the VPN.
4. **Turn off Data Saver and Battery Saver.** Both limit what apps can do in the background. If you need Data Saver, add the VPN client as an exception (Unrestricted data).
5. **Remove the second VPN.** Android runs only one VPN at a time. Another client, a work VPN or a gaming "booster" can steal the connection. Also check Private DNS: if a server is typed in manually, try Automatic.
6. **Refresh the subscription and switch servers.** If the VPN drops no matter what, tap update in the app or paste the link from the bot again. The full setup is in our [connection guide](/en/podklyuchenie/).

## If it only drops on mobile data

During restrictions in Russia, mobile internet is switched to whitelist mode: banks, Gosuslugi and marketplaces open, almost everything else doesn't. A VPN may connect and drop straight away in those hours, and no phone setting will change that. Check the [outage status page](/en/status/) to see whether there's a shutdown in your region right now. More on whitelists in [VPN not working on mobile data in Russia](/en/blog/ne-rabotaet-vpn-na-mobilnom/).

## If the app disappeared from Google Play

Roskomnadzor regularly demands that Google remove apps for bypassing blocks, and in April 2026 the number of such demands hit a record, according to iStories. An app that is already installed normally stays on your phone. Don't uninstall a working client without a reason: you may not be able to get it back from the Russian Google Play. Many clients publish an installation file (APK) on their own website or GitHub. Download it only from there, not from random APK sites.

## FAQ

### Why does my VPN disconnect on Android when the screen turns off?
The system puts the app to sleep to save battery. Set the VPN client to Unrestricted in battery settings and turn on Always-on VPN.

### Should I enable "Block connections without VPN"?
Only if you need every request to go through the tunnel. The downside: if the VPN drops, you lose internet entirely, and in whitelist mode even allowed services won't open.

### The VPN is on but apps say there's no network. Is that the same problem?
No, that's a different issue: the tunnel is up, but traffic isn't flowing. See [VPN connected but no internet](/en/blog/vpn-podklyuchen-no-net-interneta/) for a step-by-step fix.

### How do I check that the VPN really works?
Open the [connection check](/en/check/) with the VPN on. If you see a Russian IP, your traffic is bypassing the tunnel.
