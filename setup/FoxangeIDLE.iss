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
english.AddFoxangeToPath=Add foxange to PATH
chinesesimp.InstallPython=打开 Python 官网下载页
chinesesimp.AdditionalOptions=其他选项：
chinesesimp.AddFoxangeToPath=将 foxange 添加到 PATH
chinesetrad.InstallPython=開啟 Python 官網下載頁
chinesetrad.AdditionalOptions=其他選項：
chinesetrad.AddFoxangeToPath=將 foxange 加入 PATH

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopShortcut}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "python"; Description: "{cm:InstallPython}"; GroupDescription: "{cm:AdditionalOptions}"; Flags: checkedonce
Name: "addpath"; Description: "{cm:AddFoxangeToPath}"; GroupDescription: "{cm:AdditionalOptions}"; Flags: unchecked

[Files]
Source: "..\foxange\*"; DestDir: "{app}\foxange"; Flags: recursesubdirs createallsubdirs; Excludes: "__pycache__,*.pyc"
Source: "..\gui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\gui.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\foxange_repl.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\foxpkg.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\run_to_foxange.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\cpp_runner\run_fox.exe"; DestDir: "{app}\cpp_runner"; Flags: ignoreversion
Source: "..\cpp_runner\foxange.exe"; DestDir: "{app}\cpp_runner"; Flags: ignoreversion

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

[Code]
const
  WM_SETTINGCHANGE = $001A;
  HWND_BROADCAST_ALL = $FFFF;
  SMTO_ABORTIFHUNG = $0002;

function SendMessageTimeoutW(hWnd: LongInt; Msg: LongInt; wParam: LongInt;
  lParam: String; fuFlags: LongInt; uTimeout: LongInt; var lpdwResult: LongInt): LongInt;
  external 'SendMessageTimeoutW@user32.dll stdcall';

procedure RefreshEnv;
var
  Dummy: LongInt;
begin
  SendMessageTimeoutW(HWND_BROADCAST_ALL, WM_SETTINGCHANGE, 0,
    'Environment', SMTO_ABORTIFHUNG, 5000, Dummy);
end;

function GetUserPath(var Value: String): Boolean;
begin
  Result := RegQueryStringValue(HKCU, 'Environment', 'Path', Value);
  if not Result then
    Value := '';
end;

procedure AddDirToPath(Dir: String);
var
  Path: String;
begin
  if not GetUserPath(Path) then
    Exit;
  if Pos(LowerCase(Dir), LowerCase(Path)) > 0 then
    Exit;
  if Path = '' then
    Path := Dir
  else
    Path := Path + ';' + Dir;
  RegWriteExpandStringValue(HKCU, 'Environment', 'Path', Path);
  RefreshEnv;
end;

procedure RemoveDirFromPath(Dir: String);
var
  Path: String;
  List, OutList: TStringList;
  i: Integer;
  Item: String;
begin
  if not GetUserPath(Path) then
    Exit;
  if Pos(LowerCase(Dir), LowerCase(Path)) = 0 then
    Exit;
  List := TStringList.Create;
  OutList := TStringList.Create;
  try
    List.Delimiter := ';';
    List.QuoteChar := #0;
    List.DelimitedText := Path;
    for i := 0 to List.Count - 1 do
    begin
      Item := Trim(List[i]);
      if (Item <> '') and (LowerCase(Item) <> LowerCase(Dir)) then
        OutList.Add(Item);
    end;
    OutList.Delimiter := ';';
    OutList.QuoteChar := #0;
    RegWriteExpandStringValue(HKCU, 'Environment', 'Path', OutList.DelimitedText);
    RefreshEnv;
  finally
    OutList.Free;
    List.Free;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('addpath') then
      AddDirToPath(ExpandConstant('{app}\cpp_runner'));
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemoveDirFromPath(ExpandConstant('{app}\cpp_runner'));
end;
