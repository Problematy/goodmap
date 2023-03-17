import urllib.parse
from flask import request, redirect


def redirect_nonwww_to_www():
    """Redirect non-www requests to www."""
    urlparts = urllib.parse.urlparse(request.url)
    if not urlparts.netloc.startswith("www."):
        urlparts = urlparts._replace(netloc=f'www.{urlparts.netloc}')
        return redirect(urllib.parse.urlunparse(urlparts), code=301)


def redirect_www_to_nonwww():
    """Redirect www requests to non-www."""
    urlparts = urllib.parse.urlparse(request.url)
    if urlparts.netloc.startswith("www."):
        urlparts = urlparts._replace(netloc=urlparts.netloc.removeprefix("www."))
        return redirect(urllib.parse.urlunparse(urlparts), code=301)
