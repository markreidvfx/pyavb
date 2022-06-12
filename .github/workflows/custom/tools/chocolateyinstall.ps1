$ErrorActionPreference = 'Stop';


$packageName= 'vcpython27'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://web.archive.org/web/20210106040224if_/https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'msi'
  url           = $url

  silentArgs    = "ALLUSERS=1 /qn /norestart /l*v `"$env:TEMP\chocolatey\$($packageName)\$($packageName).MsiInstall.log`""
  validExitCodes= @(0, 3010, 1641)

  softwareName  = 'Microsoft Visual C++ Compiler Package for Python 2.7'
  checksum      = '4e6342923a8153a94d44ff7307fcdd1f'
  checksumType  = 'md5'
}



Install-ChocolateyPackage @packageArgs