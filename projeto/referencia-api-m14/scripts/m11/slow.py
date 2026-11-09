import time


def app(environ, start_response):
    time.sleep(float(environ["PATH_INFO"].strip("/") or 0.1))
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"ok\n"]
