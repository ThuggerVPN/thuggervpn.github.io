---
title: VPN connected but no internet: 5 causes and fixes
description: Why your VPN says "connected" but pages won't load, and how to fix it in five minutes.
date: 2026-11-19
slug: vpn-podklyuchen-no-net-interneta
---
<p class="lead"><b>In short:</b> "connected" only means the app started the tunnel. If no traffic flows, it's being cut along the way. Changing the server helps most often.</p>

## Cause 1. The server's IP address is blocked

The most common case. Specific addresses get blocked, not the whole service - sometimes entire subnets of a hosting provider. Symptom: "connected but no traffic" on all servers in one country.

**Fix:** change the server. If switching countries within the same service doesn't help, the problem is its hosting - you need a different VPN.

## Cause 2. The protocol is blocked

WireGuard and OpenVPN practically don't work in Russia now, and other protocols get restricted too.

**Fix:** if the app lets you choose a protocol, try another one. If not, refresh the configuration or subscription - the service may already have released working settings.

## Cause 3. Whitelist mode is on

During restrictions, mobile internet only allows approved services. VPNs aren't on that list.

**Fix:** switch to Wi-Fi. More in [what whitelists are](/en/blog/belye-spiski-chto-eto/).

## Cause 4. Wrong time or date on your phone

Some protocols check the time. If the date is wrong or automatic time is off, the connection fails.

**Fix:** in settings, turn on "Date & time - automatic".

## Cause 5. Conflict with another VPN or proxy

Two VPN apps, or a proxy enabled in Telegram and the system, can interfere with each other.

**Fix:** close extra VPN apps, turn off proxies and reconnect.

## 5-minute routine

1. Change the server.
2. Refresh the subscription or configuration.
3. Test on Wi-Fi.
4. Check date and time.
5. Close other VPNs.

If it still doesn't work, contact your VPN's support. If support is silent for more than a day, keep a backup service.

## FAQ

### My VPN worked yesterday; today it's "connected" but nothing opens. Why?
Most likely the server address or hosting subnet got blocked overnight. Change the server or refresh the configuration.

### Does restarting the phone help?
Sometimes, if the problem is the network itself. But if the server is blocked, a restart changes nothing - you need another server.
