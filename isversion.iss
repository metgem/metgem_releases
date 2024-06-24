// -- IsVersion.iss --
// Include file with support functions for version check
//

[CustomMessages]
english.UninstallOldVersion=Version %1 of {#AppName} is already installed. It has be uninstalled before.
french.UninstallOldVersion=La version %1 de {#AppName} est déjà  installée. Elle doit être désinstallée.
english.UninstallFailed=Failed to uninstall {#AppName} version %1. Please restart Windows and run setup again.
french.UninstallFailed=Impossible de désinstaller {#AppName} version %1. Merci de redémarrer Windows et de relancer l'installation.

[Code]     
<event('NextButtonClick')>
function NextButtonClick2(CurPageID: Integer): Boolean;
var
  oldVersion: String;
  uninstaller: String;
  ErrorCode: Integer;
begin
  if (CurPageID = wpSelectComponents) and WizardIsComponentSelected('portable') then
  begin
    if RegKeyExists(HKEY_LOCAL_MACHINE,
      'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppID}_is1') then
    begin
      RegQueryStringValue(HKEY_LOCAL_MACHINE,
          'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppID}_is1',
          'DisplayVersion', oldVersion);
      if MsgBox(FmtMessage(CustomMessage('UninstallOldVersion'), [oldVersion]), mbConfirmation, MB_OKCANCEL) = IDOK then
      begin
          RegQueryStringValue(HKEY_LOCAL_MACHINE,
            'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppID}_is1',
            'UninstallString', uninstaller);
          ShellExec('runas', uninstaller, '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
          if (ErrorCode <> 0) then
          begin
            MsgBox(CustomMessage('UninstallFailed}'), mbError, MB_OK );
            Result := False;
          end
          else
          begin
            Result := True;
          end;
      end
      else
      begin
        Result := False;
      end;
    end
    else
    begin
      Result := True;
    end;
  end
  else
  begin
    Result := true;
  end;
end;