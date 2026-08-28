#define MyAppName "MobilDesk POS"
#define MyAppVersion "2.0.19"
#define MyAppPublisher "MobilDesk POS Systems"
#define MyAppExeName "MobilDesk.exe"

[Setup]
AppId={{6A5CE9A8-092A-4CE7-9B44-5C011D7A3D55}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\MobilDesk
DefaultGroupName=MobilDesk POS
OutputDir=..\release
OutputBaseFilename=Instalar-MobilDesk
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\kiosko_logo.ico
ShowLanguageDialog=no
InfoBeforeFile=InfoBefore.txt
DisableProgramGroupPage=auto
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Messages]
spanish.WelcomeLabel1=¡Bienvenido al Asistente de Instalación de MobilDesk POS!
spanish.WelcomeLabel2=Este programa instalará [name] versión [ver] en su computadora.%n%nMobilDesk incluye control de ventas, inventario y productos unificado, caja chica, reportes, fiados y sincronización automática en la nube con la app móvil Android.%n%nSe recomienda cerrar cualquier otra aplicación antes de continuar.
spanish.FinishedHeadingLabel=¡Instalación de MobilDesk POS completada!
spanish.FinishedLabel=MobilDesk POS se ha instalado correctamente en su equipo.%n%nAl abrir el programa por primera vez, un asistente le guiará para configurar el nombre de su negocio, su cuenta de administrador y el enlace con su teléfono móvil.

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Crear un acceso directo en Inicio Rápido"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "..\package\MobilDesk\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\manual\Manual-MobilDesk.html"; DestDir: "{app}\manual"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\MobilDesk POS"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\Manual de MobilDesk POS"; Filename: "{app}\manual\Manual-MobilDesk.html"
Name: "{autodesktop}\MobilDesk POS"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall

