"""Local protocol for Switchy ESP32 touch panels (no cloud).

Reversed from the Switchy Android app's offline mode:
  GET /ip                   -> {"devid","ip",...}
  GET /offline?mes=status   -> base64(JSON of channel states, e.g. {"L1":1,...})
  GET /offline?mes=<enc>    -> enc = base64(AES-128-CFB(json)); json = {"L3":1,"timestamp":t}
      key = device id (<=9 chars) laid over "0123456789ABCDEF"; iv = "0123456789ABCDEF"
  HTTP 412 means the panel's clock is stale: send ?timesync=<enc {"timestamp": t}> and retry.

Anyone on the LAN can drive a panel this way; the "key" is derived from the device id the panel
leaks unauthenticated. Keep that in mind when exposing the network.
"""
from __future__ import annotations

import base64
import json
import time
import urllib.parse
from dataclasses import dataclass

import aiohttp
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

IV = b"0123456789ABCDEF"


def _key(devid: str) -> bytes:
    k = bytearray(IV)
    k[: min(len(devid), 9)] = devid[:9].encode()
    return bytes(k)


def _encrypt(devid: str, payload: dict) -> str:
    enc = Cipher(algorithms.AES(_key(devid)), modes.CFB(IV)).encryptor()
    return base64.b64encode(enc.update(json.dumps(payload).encode()) + enc.finalize()).decode()


class SwitchyError(Exception):
    """A panel did not answer or refused a command."""


@dataclass
class SwitchyPanel:
    """One Switchy panel, addressed by its device id at a known host."""

    devid: str
    host: str

    async def _get(self, session: aiohttp.ClientSession, path: str) -> str:
        try:
            async with session.get(f"http://{self.host}/{path}", timeout=aiohttp.ClientTimeout(total=6)) as r:
                if r.status == 412:
                    return "412"
                r.raise_for_status()
                return await r.text()
        except aiohttp.ClientError as err:
            raise SwitchyError(f"{self.devid}: {err}") from err

    async def identify(self, session: aiohttp.ClientSession) -> dict:
        """GET /ip — confirms this host answers as this device id."""
        return json.loads(await self._get(session, "ip"))

    async def status(self, session: aiohttp.ClientSession) -> dict[str, int]:
        """Current channel states, {"L1": 0, "L2": 1, ...}."""
        body = await self._get(session, "offline?mes=status")
        return {k: int(v) for k, v in json.loads(base64.b64decode(body)).items() if k.startswith("L")}

    async def set_channel(self, session: aiohttp.ClientSession, channel: str, value: int) -> dict[str, int]:
        """Set one channel (e.g. 'L3') to a value (0 off, 1 on, or a level), with a clock resync
        retry on 412."""
        for _ in range(2):
            msg = urllib.parse.quote(_encrypt(self.devid, {channel: value, "timestamp": int(time.time())}), safe="")
            body = await self._get(session, f"offline?mes={msg}")
            if body == "412":
                ts = urllib.parse.quote(_encrypt(self.devid, {"timestamp": int(time.time())}), safe="")
                await self._get(session, f"offline?timesync={ts}")
                continue
            return {k: int(v) for k, v in json.loads(base64.b64decode(body)).items() if k.startswith("L")}
        raise SwitchyError(f"{self.devid}: panel kept asking for a time sync")
