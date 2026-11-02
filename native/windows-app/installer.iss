; MATCHLAB AZ Windows installer, per-user by design.
; Installer is not signed: SmartScreen warnings are still possible.
#define AppName "MATCHLAB AZ"
#define AppVersion "0.9.45"
#define AppExe "MATCHLAB_AZ.exe"

[Setup]
AppId={{2A86F671-A410-4B4A-858A-53B12C66D9AB}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName=MATCHLAB AZ {#AppVersion}
AppPublisher=MATCHLAB AZ
AppPublisherURL=https://github.com/imandustnihan/matchlab-az-online
AppSupportURL=https://github.com/imandustnihan/matchlab-az-online/issues
DefaultDirName={localappdata}\Programs\MATCHLAB AZ
DefaultGroupName=MATCHLAB AZ
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer-out
OutputBaseFilename=MATCHLAB_AZ_Setup_v0945
SetupIconFile=..\branding\matchlab_icon.ico
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
VersionInfoVersion=0.9.45.0
VersionInfoDescription=MATCHLAB AZ Desktop Setup
VersionInfoProductName=MATCHLAB AZ
VersionInfoCompany=MATCHLAB AZ

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a MATCHLAB AZ desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "out\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\MATCHLAB AZ"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}"; Comment: "MATCHLAB AZ football center"
Name: "{autodesktop}\MATCHLAB AZ"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon; Comment: "MATCHLAB AZ football center"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch MATCHLAB AZ"; Flags: nowait postinstall skipifsilent
