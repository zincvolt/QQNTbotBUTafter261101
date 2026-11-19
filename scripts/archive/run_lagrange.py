import subprocess, sys, time, os
d = r"D:\QQNTBOT\apps\Lagrange\Lagrange.OneBot\bin\Release\net9.0\win-x64\publish"
p = subprocess.Popen([os.path.join(d,"Lagrange.OneBot.exe")], cwd=d,
                     creationflags=subprocess.CREATE_NEW_CONSOLE)
print("pid", p.pid)
time.sleep(12)
print("alive:", p.poll() is None)
