using System;
using System.Diagnostics;
using System.IO;
using System.Threading;

class Program {
    static int Main(string[] args) {
        // Find self name to determine provider
        string exePath = System.Reflection.Assembly.GetExecutingAssembly().Location;
        string exeName = Path.GetFileNameWithoutExtension(exePath).ToLower();
        string provider = "gemini"; // default
        if (exeName.Contains("cursor")) provider = "cursor";
        else if (exeName.Contains("copilot")) provider = "copilot";
        else if (exeName.Contains("claude")) provider = "claude";
        else if (exeName.Contains("codex")) provider = "codex";
        else if (exeName.Contains("gemini")) provider = "gemini";

        string exeDir = Path.GetDirectoryName(exePath);
        string mainPyPath = Path.GetFullPath(Path.Combine(exeDir, @"..\..\src\agy_shim\main.py"));
        
        if (!File.Exists(mainPyPath)) {
            Console.Error.WriteLine("Error: Cannot find main.py at " + mainPyPath);
            return 1;
        }

        // Build arguments
        string arguments = EscapeArg(mainPyPath) + " --provider " + provider;
        foreach (string arg in args) {
            arguments += " " + EscapeArg(arg);
        }

        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = "python.exe";
        psi.Arguments = arguments;
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        psi.RedirectStandardInput = true;
        psi.RedirectStandardOutput = true;
        psi.RedirectStandardError = true;

        Process proc = new Process();
        proc.StartInfo = psi;

        try {
            proc.Start();
        } catch (Exception ex) {
            Console.Error.WriteLine("Error starting python.exe: " + ex.Message);
            return 1;
        }

        // Copy input stream to process input stream in a background thread
        Thread inputThread = new Thread(() => {
            try {
                byte[] buffer = new byte[8192];
                int bytesRead;
                using (Stream inputStream = Console.OpenStandardInput())
                using (Stream processInput = proc.StandardInput.BaseStream) {
                    while ((bytesRead = inputStream.Read(buffer, 0, buffer.Length)) > 0) {
                        processInput.Write(buffer, 0, bytesRead);
                        processInput.Flush();
                    }
                }
            } catch {
            } finally {
                try { proc.StandardInput.Close(); } catch {}
            }
        });
        inputThread.IsBackground = true;
        inputThread.Start();

        // Copy process output stream to output stream
        Thread outputThread = new Thread(() => {
            try {
                byte[] buffer = new byte[8192];
                int bytesRead;
                using (Stream processOutput = proc.StandardOutput.BaseStream)
                using (Stream outputStream = Console.OpenStandardOutput()) {
                    while ((bytesRead = processOutput.Read(buffer, 0, buffer.Length)) > 0) {
                        outputStream.Write(buffer, 0, bytesRead);
                        outputStream.Flush();
                    }
                }
            } catch {
            }
        });
        outputThread.IsBackground = true;
        outputThread.Start();

        // Copy process error stream to error stream
        Thread errorThread = new Thread(() => {
            try {
                byte[] buffer = new byte[8192];
                int bytesRead;
                using (Stream processError = proc.StandardError.BaseStream)
                using (Stream errorStream = Console.OpenStandardError()) {
                    while ((bytesRead = processError.Read(buffer, 0, buffer.Length)) > 0) {
                        errorStream.Write(buffer, 0, bytesRead);
                        errorStream.Flush();
                    }
                }
            } catch {
            }
        });
        errorThread.IsBackground = true;
        errorThread.Start();

        proc.WaitForExit();
        
        // Ensure all output and error data are completely flushed to console
        outputThread.Join();
        errorThread.Join();
        inputThread.Join(100);
        
        int exitCode = proc.ExitCode;
        proc.Dispose();
        return exitCode;
    }

    static string EscapeArg(string arg) {
        if (string.IsNullOrEmpty(arg)) return "\"\"";
        if (arg.IndexOfAny(new char[] { ' ', '"', '\t', '\\' }) == -1) {
            return arg;
        }
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        sb.Append('"');
        for (int i = 0; i < arg.Length; i++) {
            char c = arg[i];
            if (c == '\\') {
                int backslashCount = 0;
                while (i < arg.Length && arg[i] == '\\') {
                    backslashCount++;
                    i++;
                }
                if (i == arg.Length) {
                    sb.Append('\\', backslashCount * 2);
                    i--;
                } else if (arg[i] == '"') {
                    sb.Append('\\', backslashCount * 2 + 1);
                    sb.Append('"');
                } else {
                    sb.Append('\\', backslashCount);
                    i--;
                }
            } else if (c == '"') {
                sb.Append("\\\"");
            } else {
                sb.Append(c);
            }
        }
        sb.Append('"');
        return sb.ToString();
    }
}
