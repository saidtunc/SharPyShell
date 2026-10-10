# SharPyShell

<p align="center"><img src="logo.png" width="500" height="300" /></p>

<hr/>

SharPyShell is a tiny and obfuscated ASP.NET webshell that executes commands received by an encrypted channel compiling them in memory at runtime.

SharPyShell supports only C# web applications that runs on .NET Framework >= 2.0<br>VB is not supported atm.

## Usage

```
python3 SharPyShell.py generate -p somepassword
python3 SharPyShell.py generate -p somepassword -f ashx -o raw -e aes256
python3 SharPyShell.py generate -p somepassword -f asmx --no-obfuscate
python3 SharPyShell.py generate -p somepassword -f asp
python3 SharPyShell.py interact -u http://target.url/sharpyshell.aspx -p somepassword
python3 SharPyShell.py interact -u http://target.url/handler.ashx  -p somepassword
```

### Generate options

| Flag | Values | Description |
|------|--------|-------------|
| `-p`, `--password` | string | Shared key for encrypting the channel (**required**) |
| `-e`, `--encryption` | `xor`, `aes128`, `aes256` | Channel encryption scheme (default `xor`) |
| `-o`, `--obfuscator` | `raw`, `encrypted_dll`, `encrypted_dll_ulong_compression` | Obfuscation strategy for the payload (default `encrypted_dll`) |
| `-f`, `--format` | `aspx`, `ashx`, `asmx`, `asp` | Output file extension / handler type (default `aspx`) |
| `--no-obfuscate` | flag | Disable post-processing obfuscation of the generated code |
| `--output` | path | Custom output path |
| `--endian-type` | `default`, `little`, `big` | Endianess for `encrypted_dll_ulong_compression` |

## Enhanced Obfuscation

The webshell generator applies an additional post-processing obfuscation pass on top of the chosen obfuscator. This pass is enabled by default and can be turned off with `--no-obfuscate`.

Each generation produces a different-looking payload. The pass performs:

  - **Identifier randomization** &mdash; every user-defined variable, method, and class name is replaced with a fresh random identifier on every build, while leaving .NET framework names and property accesses intact.
  - **String literal encoding** &mdash; sensitive strings (the password hash, `SharPyShell`, `ExecRuntime`, `SharPy`, `Run`) are encoded as `new string(new char[]{...})` so they are not visible to simple pattern scanners.
  - **Reflection-based compiler** &mdash; for the `raw` obfuscator, `new CSharpCodeProvider()` is replaced with `Activator.CreateInstance(Type.GetType(...))` and the `Microsoft.CSharp` import is dropped. The type name itself is also stored as an encoded char array.
  - **Junk code injection** &mdash; realistic-looking dead methods and variables are injected to disrupt structural signatures.
  - **Decoy comments** &mdash; misleading inline comments are scattered through the code.

## Alternative File Extensions

By default the generated agent is an `.aspx` Web Form. Two additional handler types are supported, both processed by the standard .NET pipeline on IIS:

  - `-f aspx` &mdash; ASP.NET Web Form (default). Classic `<%@ Page %>` with a `Page_Load` entry point.
  - `-f ashx` &mdash; Generic HTTP Handler. The agent is emitted as a `<%@ WebHandler %>` class implementing `IHttpHandler.ProcessRequest`. Same request model as `.aspx`; the client needs no changes &mdash; just point `interact -u` at the `.ashx` URL.
  - `-f asmx` &mdash; Web Service. The agent is emitted as a `<%@ WebService %>` class that handles POST requests inside its constructor using `HttpContext.Current`, then calls `Response.Flush()` and `ApplicationInstance.CompleteRequest()` to short-circuit the SOAP pipeline. A dummy `[WebMethod]` is included so the file still looks like a legitimate service when browsed. The client URL is the same as for `.aspx` / `.ashx`.
  - `-f asp` &mdash; Classic ASP (VBScript). A standalone command-execution shell for legacy IIS servers that do not have .NET installed. Commands are sent as XOR-encrypted Base64 in a POST `data` field and executed via `WScript.Shell`. This format does **not** support the module system or `interact` mode &mdash; it is a lightweight, single-purpose agent. VBScript-specific obfuscation (identifier randomization, password encoding, junk functions) is applied by default.

Class names and the dummy WebMethod name are generated to resemble ordinary application code (for example `DataHandler42`, `ResourceLoader`, `GetStatus`), so the file blends into a typical IIS application tree.

## Requirements

Python version >= 3.6

and

```
pip3 install -r requirements.txt
```

## Description

SharPyShell is a post-exploitation framework written in Python that are capable of:

  - Generate obfuscated webshell (generate);
  - Simulate a windows terminal as an interaction for the webshell (interact).
  
  The main aim of this framework is providing the penetration tester a series of tools to ease the post exploitation phase once an exploitation has been succesfull against an IIS webserver.
  <br>
  <br>
  This tool is not intended as a replacement of the frameworks for C2 Server (i.e. Meterpreter, Empire, ecc..) but this should be used when you land to a fully restricted server where inbound and outbound connections are very limited.
<br>
In this framework you will have all the tools needed to privesc, netdiscovery and lateral movement as you are typing behind the cmd of the target server.
<br>
<br>
Moreover this framework aim to be stealthy as much as possible implementing in memory execution for c# code and powershell modules.
<br>
<br>
The obfuscation implemented in SharPyShell aim to evade both file signatures and network signatures ids.<br>
For the network signatures evasion, a fully encrypted channel has been developed for sending commands and receiving outputs.<br>
The evasion for file signatures has been achieved using Reflection on a precompiled dll in charge of runtime compiling c# code.<br>

