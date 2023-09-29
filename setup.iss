﻿; Script generated by the Inno Script Studio Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define protected AppName "MetGem"
#define protected AppId "{15225AA3-EFDB-4261-A26D-138260F4B3D2}"
#define protected AppVersion GetVersionNumbersString("dist/MetGem/MetGem.exe")
#define AppPublisher "CNRS/ICSN"
#define AppURL "https://metgem.github.io"
#define AppExeName "MetGem.exe"

#include "isportable.iss"
#include "isversion.iss"

[Setup]
AppId={{#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={code:GetDefaultDirName|{#AppName}}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputBaseFilename=setup_{#AppName}
SolidCompression=no
OutputDir=.
SetupIconFile=main.ico
WizardImageFile=wiz-image.bmp
WizardSmallImageFile=wiz-small-image.bmp
WizardImageAlphaFormat=defined
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
ChangesAssociations=True
LicenseFile=dist\{#AppName}\LICENSE
Compression=lzma2/fast
WizardStyle=modern
Uninstallable=not IsPortable
CreateUninstallRegKey=not IsPortable
DisableDirPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}\data"; Check: IsPortable

[Files]
Source: "dist\{#AppName}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#AppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "api-ms-win-core-path-l1-1-0.dll"; DestDir: "{app}"; Flags: ignoreversion; OnlyBelowVersion: 6.2
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCR; SubKey: ".mnz"; ValueType: string; ValueData: "Molecular Network"; Flags: uninsdeletekey; Check: not IsPortable
Root: HKCR; SubKey: "Molecular Network"; ValueType: string; ValueData: "Molecular Network"; Flags: uninsdeletekey; Check: not IsPortable
Root: HKCR; SubKey: "Molecular Network\Shell\Open\Command"; ValueType: string; ValueData: """{app}\{#AppExeName}"" ""%1"""; Flags: uninsdeletekey; Check: not IsPortable
Root: HKCR; Subkey: "Molecular Network\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExeName},0"; Flags: uninsdeletevalue; Check: not IsPortable

[InstallDelete]
; Remove desktop icon if needed
Type: files; Name: {autodesktop}\{#AppName}.lnk; Tasks: not desktopicon; Check: not IsPortable
