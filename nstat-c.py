import argparse
import json
import logging
import time

import gpustat
import psutil
import requests
import yaml


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    args = parser.parse_args()

    with open(args.config) as f:
        CFG = yaml.load(f, yaml.SafeLoader)

    while True:
        body = {
            'name': CFG['CLIENT']['NAME'],
            'users': [{
                'index': i,
                'name': user.name,
            } for i, user in enumerate(psutil.users())],
            'cpu': {
                'ncore': psutil.cpu_count(logical=False),
                'percent': psutil.cpu_percent(),
            },
            'memory': {
                'used': psutil.virtual_memory().used,
                'total': psutil.virtual_memory().total,
                'percent': psutil.virtual_memory().percent,
            },
            'gpus': [{
                'index': gpu['index'],
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
                    'command': ' '.join(process['full_command']),
                    'usage': process['gpu_memory_usage'],
                    'pid': process['pid'],
                } for process in filter(
                    lambda process: process['gpu_memory_usage'] is not None and process['gpu_memory_usage'] > gpu['memory.total'] * CFG['CLIENT']['PROCESS_GPU_MEMORY_USAGE_THRESHOLD'],
                    gpu['processes'])],
            } for gpu in gpustat.GPUStatCollection.new_query().gpus],
            'disks': [{
                'name': disk.device,
                'filesystem': disk.fstype,
                'used': psutil.disk_usage(disk.mountpoint).used,
                'total': psutil.disk_usage(disk.mountpoint).total,
                'percent': psutil.disk_usage(disk.mountpoint).percent,
            } for disk in psutil.disk_partitions()],
        }
        content = json.dumps(body).encode('utf-8')

        try:
            r = requests.request(
                method='POST',
                url='http://%s:%d' % (CFG['SERVER']['ADDRESS'], CFG['SERVER']['PORT']),
                data=content,
                headers={
                    'Content-Type': 'application/json',
                })
            logging.info(r.status_code)
        except requests.RequestException as e:
            logging.error(e)

        time.sleep(CFG['CLIENT']['INTERVAL'])
