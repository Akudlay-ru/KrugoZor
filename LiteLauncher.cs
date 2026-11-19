using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

internal static class LiteLauncher
{
    const string Title = "КругоЗор Lite";
    const string PackageUrl = "https://github.com/Akudlay-ru/KrugoZor/releases/download/v15.0-lite/KruGoZor-lite.exe";
    const string PackageHash = "CD95A872B2672673EDA4D995DBA690EDB2C23BD2780DEA7A162B6C0CDEF4F20E";
    const long PackageSize = 120107606;

    [STAThread]
    static int Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        using (var mutex = new Mutex(false, @"Local\KruGoZor.Lite.Launcher"))
        {
            bool held;
            try { held = mutex.WaitOne(0); }
            catch (AbandonedMutexException) { held = true; }
            if (!held) return 0;
            try
            {
                string directory = Path.Combine(Environment.GetFolderPath(
                    Environment.SpecialFolder.LocalApplicationData), "KrugoZor", "Lite");
                Directory.CreateDirectory(directory);
                string executable = Path.Combine(directory, "KruGoZor-lite.exe");
                if (!IsVerified(executable) && !InstallWithProgress(executable)) return 1;

                bool diagnostic = args.Length == 2 && args[0] == "--check-models";
                var start = new ProcessStartInfo(executable) {
                    WorkingDirectory = directory, UseShellExecute = false
                };
                if (diagnostic)
                    start.Arguments = "--check-models \"" + Path.GetFullPath(args[1]) + "\"";
                using (var child = Process.Start(start))
                {
                    if (!diagnostic) return 0;
                    child.WaitForExit();
                    return child.ExitCode;
                }
            }
            catch (Exception ex) { ShowError(ex); return 1; }
            finally { mutex.ReleaseMutex(); }
        }
    }

    static bool IsVerified(string path)
    {
        if (!File.Exists(path) || new FileInfo(path).Length != PackageSize) return false;
        using (var sha = SHA256.Create())
        using (var input = File.OpenRead(path))
            return BitConverter.ToString(sha.ComputeHash(input)).Replace("-", "") == PackageHash;
    }

    static bool InstallWithProgress(string executable)
    {
        using (var dialog = new Form { Text = Title, ClientSize = new Size(390, 94),
                                      StartPosition = FormStartPosition.CenterScreen,
                                      FormBorderStyle = FormBorderStyle.FixedDialog,
                                      ControlBox = false, AutoScaleMode = AutoScaleMode.Font })
        {
            var status = new Label { Text = "Первый запуск. Скачиваю пакет Lite…",
                                     AutoSize = true, Location = new Point(16, 14) };
            var bar = new ProgressBar { Location = new Point(16, 46), Size = new Size(358, 19) };
            dialog.Controls.Add(status);
            dialog.Controls.Add(bar);
            dialog.Shown += async delegate
            {
                var progress = new Progress<int>(percent => {
                    if (bar.IsDisposed) return;
                    bar.Value = percent;
                    if (percent == 100) status.Text = "Проверяю скачанный файл…";
                });
                try
                {
                    await Task.Run(() => Download(executable, progress));
                    dialog.DialogResult = DialogResult.OK;
                }
                catch (Exception ex) { ShowError(ex); dialog.DialogResult = DialogResult.Cancel; }
                dialog.Close();
            };
            return dialog.ShowDialog() == DialogResult.OK;
        }
    }

    static void Download(string executable, IProgress<int> progress)
    {
        ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
        string partial = executable + ".download";
        try
        {
            using (var response = OpenPackage(new Uri(PackageUrl)))
            using (var input = response.GetResponseStream())
            using (var output = new FileStream(partial, FileMode.Create, FileAccess.Write, FileShare.None))
            {
                var buffer = new byte[65536];
                long received = 0;
                int previous = -1;
                int count;
                while ((count = input.Read(buffer, 0, buffer.Length)) != 0)
                {
                    received += count;
                    if (received > PackageSize) throw new IOException("Размер пакета отличается от ожидаемого.");
                    output.Write(buffer, 0, count);
                    int percent = (int)(received * 100 / PackageSize);
                    if (percent == previous) continue;
                    progress.Report(percent);
                    previous = percent;
                }
            }
            if (!IsVerified(partial)) throw new IOException("Пакет не прошёл проверку SHA-256.");
            if (File.Exists(executable)) File.Replace(partial, executable, null);
            else File.Move(partial, executable);
        }
        finally
        {
            if (File.Exists(partial)) File.Delete(partial);
        }
    }

    static HttpWebResponse OpenPackage(Uri uri)
    {
        for (int redirect = 0; redirect < 6; redirect++)
        {
            if (uri.Scheme != Uri.UriSchemeHttps ||
                (uri.Host != "github.com" && uri.Host != "release-assets.githubusercontent.com"))
                throw new IOException("Недопустимый адрес загрузки пакета.");
            var request = (HttpWebRequest)WebRequest.Create(uri);
            request.AllowAutoRedirect = false;
            request.UserAgent = "KrugoZor-Lite-Launcher";
            request.Timeout = 30000;
            request.ReadWriteTimeout = 30000;
            var response = (HttpWebResponse)request.GetResponse();
            if (response.StatusCode == HttpStatusCode.OK) return response;
            using (response)
            {
                int code = (int)response.StatusCode;
                string next = response.Headers["Location"];
                if (code < 300 || code >= 400 || String.IsNullOrEmpty(next))
                    throw new IOException("GitHub вернул неожиданный ответ.");
                uri = new Uri(uri, next);
            }
        }
        throw new IOException("Слишком много перенаправлений при скачивании.");
    }

    static void ShowError(Exception ex)
    {
        MessageBox.Show("Не удалось запустить КругоЗор Lite.\n\n" + ex.Message,
                        Title, MessageBoxButtons.OK, MessageBoxIcon.Error);
    }
}
