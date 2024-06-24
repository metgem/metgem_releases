// -- IsPortable.iss --
// Add a page to install app in portable mode
//

[CustomMessages]
english.CreateIconsFor=Create start menu and desktop icons for:
english.IconsCurrentUser=The current user only
english.IconsAllUsers=All users
english.PortablePageTitle=How should {#AppName} be installed?
english.InstallationMode={#AppName} can run as an installed application or in portable mode. Please select your preferred mode
english.InstallationType=Installation Type
english.InstallationModeNormal=Normal
english.InstallationModePortable=Portable
french.CreateIconsFor=Créer les icônes du menu démarrer et sur le bureau pour :
french.IconsCurrentUser=L'utilisateur courant uniquement
french.IconsAllUsers=Tous les utilisateurs
french.PortablePageTitle=Comment {#AppName} doit être installé ?
french.InstallationMode={#AppName} peut s'exécuter en tant qu'application installée ou en mode portable. Veuillez sélectionner le mode que vous préférez.
french.InstallationType=Type d'installation
french.InstallationModeNormal=Normal
french.InstallationModePortable=Portable

[Code]
var
  PortablePage: TInputOptionWizardPage;

function IsRegularUser(): Boolean;
begin
  Result := not (IsAdminInstallMode or IsPowerUserLoggedOn);
end;

function IsPortable(): Boolean;
begin
  if PortablePage = nil then
    Result := false
  else
    Result := PortablePage.Values[1];
end;

function DefaultInstallDirectory(Param: String): String;
begin
  if IsPortable then
    Result := ExpandConstant('{drive:{srcexe}}')
  else if IsRegularUser then
    Result := ExpandConstant('{localappdata}')
  else
    Result := ExpandConstant('{autopf}');
  Result := Result + '\{#AppName}';
end;

function UserOrCommonDirectory(Param: String): String;
begin
  if WizardIsTaskSelected('iconscommon') then
    Result := ExpandConstant('{common' + Param + '}')
  else
    Result := ExpandConstant('{user' + Param + '}')
end;

procedure InitializeWizard;
begin
  PortablePage := CreateInputOptionPage(wpLicense,
    CustomMessage('InstallationType'),
    CustomMessage('PortablePageTitle'),
    CustomMessage('InstallationMode'),
    True, False);
  PortablePage.Add(CustomMessage('InstallationModeNormal'));
  PortablePage.Add(CustomMessage('InstallationModePortable'));
  PortablePage.Values[0] := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  if (CurPageID = PortablePage.ID) then
  begin
    WizardForm.DirEdit.Text := DefaultInstallDirectory('');
    WizardForm.NoIconsCheck.Checked := IsPortable;
  end;
  Result := True;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  if (PageID = wpSelectProgramGroup) and IsPortable then
  begin
      WizardForm.NoIconsCheck.Checked := True;
      Result := True;
  end;
end;