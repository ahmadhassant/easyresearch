; Windows setup program for EasyResearch Desktop (Inno Setup 6.3 or later).
;
; Made from the portable folder that publish.ps1 creates:
;   powershell -ExecutionPolicy Bypass -File desktop\publish.ps1
;   "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" /DAppVersion=0.1.0 desktop\installer\EasyResearchDesktop.iss
; The result is desktop\release\EasyResearchDesktop-<version>-setup.exe.
; The GitHub workflow desktop-release.yml does the same and attaches the
; setup program to each GitHub release.
;
; By default it installs for the current user only (in
; %LOCALAPPDATA%\Programs), so no administrator rights are needed; the
; first page lets the user choose an installation for all users instead.

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\release\EasyResearchDesktop"
#endif
#define AppName "EasyResearch Desktop"
#define AppExe "EasyResearchDesktop.exe"

[Setup]
; The AppId identifies the application for upgrades and uninstalling; never change it.
AppId={{F495434F-C7C4-473A-861C-BEAFD2BA332E}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Ahmad B. Hassanat
AppPublisherURL=https://github.com/ahmadhassant/easyresearch
AppSupportURL=https://github.com/ahmadhassant/easyresearch/issues
AppUpdatesURL=https://github.com/ahmadhassant/easyresearch/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile=..\..\LICENSE
OutputDir=..\release
OutputBaseFilename=EasyResearchDesktop-{#AppVersion}-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName} {#AppVersion}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} setup
CloseApplications=yes
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; A new version replaces the bundled Python, its packages and the worker
; completely, so no files of an older version are left behind.
Type: filesandordirs; Name: "{app}\runtime"
Type: filesandordirs; Name: "{app}\worker"
Type: filesandordirs; Name: "{app}\modules"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autoprograms}\{#AppName} example files"; Filename: "{app}\examples"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Python writes compiled files (__pycache__) next to the code it runs; they
; are removed with the application. Results in Documents\EasyResearch Results
; are never touched.
Type: filesandordirs; Name: "{app}\runtime"
Type: filesandordirs; Name: "{app}\worker"
Type: filesandordirs; Name: "{app}\modules"