## Technical Diagram

Generated with asciiflow.com
 ```
+-------------------------------------------+                      +--------------------------------------------+
| SharPyShell Client (Local)                |                      | Target Server (Remote)                     |
+-------------------------------------------+   +--------------+   +--------------------------------------------+
|                                           |   |  Encrypted   |   |                                            |
|   +--------+-----------------^-----------<---->     HTTP     <---->-----------+-----------------^--------+    |
|            |                 |            |   |   Channel    |   |            |                 |             |
|            |4-Receive        |1-Send      |   +--------------+   |            |2-Receive        |3-Send       |
|            |                 |            |                      |            |                 |             |
|   +--------v-----------------+--------+   |                      |   +--------v-----------------+--------+    |
|   |              Module               |   |                      |   |           Webshell URL            |    |
|   +--------+-----------------^--------+   |                      |   +--------+-----------------^--------+    |
|   |        |Parse            |Generate|   |                      |   |        |Parse            |Generate|    |
|   | +------v------+   +------+------+ |   |                      |   | +------v------+   +------+------+ |    |
|   | |Base64 Resp  |   |Base64 Req   | |   |                      |   | |Base64 Req   |   |Base64 Resp  | |    |
|   | +------+------+   +------^------+ |   |                      |   | +------+------+   +------^------+ |    |
|   |        |Decode           |Encode  |   |                      |   |        |Decode           |Encode  |    |
|   | +------v------+   +------+------+ |   |                      |   | +------v------+   +------+------+ |    |
|   | |Xor/Aes Data |   |Xor/Aes Data | |   |                      |   | |Xor/Aes Data |   |Xor/Aes Data | |    |
|   | +------+------+   +------^------+ |   |                      |   | +------+------+   +------^------+ |    |
|   |        |Decrypt          |Encrypt |   |                      |   |        |Decrypt          |Encrypt |    |
|   | +------v------+   +------+------+ |   |                      |   | +------v------+   +------+------+ |    |
|   | |Response     |   |C# Code      | |   |                      |   | |C# Code      |   |Output       | |    |
|   | +------+------+   +------+------+ |   |                      |   | +------+------+   +------+------+ |    |
|   |        |                 ^        |   |                      |   |        |                 ^        |    |
|   |        v                 |        |   |                      |   |        v                 |        |    |
|   |        +--------+--------+        |   |                      |   |        +--------+--------+        |    |
|   |                 |                 |   |                      |   |                 |                 |    |
|   +---------------- ^ ----------------+   |                      |   +---------------- ^ ----------------+    |
|                     |                     |                      |                     |                      |
|                     |Run&Parse            |                      |                     |Compile&Run           |
|                     |                     |                      |                     |                      |
|             +------ v ------+             |                      |             +------ v ------+              |
|             |Terminal       |             |                      |             |csc.exe        |              |
|             +---------------+             |                      |             +---------------+              |
|             |Modules:       |             |                      |             |System.dll     |              |
|             |#exec_cmd      |             |                      |             |Compile in Mem |              |
|             |#exec_ps       |             |                      |             |No exe output  |              |
|             |#runas         |             |                      |             |               |              |
|             |.....          |             |                      |             |               |              |
|             |               |             |                      |             |               |              |
|             +---------------+             |                      |             +---------------+              |
|                                           |                      |                                            |
+-------------------------------------------+                      +--------------------------------------------+
```

## Modules

```
 #download               Download a file from the server                                            
 #exec_cmd               Run a cmd.exe /c command on the server                                     
 #exec_ps                Run a powershell.exe -nop -noni -enc 'base64command' on the server         
 #inject_dll_reflective  Inject a reflective DLL in a new (or existing) process                     
 #inject_dll_srdi        Inject a generic DLL in a new (or existing) process                        
 #inject_shellcode       Inject shellcode in a new (or existing) process                            
 #invoke_ps_module       Run a ps1 script on the target server                                      
 #invoke_ps_module_as    Run a ps1 script on the target server as a specific user                   
 #lateral_psexec         Run psexec binary to move laterally                                        
 #lateral_wmi            Run builtin WMI command to move laterally                                  
 #mimikatz               Run an offline version of mimikatz directly in memory                      
 #net_portscan           Run a port scan using regular sockets, based (pretty) loosely on nmap      
 #privesc_juicy_potato   Launch InMem Juicy Potato attack trying to impersonate NT AUTHORITY\SYSTEM 
 #privesc_powerup        Run Powerup module to assess all misconfiguration for privesc              
 #runas                  Run a cmd.exe /c command spawning a new process as a specific user         
 #runas_ps               Run a powershell.exe -enc spawning a new process as a specific user        
 #upload                 Upload a file to the server 
```

## Windows version tested

Windows Server >= 2008 Standard x64


## Credits

<ul>
  <li><a href="https://github.com/newfinal100">@newfinal100</a> (for the fancy logo!)</li>
  <li><a href="https://github.com/epinna/weevely3">@weevely3</a></li>
  <li><a href="https://github.com/ohpe/juicy-potato">@juicy-potato</a></li>
  <li><a href="https://github.com/PowerShellMafia/PowerSploit">@PowerSploit</a></li>
  <li><a href="https://github.com/gentilkiwi/mimikatz">@mimikatz</a></li>
</ul>
