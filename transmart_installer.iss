#define MyAppName "TransMart"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CongNhat"
#define MyAppExeName "TransMart.exe"

[Setup]
; Unique ID generated specifically for TransMart installer
AppId={{5C6B7B4B-9E3A-4F3B-BA8F-0FA3050FFB1F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={userpf}\{#MyAppName}
DisableDirPage=yes
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_build
OutputBaseFilename=TransMart_Setup
SetupIconFile=ui\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; PrivilegesRequired=lowest allows normal users to install without UAC Administrator prompt
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
