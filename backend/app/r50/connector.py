"""Direkte tilkobling til Garmin Approach R50 over lokalt nettverk.

Oppdager R50 via mDNS, kobler til via TCP, dekrypterer slagdata.

Protokoll (reverse-engineered fra GSPconnect.exe):
- mDNS service: _garmin-golf-launch-monitor-api-service._tcp
- Framing: 4-byte big-endian length prefix + JSON payload
- Kryptering: RSA-OAEP-SHA1 handshake + AES-128-CBC per melding
- Slagdata: JSON med ball/club metrics i m/s og radianer
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import math
import struct
from pathlib import Path
from typing import AsyncGenerator, Callable, Optional

from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_garmin-golf-launch-monitor-api-service._tcp.local."
KEY_FILE = Path(__file__).parent / "r50_key.pem"


def _load_rsa_key() -> Optional[str]:
    """Last RSA-nøkkel fra fil (om tilgjengelig)."""
    if KEY_FILE.exists():
        return KEY_FILE.read_text()
    return None


# Konverteringsfaktorer
MPS_TO_KMH = 3.6
RAD_TO_DEG = 180.0 / math.pi


class R50Discovery:
    """Oppdager Garmin R50 på lokalt nettverk via mDNS."""

    def __init__(self) -> None:
        self._zeroconf: Optional[Zeroconf] = None
        self._browser: Optional[ServiceBrowser] = None
        self._found_devices: dict[str, tuple[str, int]] = {}
        self._on_found: Optional[Callable] = None

    def start(self, on_found: Optional[Callable] = None) -> None:
        """Start mDNS-søk etter R50-enheter."""
        self._on_found = on_found
        self._zeroconf = Zeroconf()
        self._browser = ServiceBrowser(
            self._zeroconf, SERVICE_TYPE, handlers=[self._on_service_state_change]
        )
        logger.info("Søker etter Garmin R50 på nettverket...")

    def stop(self) -> None:
        if self._zeroconf:
            self._zeroconf.close()

    def _on_service_state_change(self, zeroconf: Zeroconf, service_type: str, name: str, state_change) -> None:
        info = zeroconf.get_service_info(service_type, name)
        if info and info.addresses:
            import socket
            ip = socket.inet_ntoa(info.addresses[0])
            port = info.port
            self._found_devices[name] = (ip, port)
            logger.info("Fant R50: %s på %s:%d", name, ip, port)
            if self._on_found:
                self._on_found(name, ip, port)

    @property
    def devices(self) -> dict[str, tuple[str, int]]:
        return self._found_devices.copy()


class R50Connection:
    """TCP-tilkobling til R50 med meldingsframing."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False

    async def connect(self) -> bool:
        """Koble til R50 via TCP."""
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self.host, self.port
            )
            self._connected = True
            logger.info("Koblet til R50 på %s:%d", self.host, self.port)
            return True
        except Exception as e:
            logger.error("Kunne ikke koble til R50: %s", e)
            return False

    async def disconnect(self) -> None:
        if self._writer:
            self._writer.close()
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def read_message(self) -> Optional[dict]:
        """Les én melding fra R50 (4-byte length prefix + JSON).

        Håndterer både ukrypterte og krypterte meldinger (iv/sk/pl envelope).
        """
        if not self._reader:
            return None
        try:
            # Les 4-byte length prefix (big-endian uint32)
            length_bytes = await self._reader.readexactly(4)
            length = struct.unpack(">I", length_bytes)[0]

            if length > 1_000_000:  # Sanity check
                logger.warning("Urimelig stor melding: %d bytes", length)
                return None

            # Les payload
            payload = await self._reader.readexactly(length)
            data = json.loads(payload.decode("utf-8"))

            # Sjekk om meldingen er kryptert (har iv/sk/pl felter)
            if isinstance(data, dict) and "pl" in data and "sk" in data and "iv" in data:
                decrypted = self._try_decrypt(data)
                if decrypted:
                    return decrypted
                # Kan ikke dekryptere — logg rå envelope for debugging
                logger.debug("Kryptert melding (kan ikke dekryptere): iv=%s...", str(data["iv"])[:20])
                return {"_encrypted": True, "_raw": data}

            return data

        except asyncio.IncompleteReadError:
            logger.info("R50 lukket tilkoblingen")
            self._connected = False
            return None
        except Exception as e:
            logger.error("Feil ved lesing fra R50: %s", e)
            return None

    def _try_decrypt(self, envelope: dict) -> Optional[dict]:
        """Forsøk å dekryptere en R50-melding.

        Protokoll:
          iv: base64(hex_string) → raw bytes
          sk: RSA-OAEP-SHA1 kryptert sesjonsnøkkel (base64)
          pl: AES-128-CBC + PKCS7 kryptert payload (base64)

        Returnerer None hvis vi ikke har nøklene.
        """
        rsa_key_pem = _load_rsa_key()
        if not rsa_key_pem:
            return None

        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

            # Last RSA-nøkkel
            private_key = serialization.load_pem_private_key(
                rsa_key_pem.encode(), password=None
            )

            # Dekod IV: base64 → hex string → bytes
            iv_hex = base64.b64decode(envelope["iv"]).decode("utf-8")
            iv = bytes.fromhex(iv_hex)

            # Dekrypter sesjonsnøkkel med RSA-OAEP-SHA1
            sk_encrypted = base64.b64decode(envelope["sk"])
            session_key = private_key.decrypt(
                sk_encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA1()),
                    algorithm=hashes.SHA1(),
                    label=None,
                ),
            )

            # Dekrypter payload med AES-128-CBC
            pl_encrypted = base64.b64decode(envelope["pl"])
            cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded = decryptor.update(pl_encrypted) + decryptor.finalize()

            # Fjern PKCS7 padding
            pad_len = padded[-1]
            plaintext = padded[:-pad_len]

            return json.loads(plaintext.decode("utf-8"))

        except Exception as e:
            logger.debug("Dekryptering feilet: %s", e)
            return None

    async def send_message(self, data: dict) -> None:
        """Send en melding til R50."""
        if not self._writer:
            return
        payload = json.dumps(data).encode("utf-8")
        length = struct.pack(">I", len(payload))
        self._writer.write(length + payload)
        await self._writer.drain()


