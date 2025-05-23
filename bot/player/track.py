from __future__ import annotations
import copy
import os
from threading import Lock
from typing import Any, Dict, Optional, TYPE_CHECKING

from bot.player.enums import TrackType
from bot import utils

if TYPE_CHECKING:
    from bot.services import Service

class Track:
    format: str
    type: TrackType

    def __init__(
        self,
        service: str = "",
        url: str = "",
        name: str = "",
        format: str = "",
        extra_info: Optional[Dict[str, Any]] = None,
        type: TrackType = TrackType.Default,
    ) -> None:
        self.service = service
        self.url = url
        self.name = name
        self.format = format
        self.extra_info = extra_info
        self.type = type
        self._lock = Lock()
        self._is_fetched = False

    def download(self, directory: str) -> str:
        service: Service = get_service_by_name(self.service)
        file_name = self.name + "." + self.format
        file_name = utils.clean_file_name(file_name)
        file_path = os.path.join(directory, file_name)
        service.download(self, file_path)
        return file_path

    def _fetch_stream_data(self):
        if self.type != TrackType.Dynamic or self._is_fetched:
            return
        self._original_track = copy.deepcopy(self)
        service: Service = get_service_by_name(self.service)
        track = service.get(self._url, extra_info=self.extra_info, process=True)[0]
        self.url = track.url
        self.name = track.name
        self._original_track.name = track.name
        self.format = track.format
        self.type = track.type
        self.extra_info = track.extra_info
        self._is_fetched = True

    @property
    def url(self) -> str:
        with self._lock:
            self._fetch_stream_data()
            return self._url

    @url.setter
    def url(self, value: str) -> None:
        self._url = value

    @property
    def original_url(self) -> str:
        if self.extra_info and "webpage_url" in self.extra_info:
            return self.extra_info["webpage_url"]
        return self._url  # fallback ke URL biasa


    @property
    def name(self) -> str:
        with self._lock:
            if not self._name:
                self._fetch_stream_data()
            return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    def get_meta(self) -> Dict[str, Any]:
        try:
            return {"name": self.name, "url": self.url}
        except:
            return {"name": None, "url": ""}

    def get_raw(self) -> Track:
        raw = copy.deepcopy(self._original_track) if hasattr(self, "_original_track") else copy.deepcopy(self)
        if raw.extra_info and "webpage_url" in raw.extra_info:
            raw.url = raw.extra_info["webpage_url"]
        return raw

    def __bool__(self):
        if self.service or self.url:
            return True
        else:
            return False

    def __getstate__(self) -> Dict[str, Any]:
        state: Dict[str, Any] = self.__dict__.copy()
        del state["_lock"]
        return state

    def __setstate__(self, state: Dict[str, Any]):
        self.__dict__.update(state)
        self._lock = Lock()
