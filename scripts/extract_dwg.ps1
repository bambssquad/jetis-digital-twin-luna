param([Parameter(Mandatory=$true)][string]$Dwg,[Parameter(Mandatory=$true)][string]$Output,[string]$ProgId='AutoCAD.Application')
$ErrorActionPreference='Stop'
$sourcePath=(Resolve-Path -LiteralPath $Dwg).Path
$outputPath=[IO.Path]::GetFullPath($Output)
if ($sourcePath -eq $outputPath) { throw 'Output cannot overwrite source' }
$cad=$null;$db=$null
$warnings=New-Object System.Collections.Generic.List[string]
function Read-Entities($collection) {
 $records=New-Object System.Collections.Generic.List[object]
 foreach($e in $collection) {
  $r=@{type=$e.ObjectName;layer=$e.Layer;handle=$e.Handle}
  try {
   switch -Regex ($e.ObjectName) {
    '^AcDbLine$' {$r.a=$e.StartPoint;$r.b=$e.EndPoint;break}
    '^AcDb(2d|3d)?Polyline$' {$r.points=$e.Coordinates;$r.closed=$e.Closed; if($e.ObjectName -eq 'AcDbPolyline'){$r.elevation=$e.Elevation;$r.normal=$e.Normal;$r.bulges=@(for($i=0;$i -lt $r.points.Count/2;$i++){$e.GetBulge($i)})};break}
    '^AcDbCircle$' {$r.center=$e.Center;$r.radius=$e.Radius;$r.normal=$e.Normal;break}
    '^AcDbArc$' {$r.center=$e.Center;$r.radius=$e.Radius;$r.start=$e.StartAngle;$r.end=$e.EndAngle;$r.normal=$e.Normal;break}
    '^AcDbBlockReference$' {$r.name=$e.Name;$r.position=$e.InsertionPoint;$r.scale=@($e.XScaleFactor,$e.YScaleFactor,$e.ZScaleFactor);$r.rotation=$e.Rotation;$r.normal=$e.Normal;if($e.HasAttributes){$r.attributes=@($e.GetAttributes() | ForEach-Object {@{tag=$_.TagString;text=$_.TextString}})};break}
    '^AcDb(MText|Text)$' {$r.text=$e.TextString;$r.position=$e.InsertionPoint;$r.height=$e.Height;break}
    'Dimension$' {$r.measurement=$e.Measurement;$r.text=$e.TextOverride;$r.textPosition=$e.TextPosition;break}
    default {$r.unsupported=$true;$warnings.Add('Unsupported entity '+$e.ObjectName+' '+$e.Handle)}
   }
  } catch {$r.partial=$true;$warnings.Add('Partial entity '+$e.Handle+': '+$_.Exception.Message)}
  $records.Add($r)
 }
 return ,$records.ToArray()
}
try {
 $cad=[Runtime.InteropServices.Marshal]::GetActiveObject($ProgId)
 $major=([string]$cad.Version).Split('.')[0]
 $db=$cad.GetInterfaceObject('ObjectDBX.AxDbDocument.'+$major)
 $db.Open($sourcePath)
 $entities=Read-Entities $db.ModelSpace
 $blocks=@{}
 foreach($b in $db.Blocks){if(-not $b.IsLayout){$blocks[$b.Name]=@{origin=$b.Origin;isXref=$b.IsXRef;entities=(Read-Entities $b)};if($b.IsXRef){$warnings.Add('External reference: '+$b.Name)}}}
 $units=$null
 try {$units=$db.GetVariable('INSUNITS')} catch {$warnings.Add('INSUNITS unavailable; inspect drawing dimensions')}
 @{source_sha256=(Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash;insunits=$units;entities=$entities;blocks=$blocks;warnings=$warnings.ToArray()} | ConvertTo-Json -Depth 20 -Compress | Set-Content -LiteralPath $outputPath -Encoding utf8
 Write-Output ('Extracted {0} entities, {1} blocks, {2} warnings. Dimension and visual checks still required.' -f $entities.Count,$blocks.Count,$warnings.Count)
} finally {
 if($null -ne $db){[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($db)}
 if($null -ne $cad){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($cad)}
}
