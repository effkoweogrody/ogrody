<?php
declare(strict_types=1);
function github(string $method,string $path,?array $body=null): array {
 $base=testing()?(config()['github_api']??'https://api.github.com'):'https://api.github.com';$repo=config()['repo'];if(!preg_match('~^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$~D',$repo))throw new RuntimeException('Nieprawidłowa konfiguracja publikacji.');
 $ch=curl_init($base.'/repos/'.$repo.$path);curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_CUSTOMREQUEST=>$method,CURLOPT_CONNECTTIMEOUT=>10,CURLOPT_TIMEOUT=>35,CURLOPT_HTTPHEADER=>['Authorization: Bearer '.config()['github_token'],'Accept: application/vnd.github+json','Content-Type: application/json','X-GitHub-Api-Version: 2022-11-28','User-Agent: Effkowe-Ogrody-CMS/1.0'],CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2]);
 if($body!==null)curl_setopt($ch,CURLOPT_POSTFIELDS,json_encode($body,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR));$raw=curl_exec($ch);$status=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);$error=curl_error($ch);curl_close($ch);
 if($raw===false||$status<200||$status>=300){error_log('CMS GitHub '.$method.' '.$path.' status '.$status);if(in_array($status,[409,422],true))throw new RuntimeException('W międzyczasie zmieniła się strona. Odśwież panel i spróbuj ponownie.');throw new RuntimeException($status===401||$status===403?'Połączenie z publikacją wymaga sprawdzenia przez opiekuna strony.':'Nie udało się potwierdzić publikacji. Sprawdź jej status przed ponowną próbą.');}
 return json_decode($raw,true,512,JSON_THROW_ON_ERROR)??[];
}
function publish_record(string $kind,string $id,int $version,bool $remove=false): array {
 set_time_limit(180);$job=bin2hex(random_bytes(12));
 $snapshot=state(function(&$s)use($kind,$id,$version,$remove,$job){
  if(!isset($s[$kind][$id]))throw new InvalidArgumentException('Nie znaleziono treści.');$row=$s[$kind][$id];if($row['archived'])throw new InvalidArgumentException('Najpierw przywróć materiał z archiwum.');if($row['version']!==$version)throw new InvalidArgumentException('Ta treść została zmieniona w drugim oknie. Odśwież panel.');
  if(!empty($s['publishing'])&&time()-$s['publishing']['started']<240)throw new RuntimeException('Trwa już publikowanie. Poczekaj na zakończenie.');
  $item=$remove?null:clean_record($row['draft'],$row['draft'],$kind,$s,true);$s['publishing']=['id'=>$job,'started'=>time(),'item'=>$id];$payload=['version'=>1,'revision'=>$s['revision']+1,'projects'=>[],'articles'=>[]];
  foreach(['projects','articles'] as $k)foreach($s[$k] as $rid=>$r){$p=($kind===$k&&$id===$rid)?$item:$r['published'];if($p!==null)$payload[$k][]=$p;}
  return ['item'=>$item,'payload'=>$payload,'revision'=>$s['revision'],'draftVersion'=>$row['version'],'media'=>$s['media']];
 });
 try {
  $branch=rawurlencode(config()['branch']??'main');$head=github('GET','/git/ref/heads/'.$branch)['object']['sha'];$commit=github('GET','/git/commits/'.$head);
  $remote=github('GET','/contents/cms/published.json?ref='.$branch);$current=json_decode(base64_decode($remote['content'],true),true,512,JSON_THROW_ON_ERROR);
  if(($current['revision']??null)!==$snapshot['revision'])throw new RuntimeException('Źródło strony zmieniło się poza panelem. Poproś opiekuna o synchronizację; szkic został zachowany.');
  $tree=[];$serialized=json_encode($snapshot['payload'],JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR)."\n";
  foreach($snapshot['media'] as $src=>$media){
   if(!str_contains($serialized,$src)||!empty($media['published']))continue;
   foreach($media['files'] as $file){$local=private_dir().'/uploads/'.basename($file);if(!is_file($local))throw new RuntimeException('Brakuje przesłanego zdjęcia. Dodaj je ponownie.');$blob=github('POST','/git/blobs',['content'=>base64_encode(file_get_contents($local)),'encoding'=>'base64']);$tree[]=['path'=>$file,'mode'=>'100644','type'=>'blob','sha'=>$blob['sha']];}
  }
  $tree[]=['path'=>'cms/published.json','mode'=>'100644','type'=>'blob','content'=>$serialized];$newTree=github('POST','/git/trees',['base_tree'=>$commit['tree']['sha'],'tree'=>$tree]);
  $message=($remove?'Ukrycie treści':'Publikacja treści').' - '.($snapshot['item']['name']??$snapshot['item']['title']??$id);$newCommit=github('POST','/git/commits',['message'=>$message,'tree'=>$newTree['sha'],'parents'=>[$head]]);
  github('PATCH','/git/refs/heads/'.$branch,['sha'=>$newCommit['sha'],'force'=>false]);
  state(function(&$s)use($kind,$id,$remove,$snapshot,$job,$newCommit,$serialized){
   if(($s['publishing']['id']??'')!==$job)throw new RuntimeException('Sprawdź status publikacji.');$s[$kind][$id]['published']=$snapshot['item'];
   if(!$remove&&$s[$kind][$id]['version']===$snapshot['draftVersion'])$s[$kind][$id]['draft']=$snapshot['item'];
   if($remove)$s[$kind][$id]['archived']=true;$s['revision']=$snapshot['payload']['revision'];$s['lastCommit']=$newCommit['sha'];
   foreach($s['media'] as $src=>&$media)if(str_contains($serialized,$src))$media['published']=true;unset($media);
   array_unshift($s['history'],['date'=>gmdate('c'),'kind'=>$kind,'id'=>$id,'action'=>$remove?'hidden':'published','commit'=>$newCommit['sha']]);$s['history']=array_slice($s['history'],0,30);unset($s['publishing']);
  });return ['ok'=>true,'commit'=>$newCommit['sha'],'status'=>'building','message'=>'Treść została przekazana do publikacji. Strona aktualizuje się zwykle w ciągu kilku minut.'];
 }catch(Throwable $e){state(function(&$s)use($job){if(($s['publishing']['id']??'')===$job)unset($s['publishing']);});throw $e;}
}
function upload_photo(): array {
 $file=$_FILES['file']??null;if(!$file||$file['error']!==UPLOAD_ERR_OK||$file['size']>MAX_IMAGE_BYTES)throw new InvalidArgumentException('Nie udało się przesłać zdjęcia. Wybierz JPG, PNG lub WebP do 3 MB po przygotowaniu.');
 $info=getimagesize($file['tmp_name']);if(!$info||!in_array($info['mime'],['image/jpeg','image/png','image/webp'],true)||$info[0]>3200||$info[1]>3200||$info[0]*$info[1]>12000000)throw new InvalidArgumentException('Nieprawidłowe zdjęcie lub zbyt duża rozdzielczość.');
 $image=imagecreatefromstring(file_get_contents($file['tmp_name']));if(!$image)throw new InvalidArgumentException('Nie można odczytać zdjęcia.');
 $dir=private_dir().'/uploads';if(!is_dir($dir))mkdir($dir,0700,true);$bytes=0;foreach(glob($dir.'/*.webp') as $path)$bytes+=filesize($path);if($bytes>65000000)throw new RuntimeException('Przestrzeń szkiców jest pełna. Opublikuj bieżące zdjęcia lub skontaktuj się z opiekunem strony.');
 $name=bin2hex(random_bytes(16));$base='assets/cms/'.$name;$files=[];$w=imagesx($image);$h=imagesy($image);$sizes=[''=>max($w,$h),'-display'=>min(1440,max($w,$h)),'-card'=>min(960,max($w,$h)),'-thumb'=>min(240,max($w,$h))];
 foreach($sizes as $suffix=>$edge){$scale=min(1,$edge/max($w,$h));$tw=max(1,(int)round($w*$scale));$th=max(1,(int)round($h*$scale));$out=imagecreatetruecolor($tw,$th);imagefill($out,0,0,imagecolorallocate($out,255,255,255));imagecopyresampled($out,$image,0,0,0,0,$tw,$th,$w,$h);$path=$base.$suffix.'.webp';if(!imagewebp($out,$dir.'/'.basename($path),92))throw new RuntimeException('Nie udało się przygotować zdjęcia.');chmod($dir.'/'.basename($path),0600);$files[]=$path;imagedestroy($out);}
 imagedestroy($image);$record=['src'=>$base.'.webp','width'=>$w,'height'=>$h,'display'=>$base.'-display.webp','card'=>$base.'-card.webp','thumb'=>$base.'-thumb.webp','alt'=>'','is_top'=>false];state(function(&$s)use($record,$files){$s['media'][$record['src']]=['image'=>$record,'files'=>$files,'created'=>time(),'published'=>false];});return $record;
}