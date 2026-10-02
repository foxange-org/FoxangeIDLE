[Setup]
AppName=FoxangeIDLE
AppVersion=1.0
AppVerName=FoxangeIDLE 1.0
AppPublisher=Foxange Project
AppPublisherURL=https://foxange.fwh.is
AppSupportURL=https://foxange.fwh.is
AppUpdatesURL=https://foxange.fwh.is
AppCopyright=Copyright (C) 2026 Foxange Project
DefaultDirName={autopf}\FoxangeIDLE
DefaultGroupName=FoxangeIDLE
UninstallDisplayIcon={app}\cpp_runner\run_fox.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename=FoxangeIDLE_Setup
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "chinesetrad"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"

[CustomMessages]
english.CreateDesktopShortcut=Create a desktop shortcut
english.AdditionalIcons=Additional icons:
chinesesimp.CreateDesktopShortcut=创建桌面快捷方式
chinesesimp.AdditionalIcons=附加图标：
chinesetrad.CreateDesktopShortcut=建立桌面捷徑
chinesetrad.AdditionalIcons=附加圖示：
english.InstallPython=Open Python download page
english.AdditionalOptions=Additional options:
chinesesimp.InstallPython=打开 Python 官网下载页
chinesesimp.AdditionalOptions=其他选项：
chinesetrad.InstallPython=開啟 Python 官網下載頁
chinesetrad.AdditionalOptions=其他選項：

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopShortcut}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "python"; Description: "{cm:InstallPython}"; GroupDescription: "{cm:AdditionalOptions}"; Flags: checkedonce

[Files]
Source: "..\foxange\*"; DestDir: "{app}\foxange"; Flags: recursesubdirs createallsubdirs; Excludes: "__pycache__,*.pyc"
Source: "..\gui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\gui.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\foxange_repl.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\run_to_foxange.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\cpp_runner\run_fox.exe"; DestDir: "{app}\cpp_runner"; Flags: ignoreversion

[Registry]
Root: HKCU; Subkey: "Software\Classes\.fx"; ValueType: string; ValueName: ""; ValueData: "FoxangeIDLE.fx"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\FoxangeIDLE.fx"; ValueType: string; ValueName: ""; ValueData: "FoxangeIDLE Source File"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\FoxangeIDLE.fx\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\cpp_runner\run_fox.exe,0"
Root: HKCU; Subkey: "Software\Classes\FoxangeIDLE.fx\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\cpp_runner\run_fox.exe"" ""%1"""

[Icons]
Name: "{group}\FoxangeIDLE"; Filename: "{app}\gui.exe"; WorkingDir: "{app}"
Name: "{group}\FoxangeIDLE Runner"; Filename: "{app}\cpp_runner\run_fox.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,FoxangeIDLE}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\FoxangeIDLE"; Filename: "{app}\gui.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "https://www.python.org/downloads/"; Description: "{cm:InstallPython}"; Flags: nowait postinstall skipifsilent unchecked; Tasks: python
