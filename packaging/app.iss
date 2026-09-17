; AI Teaching Assistant - Windows installer (Inno Setup 6+)
; Build: packaging\build.ps1 (tu dong nap backend + frontend + launcher)

#define MyAppName "AI Teaching Assistant"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "AI Teaching Assistant (Open Source)"
#define MyAppURL "https://github.com/Swon010191/Math_teacher"
#define MyAppExeName "AI-Teaching-Assistant.exe"

[Setup]
AppId={{8F3A2B1C-4D5E-4F6A-9B7C-A1B2C3D4E5F6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\AI Teaching Assistant
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Cai per-user: khong can quyen admin, khong hien UAC - phu hop may giao vien.
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=Setup-AI-Teaching-Assistant-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
; Tu nhac tat app dang chay khi cai de / go cai dat.
CloseApplications=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài Desktop"; GroupDescription: "Biểu tượng:"; Flags: unchecked
Name: "pix2text"; Description: "Tải AI nhận dạng công thức Pix2Text (~1-2 GB, cần mạng, mất 10-30 phút)"; GroupDescription: "AI nhận dạng:"; Flags: checkedonce

[Files]
; Launcher + cong cu cai AI
Source: "stage\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "stage\tools\*"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs
Source: "stage\setup_pix2text.bat"; DestDir: "{app}"; Flags: ignoreversion
; Backend dong goi (PyInstaller onedir) + frontend dist ben trong
Source: "stage\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Cai Pix2Text (hien cua so tien trinh, that bai van tiep tuc cai app)
Filename: "{app}\setup_pix2text.bat"; StatusMsg: "Đang tải AI Pix2Text (lâu, cần mạng)..."; Tasks: pix2text; Flags: runascurrentuser waituntilterminated; Check: Pix2TextChuaCo
; Mo app sau khi cai xong
Filename: "{app}\{#MyAppExeName}"; Description: "Mở {#MyAppName} ngay"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\backend"
Type: filesandordirs; Name: "{app}\pix2text-runtime"

[Code]
function Pix2TextChuaCo(): Boolean;
begin
  Result := not DirExists(ExpandConstant('{app}\pix2text-runtime\.venv'));
end;
