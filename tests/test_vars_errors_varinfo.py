"""Tests for /user/vars, /user/errors and /user/varinfo parsing."""

import aiohttp
import pytest

from custom_components.eta_heating_technology.api import (
    EtaApiClient,
    normalize_object_uri,
    uri_path_for_varset,
)

VARSET_XML = """<?xml version="1.0" encoding="utf-8"?>
<eta version="1.0" xmlns="http://www.eta.co.at/rest/v1">
  <vars uri="/user/vars/myset1">
    <variable uri="112/10021/0/0/12112" strValue="Off" unit="" decPlaces="0"
      scaleFactor="1" advTextOffset="1802">1802</variable>
    <variable uri="/120/10102/0/11060/0" strValue="40" unit="°C" decPlaces="0"
      scaleFactor="10" advTextOffset="0">403</variable>
  </vars>
</eta>
"""

ERRORS_XML = """<?xml version="1.0" encoding="utf-8"?>
<eta version="1.0" xmlns="http://www.eta.co.at/rest/v1">
  <errors uri="/user/errors">
    <fub uri="/112/10021" name="Kessel">
      <error msg="Flue gas sensor Interrupted" priority="Error"
        time="2011-06-29 12:47:50">Sensor or Cable broken</error>
      <error msg="Water pressure too low" priority="Error"
        time="2011-06-29 12:48:12">Top up heating water!</error>
    </fub>
    <fub uri="/112/10101" name="HK1"/>
  </errors>
</eta>
"""

VARINFO_WRITABLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<eta xmlns="http://www.eta.co.at/rest/v1" version="1.0">
  <varInfo uri="/user/varinfo/40/10021/0/0/12080">
    <variable uri="40/10021/0/0/12080" name="On/off button"
      fullName="Misc. > On/off button" unit="" decPlaces="0"
      scaleFactor="1" advTextOffset="1802" isWritable="1">
      <type>TEXT</type>
      <validValues>
        <value strValue="Off">1802</value>
        <value strValue="On">1803</value>
      </validValues>
    </variable>
  </varInfo>
</eta>
"""

VARINFO_READONLY_XML = """<?xml version="1.0" encoding="utf-8"?>
<eta xmlns="http://www.eta.co.at/rest/v1" version="1.0">
  <varInfo uri="/user/varinfo/24/10561/0/11031/2016">
    <variable uri="24/10561/0/11031/2016" name="Eingang"
      fullName="Kessel > Eingang" unit="" decPlaces="0"
      scaleFactor="1" advTextOffset="1802" isWritable="0">
      <type>TEXT</type>
    </variable>
  </varInfo>
</eta>
"""

SUCCESS_XML = """<?xml version="1.0" encoding="utf-8"?>
<eta version="1.0" xmlns="http://www.eta.co.at/rest/v1">
  <success uri="/user/vars/myset1"/>
</eta>
"""


class FakeResponse:
    def __init__(self, status: int, text: str) -> None:
        self.status = status
        self._text = text

    async def text(self) -> str:
        return self._text


def mock_response(status: int, text: str):
    async def _mock(*args, **kwargs):
        return FakeResponse(status, text)

    return _mock


def test_normalize_object_uri() -> None:
    assert normalize_object_uri("112/10021/0/0/12112") == "/112/10021/0/0/12112"
    assert normalize_object_uri("/112/10021/0/0/12112") == "/112/10021/0/0/12112"
    assert normalize_object_uri("/user/var/112/10021/0/0/12112") == "/112/10021/0/0/12112"
    assert uri_path_for_varset("/24/1/0/0/1") == "24/1/0/0/1"


@pytest.mark.asyncio
async def test_get_varset(monkeypatch) -> None:
    monkeypatch.setattr(EtaApiClient, "_api_wrapper", mock_response(200, VARSET_XML))
    client = EtaApiClient(host="1.2.3.4", port="8080", session=aiohttp.ClientSession())
    data = await client.async_get_varset("myset1")
    assert set(data) == {"/112/10021/0/0/12112", "/120/10102/0/11060/0"}
    assert data["/112/10021/0/0/12112"].value == "1802"
    assert data["/120/10102/0/11060/0"].scaled_value == 40.3


@pytest.mark.asyncio
async def test_get_errors(monkeypatch) -> None:
    monkeypatch.setattr(EtaApiClient, "_api_wrapper", mock_response(200, ERRORS_XML))
    client = EtaApiClient(host="1.2.3.4", port="8080", session=aiohttp.ClientSession())
    errors = await client.async_get_errors()
    flat = errors.all_errors()
    assert len(flat) == 2
    assert flat[0]["fub"] == "Kessel"
    assert flat[0]["msg"] == "Flue gas sensor Interrupted"
    assert "Sensor or Cable broken" in flat[0]["description"]


@pytest.mark.asyncio
async def test_get_varinfo_writable(monkeypatch) -> None:
    monkeypatch.setattr(EtaApiClient, "_api_wrapper", mock_response(200, VARINFO_WRITABLE_XML))
    client = EtaApiClient(host="1.2.3.4", port="8080", session=aiohttp.ClientSession())
    info = await client.async_get_varinfo("/40/10021/0/0/12080")
    assert info.writable is True
    assert info.valid_values is not None
    assert len(info.valid_values.values) == 2


@pytest.mark.asyncio
async def test_get_varinfo_readonly(monkeypatch) -> None:
    monkeypatch.setattr(EtaApiClient, "_api_wrapper", mock_response(200, VARINFO_READONLY_XML))
    client = EtaApiClient(host="1.2.3.4", port="8080", session=aiohttp.ClientSession())
    info = await client.async_get_varinfo("24/10561/0/11031/2016")
    assert info.writable is False
