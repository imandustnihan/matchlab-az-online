; MATCHLAB AZ Windows native (WinForms), no browser/WebView2 required.
#define AppName "MATCHLAB AZ"
#define AppVersion "0.9.48"
#define AppExe "MATCHLAB_AZ.exe"

[Setup]
AppId={{2A86F671-A410-4B4A-858A-53B12C66D9AB}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName=MATCHLAB AZ {#AppVersion}
AppPublisher=MATCHLAB AZ
AppPublisherURL=https://github.com/imandustnihan/matchlab-az-online
DefaultDirName={localappdata}\Programs\MATCHLAB AZ
DefaultGroupName=MATCHLAB AZ
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer-out
OutputBaseFilename=MATCHLAB_AZ_Native_Setup_v0948
SetupIconFile=..\branding\matchlab_icon.ico
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
UsePreviousAppDir=yes
VersionInfoVersion=0.9.48.0
VersionInfoProductName=MATCHLAB AZ
VersionInfoCompany=MATCHLAB AZ

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstündə MATCHLAB AZ qısayolu yarat"; GroupDescription: "Qısayollar:"; Flags: checkedonce

[Files]
Source: "out\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\MATCHLAB AZ"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\MATCHLAB AZ"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "MATCHLAB AZ aç"; Flags: nowait postinstall skipifsilent
