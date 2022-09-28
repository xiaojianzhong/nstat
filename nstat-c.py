import argparse
import json
import logging
import time

import gpustat
import requests
import yaml


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    args = parser.parse_args()

    with open(args.config) as f:
        CFG = yaml.load(f, yaml.SafeLoader)

    while True:
        gpu_stat = gpustat.GPUStatCollection.new_query()
        gpu_stat.print_formatted()
        body = {
            'name': CFG['CLIENT']['NAME'],
            'time': gpu_stat.query_time,
            'urls': [{
                'protocol': URL['PROTOCOL'],
                'address': URL['ADDRESS'],
                'port': URL['PORT'],
            } for URL in CFG['CLIENT']['URLS']],
            'stat': {
                'gpus': [{
                    'index': gpu['index'],
                    'uuid': gpu['uuid'],
                    'name': gpu['name'],
                    'temperature': gpu['temperature.gpu'],
                    'fan': gpu['fan.speed'],
                    'utilization': gpu['utilization.gpu'],
                    'power': gpu['power.draw'],
                    'memory': {
                        'used': gpu['memory.used'],
                        'total': gpu['memory.total'],
                    },
                    'processes': [{
                        'username': process['username'],
                        'command': process['full_command'],
                        'usage': process['gpu_memory_usage'],
                        'pid': process['pid'],
                    } for process in gpu['processes']],
                } for gpu in gpu_stat.gpus],
            },
        }
        content = json.dumps(body).encode('utf-8')

        r = requests.request(
            method='POST',
            url='http://%s:%d' % (CFG['SERVER']['ADDRESS'], CFG['SERVER']['PORT']),
            data=content,
            headers={
                'Content-Type': 'application/json',
            })
        logging.info(r.status_code)

        time.sleep(CFG['CLIENT']['INTERVAL'])
