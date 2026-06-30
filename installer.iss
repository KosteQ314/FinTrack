#define MyAppName "FinTrack"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "KosteQ314"
#define MyAppURL "https://github.com/KosteQ314/FinTrack"
#define MyAppExeName "FinTrack.exe"
#define MyAppCLIExeName "FinTrack-CLI.exe"

[Setup]
AppId={{13314af4-6aad-4110-8d17-ee5fa1fdda0f}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=FinTrack-Setup-v{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableDirPage=no
DisableProgramGroupPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full installation (App + CLI)"
Name: "app"; Description: "App only"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "app"; Description: "FinTrack App (overlay, voice control)"; Types: full app custom; Flags: fixed
Name: "cli"; Description: "FinTrack CLI (command line interface)"; Types: full custom

[Tasks]
Name: "startmenu"; Description: "Create Start Menu shortcuts"; GroupDescription: "Shortcuts:"; Components: app
Name: "startmenucli"; Description: "Create Start Menu shortcut for CLI"; GroupDescription: "Shortcuts:"; Components: cli
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Components: app
Name: "desktopiconcli"; Description: "Create a desktop shortcut for CLI"; GroupDescription: "Shortcuts:"; Components: cli

[Files]
; App files
Source: "dist\FinTrack\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: app
; CLI files
Source: "dist\FinTrack-CLI\*"; DestDir: "{app}\CLI"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: cli

[Icons]
; Start Menu
Name: "{group}\FinTrack"; Filename: "{app}\{#MyAppExeName}"; Components: app; Tasks: startmenu
Name: "{group}\FinTrack CLI"; Filename: "{app}\CLI\{#MyAppCLIExeName}"; Components: cli; Tasks: startmenucli
Name: "{group}\Uninstall FinTrack"; Filename: "{uninstallexe}"; Tasks: startmenu
; Desktop
Name: "{autodesktop}\FinTrack"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autodesktop}\FinTrack CLI"; Filename: "{app}\CLI\{#MyAppCLIExeName}"; Tasks: desktopiconcli

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch FinTrack"; Flags: nowait postinstall skipifsilent; Components: app
