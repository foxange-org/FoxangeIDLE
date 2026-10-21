[Setup]
AppName=FoxangeIDLE
AppVersion=1.1
AppVerName=FoxangeIDLE 1.1
AppPublisher=Foxange Project
AppPublisherURL=https://foxange.fwh.is
AppSupportURL=https://foxange.fwh.is
AppUpdatesURL=https://foxange.fwh.is
AppCopyright=Copyright (C) 2026 Foxange Project
DefaultDirName={autopf}\FoxangeIDLE
DefaultGroupName=FoxangeIDLE
UninstallDisplayIcon={app}\FoxangeIDLE.exe
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
english.InstallPython=Open Python download page
english.AdditionalOptions=Additional options:
english.RegisterFxAssociation=Register .fx file association
chinesesimp.CreateDesktopShortcut=创建桌面快捷方式
chinesesimp.AdditionalIcons=附加图标：
chinesesimp.InstallPython=打开 Python 官网下载页
chinesesimp.AdditionalOptions=其他选项：
chinesesimp.RegisterFxAssociation=注册 .fx 文件关联
chinesetrad.CreateDesktopShortcut=建立桌面捷徑
chinesetrad.AdditionalIcons=附加圖示：
chinesetrad.InstallPython=開啟 Python 官網下載頁
chinesetrad.AdditionalOptions=其他選項：
chinesetrad.RegisterFxAssociation=註冊 .fx 檔案關聯

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopShortcut}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "python"; Description: "{cm:InstallPython}"; GroupDescription: "{cm:AdditionalOptions}"; Flags: checkedonce
Name: "registerfx"; Description: "{cm:RegisterFxAssociation}"; GroupDescription: "{cm:AdditionalOptions}"; Flags: unchecked

[Files]
Source: "..\..\FoxangeIDLE.exe"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
Root: HKCU; Subkey: "Software\Classes\.fx"; ValueType: string; ValueName: ""; ValueData: "FoxangeIDLE.fx"; Flags: uninsdeletevalue; Tasks: registerfx
Root: HKCU; Subkey: "Software\Classes\FoxangeIDLE.fx"; ValueType: string; ValueName: ""; ValueData: "FoxangeIDLE Source File"; Flags: uninsdeletekey; Tasks: registerfx
Root: HKCU; Subkey: "Software\Classes\FoxangeIDLE.fx\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\FoxangeIDLE.exe,0"; Tasks: registerfx
Root: HKCU; Subkey: "Software\Classes\FoxangeIDLE.fx\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\FoxangeIDLE.exe"" ""%1"""; Tasks: registerfx

[Icons]
Name: "{group}\FoxangeIDLE"; Filename: "{app}\FoxangeIDLE.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,FoxangeIDLE}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\FoxangeIDLE"; Filename: "{app}\FoxangeIDLE.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "https://www.python.org/downloads/"; Description: "{cm:InstallPython}"; Flags: nowait postinstall skipifsilent unchecked; Tasks: python

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if RegKeyExists(HKCU, 'Software\Classes\.fx') then
      RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\.fx');
    if RegKeyExists(HKCU, 'Software\Classes\FoxangeIDLE.fx') then
      RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\FoxangeIDLE.fx');
  end;
end;
