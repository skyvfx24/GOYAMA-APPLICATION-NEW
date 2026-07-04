; installer.iss
[Setup]
AppName=Goyama Financial Reconciliation System
AppVersion=1.0.0
AppPublisher=Goyama Financial Services
DefaultDirName={autopf}\GoyamaRecon
DefaultGroupName=GoyamaRecon
UninstallDisplayIcon={app}\mfrecon.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=mfrecon_setup
SetupIconFile=favicon.ico
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
DisableWelcomePage=no
DisableDirPage=no

[Files]
Source: "dist\mfrecon\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Goyama Financial Reconciliation System"; Filename: "{app}\mfrecon.exe"
Name: "{autodesktop}\Goyama Financial Reconciliation System"; Filename: "{app}\mfrecon.exe"; IconFilename: "{app}\favicon.ico"

[Run]
Filename: "{app}\mfrecon.exe"; Description: "Launch Goyama Financial Reconciliation System"; Flags: postinstall nowait
