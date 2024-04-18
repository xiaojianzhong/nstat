import argparse
import json
import logging
from collections import OrderedDict
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

import yaml
from json2html import json2html


name2info = OrderedDict()


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        body = dict()
        for name, info in name2info.items():
            body[name] = {
                '用户': [{
                    '序号': user['index'],
                    '名称': user['name'],
                } for user in info['users']],
                'CPU': {
                    '物理核心数': info['cpu']['ncore'],
                    '利用率': '%d%%' % info['cpu']['percent'],
                },
                '内存': '%.1fG / %.1fG (%d%%)' % (
                    info['memory']['used'] / 1024 / 1024 / 1024,
                    info['memory']['total'] / 1024 / 1024 / 1024,
                    info['memory']['percent'],
                ),
                'GPU': [{
                    '序号': gpu['index'],
                    '名称': gpu['name'],
                    '温度': '%d°C' % gpu['temperature'] if gpu['temperature'] is not None else '?',
                    '风扇转速': '%d%%' % gpu['fan'] if gpu['fan'] is not None else '?',
                    '负载': '%d%%' % gpu['utilization'] if gpu['utilization'] is not None else '?',
                    '功率': '%dW' % gpu['power'] if gpu['power'] is not None else '?',
                    '显存': '%.1fG / %.1fG (%d%%)' % (
                        gpu['memory']['used'] / 1024,
                        gpu['memory']['total'] / 1024,
                        gpu['memory']['used'] / gpu['memory']['total'] * 100),
                    '进程': [{
                        '用户名': process['username'],
                        '命令': process['command'],
                        '显存占用量': '%.1fG' % (process['usage'] / 1024) if process['usage'] is not None else '?',
                    } for process in gpu['processes']],
                } for gpu in info['gpus']],
                '磁盘': [{
                    '名称': disk['name'],
                    '文件系统': disk['filesystem'],
                    '空间': '%.1fG / %.1fG (%d%%)' % (
                        disk['used'] / 1024 / 1024 / 1024,
                        disk['total'] / 1024 / 1024 / 1024,
                        disk['percent'],
                    ),
                } for disk in info['disks']],
                '更新时间': info['time'].strftime('%Y/%m/%d %H:%M:%S'),
            }
        with open('static/index.html') as f:
            content = (f.read() % json2html.convert(json=body)).encode('utf-8')
            self.wfile.write(content)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)
        content = data.decode('utf-8')
        print(content)
        body = json.loads(content)
        name = body['name']
        time = datetime.now()
        name2info[name] = {
            'users': body['users'],
            'cpu': body['cpu'],
            'memory': body['memory'],
            'gpus': body['gpus'],
            'disks': body['disks'],
            'time': time,
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
