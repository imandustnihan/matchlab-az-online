; MATCHLAB AZ Desktop Installer 0.9.56 (offline, native, per-user).
; Built only from the signed/unsigned published EXE; signing for Microsoft Store
; is a separate release step with a CA-trusted Authenticode certificate.
#define MyAppName "MATCHLAB AZ"
#define MyAppVersion "0.9.56"
#define MyAppExeName "MATCHLAB_AZ.exe"

[Setup]
AppId={{0A939D9E-606A-40ED-906B-CB6033BC7352}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=MATCHLAB AZ
AppPublisherURL=https://github.com/imandustnihan/matchlab-az-online
AppSupportURL=https://github.com/imandustnihan/matchlab-az-online/issues
DefaultDirName={localappdata}\Programs\MATCHLAB AZ
DefaultGroupName=MATCHLAB AZ
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\windows-app\installer-out
OutputBaseFilename=MATCHLAB_AZ_Setup_0.9.56_x64
SetupIconFile=..\branding\matchlab_icon.ico
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
VersionInfoVersion=0.9.56.0
VersionInfoProductName=MATCHLAB AZ
VersionInfoProductVersion=0.9.56
VersionInfoDescription=MATCHLAB AZ native Windows installer
AllowNoIcons=yes
MinVersion=10.0.19041
ChangesAssociations=no
AppMutex=MATCHLAB_AZ_v0956

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Create a Quick Launch shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\windows-app\out\MATCHLAB_AZ.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\MATCHLAB AZ"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\MATCHLAB AZ"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\MATCHLAB AZ"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch MATCHLAB AZ"; Flags: nowait postinstall skipifsilent
