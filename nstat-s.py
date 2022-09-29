import argparse
import json
from collections import OrderedDict
from http.server import HTTPServer, BaseHTTPRequestHandler

import yaml


name2info = OrderedDict()


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        content = json.dumps(name2info).encode('utf-8')
        self.wfile.write(content)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length).decode('utf-8')
        body = json.loads(content)
        name = body['name']
        urls = body['urls']
        stat = body['stat']
        name2info[name] = {
            'urls': urls,
            'stat': stat,
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        content = json.dumps({}).encode('utf-8')
        self.wfile.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    args = parser.parse_args()

    with open(args.config) as f:
        CFG = yaml.load(f, yaml.SafeLoader)

    server = HTTPServer((CFG['SERVER']['ADDRESS'], CFG['SERVER']['PORT']), HTTPRequestHandler)
    server.serve_forever()
