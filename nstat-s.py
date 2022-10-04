import argparse
import json
import logging
import socket
from collections import OrderedDict
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

import yaml
from json2html import json2html

name2info = OrderedDict()


def ping(addr, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            return sock.connect_ex((addr, port)) == 0
        except:
            return False


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        body = dict()
        for name, info in name2info.items():
            body[name] = {
                '神卓': [{
                    '协议': url['protocol'],
                    '地址': '%s:%s' % (url['address'], url['port']),
                    '连通性': '✅' if ping(url['address'], url['port']) else '❌',
                } for url in info['urls']],
                '统计信息': {
                    'GPU': [{
                        '序号': gpu['index'],
                        '名称': gpu['name'],
                        '温度': '%d°C' % gpu['temperature'],
                        '风扇转速': '%d%%' % gpu['fan'],
                        '负载': '%d%%' % gpu['utilization'],
                        '功率': '%dW' % gpu['power'],
                        '显存': '%.2fG / %.2fG' % (gpu['memory']['used'] / 1024, gpu['memory']['total'] / 1024),
                        '显存占用率': '%.2f%%' % (gpu['memory']['used'] / gpu['memory']['total'] * 100),
                    } for gpu in info['stat']['gpus']],
                },
                '统计时间': info['time'].strftime('%Y/%m/%d %H:%M:%S'),
            }
        content = b'<html><meta charset="utf-8" />' + json2html.convert(json=body).encode('utf-8') + b'</html>'
        self.wfile.write(content)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length).decode('utf-8')
        body = json.loads(content)
        name = body['name']
        time = datetime.now()
        urls = body['urls']
        stat = body['stat']
        name2info[name] = {
            'time': time,
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
    logging.info('http server is listening at %s:%s' % server.server_address)
    server.serve_forever()
