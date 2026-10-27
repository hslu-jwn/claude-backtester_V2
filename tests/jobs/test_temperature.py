def test_read_temperature_does_not_send_connection_close(tmp_path):
    """LibreHardwareMonitor's web server stalls on urllib's `Connection: close` request
    header (found on the user's PC 2026-10-27: curl 20 ms, urllib timed out); the reader
    must not send it."""
    import json as _json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from backtester.jobs.temperature import read_temperature

    seen = {}
    body = _json.dumps({"Text": "Sensor", "Children": [{"Text": "CPU", "ImageURL": "images/cpu.png",
        "Children": [{"Text": "Temperatures", "Children": [
            {"Text": "CPU Package", "Value": "57.0 °C"}]}]}]}).encode()  # fmt: skip

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen["connection"] = self.headers.get("Connection", "")
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/data.json"
        assert read_temperature(url, timeout=5) == 57.0
        assert "close" not in seen["connection"].lower()
    finally:
        server.shutdown()
