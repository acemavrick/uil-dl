[Setup]
AppName=UIL-DL
AppVersion=1.0.0.1
AppId={{CA564B92-37BA-4D85-B190-218890A7459D}}
DefaultDirName={localappdata}\UIL-DL
OutputBaseFilename=UILDL-Setup
OutputDir=dist
PrivilegesRequired=lowest
DisableDirPage=no

[Files]
Source: ".\dist\main.dist\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\UIL-DL"; Filename: "{app}\main.exe"
Name: "{userdesktop}\UIL-DL"; Filename: "{app}\main.exe"

[Run]
Filename: "{app}\main.exe"; Description: "Launch UIL-DL"; Flags: nowait postinstall skipifsilent