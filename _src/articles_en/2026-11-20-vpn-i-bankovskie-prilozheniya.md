---
title: Russian bank apps not working with VPN: Sber, T-Bank, Ozon fixes
description: Why Russian banking, marketplace and carrier apps block or warn you when a VPN is on - at home and abroad - and how to use them without hassle.
date: 2026-11-20
slug: vpn-i-bankovskie-prilozheniya
---
<p class="lead"><b>In short:</b> since spring 2026 many Russian apps - banks, marketplaces, mobile carrier accounts - restrict access when a VPN is on. The easiest fix is split tunneling: the VPN handles blocked services while your bank and shopping apps connect directly.</p>

## What's going on

In late March 2026 Russia's Ministry of Digital Development met with major companies. According to media reports, minister Maksut Shadaev said services should restrict access for users with a VPN turned on "by April 15". No decree or law was cited in those reports, but from April apps started reacting to VPNs on a large scale.

What users saw, according to URA.RU and Verstka:

| Service | What happens with a VPN on |
|---|---|
| Sberbank, T-Bank | apps partly unavailable |
| Yandex Pay | no login, citing "a regulator requirement" |
| Wildberries, Ozon | a warning; products or orders may not load |
| MTS, MegaFon, Beeline | a warning that data may not display |
| Kinopoisk, Wink | stop working |

Kremlin spokesman Dmitry Peskov said at the time that there is no liability for simply using a VPN. This is not legal advice - rules can change.

## How an app knows you're on a VPN

Mostly by IP address: hosting and VPN provider ranges are well known. Another signal is location "jumps" - Moscow one minute, the Netherlands the next. So even a working VPN will almost always trigger a warning in a banking app.

## What to do: 4 options that work

1. **Turn on split tunneling.** In your VPN client look for "Split tunneling", "Exclusions" or "Apps that bypass VPN". Add your bank, marketplaces and Gosuslugi - they'll connect directly, everything else goes through the VPN.
2. **Switch the VPN off while you pay.** Simple if your client has no exclusions. Done with the bank - turn it back on.
3. **Don't keep the VPN on "just in case" on your phone.** Turn it on for the services that need it, and you'll see fewer warnings.
4. **Don't try to trick your bank.** Banking apps already encrypt the connection, they don't need a VPN. Frequent country and IP changes can also alarm the bank's anti-fraud system.

If the VPN is on but there's no internet at all, the problem may be the network, not the bank: check the [outage and whitelist status](/en/status/) and our guide [VPN connected but no internet](/en/blog/vpn-podklyuchen-no-net-interneta/).

## If you're outside Russia

In spring 2026 Russians in Turkey, Egypt, Thailand and Vietnam complained that banking, marketplace and airline apps treated them as VPN users and restricted access - even with no VPN running. It's hard for a service to tell foreign traffic from VPN traffic. According to the same reports, people in CIS countries didn't have this problem.

What helps:

- keep a Russian SIM with a data package for urgent tasks - the Association of Tour Operators of Russia recommends this (mind the roaming costs);
- before you leave, check that your bank app opens and that PIN or biometric login is set up;
- make important payments before the trip.

## FAQ

### Will my account be frozen if I open the bank app with a VPN?
The reports were about restricting access to the app, not about freezing accounts. Usually the bank shows a warning or won't let you in while the VPN is on.

### Why does my bank app work on Wi-Fi but not on mobile data?
Mobile internet may be in whitelist mode or your carrier may be having problems. Bank apps are often on the whitelist, VPNs are not. Check the [status page](/en/status/).

### Does every VPN have split tunneling?
No, it depends on the client app. It's more common on Android, less so on iPhone. If yours doesn't have it, switch the VPN off while you use the bank.

### Do I need a VPN for Gosuslugi?
No. Gosuslugi and banks work directly in Russia, and with a VPN they may load worse. Add them to exclusions.
