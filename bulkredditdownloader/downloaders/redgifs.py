#!/usr/bin/env python3

import json
import pathlib
import urllib.request

from bs4 import BeautifulSoup

from bulkredditdownloader.downloaders.gif_delivery_network import GifDeliveryNetwork
from bulkredditdownloader.errors import NotADownloadableLinkError


class Redgifs(GifDeliveryNetwork):
    def __init__(self, directory: pathlib.Path, post: dict):
        super().__init__(directory, post)
        self.download()

    def download(self):
        super().download()

    @staticmethod
    def _get_link(url: str) -> str:
        """Extract direct link to the video from page's source
        and return it
        """
        if '.webm' in url or '.mp4' in url or '.gif' in url:
            return url

        if url[-1:] == '/':
            url = url[:-1]

        url = urllib.request.Request("https://redgifs.com/watch/" + url.split('/')[-1])

        url.add_header(
            'User-Agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36 OPR/54.0.2952.64')

        page_source = (urllib.request.urlopen(url).read().decode())

        soup = BeautifulSoup(page_source, "html.parser")
        attributes = {"data-react-helmet": "true", "type": "application/ld+json"}
        content = soup.find("script", attrs=attributes)

        if content is None:
            raise NotADownloadableLinkError("Could not read the page source")

        return json.loads(content.contents[0])["video"]["contentUrl"]
