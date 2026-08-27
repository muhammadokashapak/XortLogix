; installer_setup.iss
; Professional Windows Installer Script for Sales Co-Pilot AI
; Compatible with Inno Setup 6+

#define MyAppName "Sales Co-Pilot AI"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "XortLogix Enterprise AI"
#define MyAppURL "http://127.0.0.1:8000"
#define MyAppExeName "SalesCoPilot.exe"

[Setup]
AppId={{D37B4C89-5F1A-4C2E-8A01-9F54E7812B4D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\SalesCoPilot
DisableProgramGroupPage=yes
OutputBaseFilename=Sales_CoPilot_Setup
OutputDir=installer_output
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=app_icon.ico
ChangesAssociations=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Launch Sales Co-Pilot AI automatically on system startup"; GroupDescription: "System Integration:"; Flags: unchecked

[Files]
; Main PyInstaller executable bundle
Source: "dist\SalesCoPilot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; Auto-start with Windows if selected
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SalesCoPilotAI"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
; Launch Application after Setup Completes
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Sales Co-Pilot AI now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\sales_copilot.log"
Type: filesandordirs; Name: "{app}\sales_app.db"