def parse_shot_from_r50(message: dict) -> Optional[dict]:
    """Konverter R50-slagmelding til vårt format.

    R50 sender hastigheter i m/s og vinkler i radianer.
    Vi konverterer til km/t og grader.
    """
    msg_type = message.get("message", {}).get("type", "")

    if msg_type not in ("shot", "shotData", "launchData"):
        return None

    data = message.get("message", {}).get("data", message.get("data", message))

    ball = data.get("ballData", data.get("ball", {}))
    club = data.get("clubData", data.get("club", {}))

    def mps_to_kmh(v):
        return round(v * MPS_TO_KMH, 1) if v is not None else None

    def rad_to_deg(v):
        return round(v * RAD_TO_DEG, 1) if v is not None else None

    def safe_get(d, *keys):
        for k in keys:
            v = d.get(k)
            if v is not None:
                return v
        return None

    return {
        "club": data.get("club", data.get("clubType", "")),
        "ball_speed": mps_to_kmh(safe_get(ball, "speed", "ballSpeed")),
        "launch_angle": rad_to_deg(safe_get(ball, "vla", "launchAngle", "verticalAngle")),
        "launch_direction": rad_to_deg(safe_get(ball, "hla", "launchDirection", "horizontalAngle")),
        "spin_rate": safe_get(ball, "totalSpin", "spinRate"),
        "spin_axis": rad_to_deg(safe_get(ball, "spinAxis")),
        "club_head_speed": mps_to_kmh(safe_get(club, "speed", "clubSpeed", "clubHeadSpeed")),
        "club_face_angle": rad_to_deg(safe_get(club, "faceToTarget", "faceAngle")),
        "club_path": rad_to_deg(safe_get(club, "path", "clubPath")),
        "angle_of_attack": rad_to_deg(safe_get(club, "angleOfAttack", "attackAngle")),
        "smash_factor": safe_get(data, "smashFactor"),
        "carry_distance": safe_get(ball, "carryDistance", "carry"),
        "total_distance": safe_get(ball, "totalDistance", "total"),
        "apex_height": safe_get(ball, "apexHeight", "apex"),
        "total_deviation": safe_get(ball, "offline", "deviation", "totalDeviation"),
    }


class R50Monitor:
    """Høynivå-klasse som oppdager, kobler til og lytter på R50.

    Bruk:
        monitor = R50Monitor()
        async for shot in monitor.listen():
            print(shot)
    """

    def __init__(self) -> None:
        self._discovery = R50Discovery()
        self._connection: Optional[R50Connection] = None
        self._running = False

    async def discover_and_connect(self, timeout: float = 30.0) -> bool:
        """Søk etter R50 og koble til den første som finnes."""
        found = asyncio.Event()
        host_port: list = []

        def on_found(name, ip, port):
            host_port.append((ip, port))
            found.set()

        self._discovery.start(on_found=on_found)

        try:
            await asyncio.wait_for(found.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Fant ingen R50 på nettverket (timeout %ds)", timeout)
            self._discovery.stop()
            return False

        ip, port = host_port[0]
        self._connection = R50Connection(ip, port)
        ok = await self._connection.connect()
        self._discovery.stop()
        return ok

    async def listen(self) -> AsyncGenerator[dict, None]:
        """Lytt etter slagdata fra R50. Yielder parsed shot dicts."""
        if not self._connection or not self._connection.is_connected:
            logger.error("Ikke koblet til R50")
            return

        self._running = True
        logger.info("Lytter på slagdata fra R50...")

        while self._running and self._connection.is_connected:
            message = await self._connection.read_message()
            if message is None:
                if self._connection.is_connected:
                    await asyncio.sleep(0.1)
                    continue
                break

            # Prøv å parse som slagdata
            shot = parse_shot_from_r50(message)
            if shot:
                logger.info(
                    "Nytt slag: %s carry=%.1f ball_speed=%.1f",
                    shot.get("club", "?"),
                    shot.get("carry_distance") or 0,
                    shot.get("ball_speed") or 0,
                )
                yield shot
            else:
                # Logg ukjente meldingstyper for debugging
                msg_type = message.get("message", {}).get("type", "unknown")
                if msg_type not in ("heartbeat", "ping", "status"):
                    logger.debug("R50 melding (type=%s): %s", msg_type, json.dumps(message)[:200])

    async def stop(self) -> None:
        self._running = False
        if self._connection:
            await self._connection.disconnect()
