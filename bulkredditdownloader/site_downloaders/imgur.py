#!/usr/bin/env python3

import json
import logging
from typing import Optional

import requests
from praw.models import Submission

from bulkredditdownloader.site_authenticator import SiteAuthenticator
from bulkredditdownloader.exceptions import NotADownloadableLinkError, ResourceNotFound, SiteDownloaderError
from bulkredditdownloader.resource import Resource
from bulkredditdownloader.site_downloaders.base_downloader import BaseDownloader
from bulkredditdownloader.site_downloaders.direct import Direct

logger = logging.getLogger(__name__)


class Imgur(BaseDownloader):
    imgur_image_domain = "https://i.imgur.com/"

    def __init__(self, post: Submission):
        super().__init__(post)
        self.raw_data = {}

    def find_resources(self, authenticator: Optional[SiteAuthenticator] = None) -> list[Resource]:
        link = self.post.url

        if link.endswith(".gifv"):
            direct_thing = Direct(self.post)
            return direct_thing.find_resources(authenticator)

        self.raw_data = self._get_data(link)

        if self._is_album():
            if self.raw_data["album_images"]["count"] != 1:
                out = self._download_album(self.raw_data["album_images"])
            else:
                out = self._download_image(self.raw_data["album_images"]["images"][0])
        else:
            out = self._download_image(self.raw_data)
        return out

    def _download_album(self, images: dict):
        images_length = images["count"]

        out = []

        for i in range(images_length):
            extension = self._validate_extension(images["images"][i]["ext"])
            image_url = self.imgur_image_domain + images["images"][i]["hash"] + extension
            out.append(Resource(self.post, image_url))
        return out

    def _download_image(self, image: dict):
        extension = self._validate_extension(image["ext"])
        image_url = self.imgur_image_domain + image["hash"] + extension
        return [Resource(self.post, image_url)]

    def _is_album(self) -> bool:
        return "album_images" in self.raw_data

    @staticmethod
    def _get_data(link: str) -> dict:
        cookies = {"over18": "1", "postpagebeta": "0"}
        res = requests.get(link, cookies=cookies)
        if res.status_code != 200:
            raise ResourceNotFound(f"Server responded with {res.status_code} to {link}")
        page_source = requests.get(link, cookies=cookies).text

        starting_string = "image               : "
        ending_string = "group               :"

        starting_string_lenght = len(starting_string)
        try:
            start_index = page_source.index(starting_string) + starting_string_lenght
            end_index = page_source.index(ending_string, start_index)
        except ValueError:
            raise NotADownloadableLinkError(f"Could not read the page source on {link}")

        while page_source[end_index] != "}":
            end_index -= 1
        try:
            data = page_source[start_index:end_index + 2].strip()[:-1]
        except IndexError:
            page_source[end_index + 1] = '}'
            data = page_source[start_index:end_index + 3].strip()[:-1]

        return json.loads(data)

    @staticmethod
    def _validate_extension(extension_suffix: str) -> str:
        possible_extensions = [".jpg", ".png", ".mp4", ".gif"]
        for extension in possible_extensions:
            if extension in extension_suffix:
                return extension
        else:
            raise SiteDownloaderError(f'"{extension_suffix}" is not recognized as a valid extension for Imgur')
