#define MyAppName "KODA SYSTEM"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "MJBS COMPANY"
#define MyAppExeName "KODA_SYSTEM.exe"
#define MyAppAssocName "KODA SYSTEM"

[Setup]
AppId={{5E89C6D8-8F31-4E50-B6C0-D5C508A80C67}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\KODA_SYSTEM
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=KODA_SYSTEM_Instalador
SetupIconFile=KODA_SYSTEM.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "deploy\KODA_SYSTEM\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\KODA SYSTEM"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\KODA_SYSTEM.ico"
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\KODA_SYSTEM.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir KODA SYSTEM"; Flags: nowait postinstall skipifsilent
