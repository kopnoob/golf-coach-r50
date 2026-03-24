"""Test direkte tilkobling til Garmin R50 over lokalt nettverk.

Bruk: Slå på R50, koble den til WiFi, og kjør dette skriptet.
     python3 test_r50_live.py

Skriptet vil:
1. Søke etter R50 på nettverket via mDNS
2. Koble til den
3. Lytte på slagdata og skrive dem ut
"""
from __future__ import annotations

import asyncio
import json
import sys
sys.path.insert(0, ".")

from app.r50.connector import R50Discovery, R50Monitor


async def test_discovery_only():
    """Bare søk etter R50 på nettverket (10 sek)."""
    print("Søker etter Garmin R50 på nettverket (10 sekunder)...")
    print("Sørg for at R50 er påslått og koblet til WiFi.\n")

    discovery = R50Discovery()

    def on_found(name, ip, port):
        print(f"  FUNNET: {name} på {ip}:{port}")

    discovery.start(on_found=on_found)
    await asyncio.sleep(10)
    discovery.stop()

    if discovery.devices:
        print(f"\nFant {len(discovery.devices)} R50-enhet(er)!")
        for name, (ip, port) in discovery.devices.items():
            print(f"  {name}: {ip}:{port}")
    else:
        print("\nIngen R50 funnet. Sjekk at:")
        print("  1. R50 er påslått")
        print("  2. R50 er koblet til samme WiFi-nettverk som denne maskinen")
        print("  3. mDNS/Bonjour er ikke blokkert av brannmur")


async def test_full_connection():
    """Koble til R50 og lytt på slagdata."""
    print("Kobler til Garmin R50...")
    print("Slå noen baller når tilkoblingen er etablert!\n")

    monitor = R50Monitor()
    ok = await monitor.discover_and_connect(timeout=15)

    if not ok:
        print("Kunne ikke koble til R50.")
        return

    print("Tilkoblet! Venter på slag... (Ctrl+C for å stoppe)\n")

    shot_count = 0
    try:
        async for shot in monitor.listen():
            shot_count += 1
            print(f"\n{'='*50}")
            print(f"SLAG #{shot_count}")
            print(f"{'='*50}")
            for key, value in shot.items():
                if value is not None:
                    print(f"  {key}: {value}")
            print()
    except KeyboardInterrupt:
        print(f"\nStoppet. Mottok {shot_count} slag.")
    finally:
        await monitor.stop()


async def main():
    if "--discover" in sys.argv:
        await test_discovery_only()
    else:
        await test_full_connection()


asyncio.run(main())
