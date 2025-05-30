#define MyAppName "PDFCrop"
#define MyAppVersion GetEnv("PDFCROP_VERSION")
#define MyAppPublisher "Akimitsu Inoue"
#define MyAppExeName "pdfcrop.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=PDFCrop_Setup
SetupIconFile=src\resources\icons\PDFCrop_icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Dirs]
Name: "{localappdata}\PDFCrop\cache"; Permissions: users-modify
Name: "{tmp}\PDFCrop\pdfs"; Permissions: users-modify

[Files]
Source: "dist\pdfcrop.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PDFCrop"; Filename: "{app}\pdfcrop.exe"
Name: "{group}\Readme"; Filename: "{app}\README.md"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch PDFCrop"; Flags: nowait postinstall skipifsilent
