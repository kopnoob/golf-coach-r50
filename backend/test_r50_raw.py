"""Rå R50-protokolltest.

Kobler til R50 og prøver å:
1. Lese rå bytes (i tilfelle R50 sender noe først)
2. Sende ulike handshake-forsøk
3. Logge alt som skjer for analyse
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import struct
import sys
import time

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")
from app.r50.connector import R50Discovery


async def raw_connect_test():
    """Koble til R50 og logg alt som skjer på byte-nivå."""

    # Finn R50
    logger.info("Søker etter R50...")
    found = asyncio.Event()
    host_port = []

    def on_found(name, ip, port):
        host_port.append((ip, port))
        found.set()

    discovery = R50Discovery()
    discovery.start(on_found=on_found)

    try:
        await asyncio.wait_for(found.wait(), timeout=15)
    except asyncio.TimeoutError:
        logger.error("Fant ingen R50")
        discovery.stop()
        return

    ip, port = host_port[0]
    discovery.stop()

    logger.info("Kobler til %s:%d...", ip, port)
    reader, writer = await asyncio.open_connection(ip, port)
    logger.info("Tilkoblet!")

    # Steg 1: Sjekk om R50 sender noe av seg selv (2 sek)
    logger.info("--- STEG 1: Lytter etter data fra R50 (2 sek) ---")
    try:
        data = await asyncio.wait_for(reader.read(4096), timeout=2.0)
        if data:
            logger.info("R50 sendte %d bytes: %s", len(data), data[:200])
            logger.info("Hex: %s", data[:100].hex())
            # Prøv å tolke som framed melding
            if len(data) >= 4:
                length = struct.unpack(">I", data[:4])[0]
                logger.info("Tolket som framed: length=%d, payload=%s", length, data[4:4+min(length, 200)])
        else:
            logger.info("R50 sendte ingenting")
    except asyncio.TimeoutError:
        logger.info("Ingen data fra R50 innen 2 sek — vi må sende noe først")

    # Steg 2: Prøv ulike handshake-meldinger
    handshakes = [
        # Forsøk 1: Tom JSON
        {"type": "hello"},
        # Forsøk 2: GSPro-lignende handshake
        {"type": "handshake", "version": "1.0"},
        # Forsøk 3: Identifisering
        {"DeviceID": "GolfCoachR50", "APIversion": "1"},
        # Forsøk 4: Connect-melding
        {"message": {"type": "connect", "data": {"name": "GSPro", "version": "1.0"}}},
    ]

    for i, handshake in enumerate(handshakes):
        logger.info("--- STEG 2.%d: Sender handshake: %s ---", i+1, json.dumps(handshake)[:100])

        # Send som framed melding (4-byte length + JSON)
        payload = json.dumps(handshake).encode("utf-8")
        frame = struct.pack(">I", len(payload)) + payload
        writer.write(frame)
        await writer.drain()

        # Vent på svar
        try:
            data = await asyncio.wait_for(reader.read(4096), timeout=3.0)
            if data:
                logger.info("SVAR! %d bytes: %s", len(data), data[:200])
                logger.info("Hex: %s", data[:100].hex())
                # Prøv JSON-parsing
                if len(data) >= 4:
                    length = struct.unpack(">I", data[:4])[0]
                    json_data = data[4:4+length]
                    try:
                        parsed = json.loads(json_data)
                        logger.info("Parsed JSON: %s", json.dumps(parsed, indent=2)[:500])
                    except:
                        logger.info("Kunne ikke parse som JSON")
                break  # Fikk svar, stopp
            else:
                logger.info("Tilkobling lukket av R50")
                return
        except asyncio.TimeoutError:
            logger.info("Ingen svar innen 3 sek")

        # Sjekk om tilkoblingen fortsatt er åpen
        if reader.at_eof():
            logger.info("R50 lukket tilkoblingen")
            break

    # Steg 3: Fortsett å lytte etter data
    logger.info("--- STEG 3: Lytter etter ytterligere data (10 sek) ---")
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            data = await asyncio.wait_for(reader.read(4096), timeout=2.0)
            if data:
                logger.info("Data: %d bytes: %s", len(data), data[:200])
                logger.info("Hex: %s", data[:100].hex())
            else:
                logger.info("Tilkobling lukket")
                break
        except asyncio.TimeoutError:
            continue

    writer.close()
    logger.info("Test ferdig.")


asyncio.run(raw_connect_test())
