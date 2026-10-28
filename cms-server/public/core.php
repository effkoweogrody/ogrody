<?php
declare(strict_types=1);
/* Application files contain no credentials. Private data lives outside the web root. */
const MAX_IMAGE_BYTES = 3000000;
function private_dir(): string { return getenv('CMS_PRIVATE_DIR') ?: dirname(__DIR__,2).'/cms-private'; }
function config(): array { static $c; if ($c===null) { $f=private_dir().'/config.php'; if(!is_file($f)) throw new RuntimeException('Panel nie jest jeszcze skonfigurowany.'); $c=require $f; } return $c; }
function testing(): bool { return !empty(config()['testing']); }
function out(array $data,int $status=200): never { http_response_code($status);header('Content-Type: application/json; charset=utf-8');echo json_encode($data,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);exit; }
function fail(string $message,int $status=400): never { out(['error'=>$message],$status); }
function state(callable $callback,bool $write=true): mixed {
 $dir=private_dir();if(!is_dir($dir))mkdir($dir,0700,true);$lock=fopen($dir.'/state.lock','c+');if(!$lock||!flock($lock,LOCK_EX))throw new RuntimeException('Nie można otworzyć danych panelu.');
 try {
  $file=$dir.'/state.json';
  if(is_file($file))$s=json_decode(file_get_contents($file),true,512,JSON_THROW_ON_ERROR);
  else {
   $seed=json_decode(file_get_contents($dir.'/seed.json'),true,512,JSON_THROW_ON_ERROR);$s=['revision'=>$seed['revision'],'authVersion'=>1,'passwordHash'=>config()['password_hash'],'mustChangePassword'=>true,'media'=>[],'history'=>[],'lastCommit'=>null];
   foreach(['projects','articles'] as $kind){$s[$kind]=[];foreach($seed[$kind] as $item)$s[$kind][$item['id']]=['draft'=>$item,'published'=>$item,'version'=>1,'archived'=>false,'savedAt'=>gmdate('c')];}
  }
  $result=$callback($s);
  if($write){if(is_file($file))copy($file,$file.'.bak');$tmp=$file.'.tmp-'.bin2hex(random_bytes(6));file_put_contents($tmp,json_encode($s,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR),LOCK_EX);chmod($tmp,0600);if(!rename($tmp,$file))throw new RuntimeException('Nie udało się zapisać zmian.');}
  return $result;
 } finally {flock($lock,LOCK_UN);fclose($lock);}
}
function text(mixed $value,int $max=20000): string {
 if(!is_string($value)&&!is_numeric($value))return '';$s=trim(str_replace(["\u{2013}","\u{2014}"],'-',(string)$value));$s=preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/','',$s);
 if(mb_strlen($s)>$max)throw new InvalidArgumentException('Tekst jest za długi.');return $s;
}
function input(): array {if((int)($_SERVER['CONTENT_LENGTH']??0)>1200000)fail('Za duże żądanie.',413);$value=json_decode(file_get_contents('php://input'),true);if(!is_array($value))fail('Nieprawidłowe dane formularza.');return $value;}
function slug(string $value): string {$value=strtr(mb_strtolower($value),['ą'=>'a','ć'=>'c','ę'=>'e','ł'=>'l','ń'=>'n','ó'=>'o','ś'=>'s','ź'=>'z','ż'=>'z']);return trim(preg_replace('/[^a-z0-9]+/','-',$value),'-');}
function collection(): string {$kind=$_GET['kind']??'';if(!in_array($kind,['projects','articles'],true))fail('Nieprawidłowy typ treści.');return $kind;}
function record_id(): string {$id=$_GET['id']??'';if(!preg_match('/^[a-z0-9-]{1,120}$/D',$id))fail('Nieprawidłowy identyfikator.');return $id;}
function summary(array $row): array {$d=$row['draft'];return ['id'=>$d['id'],'title'=>$d['name']??$d['title'],'cover'=>$d['cover']??'','slug'=>$d['slug'],'published'=>$row['published']!==null,'dirty'=>$row['published']!==$d,'archived'=>$row['archived'],'version'=>$row['version'],'savedAt'=>$row['savedAt'],'display_order'=>$d['display_order']??0];}
function session_open(): void {
 if(session_status()===PHP_SESSION_ACTIVE)return;$dir=private_dir().'/sessions';if(!is_dir($dir))mkdir($dir,0700,true);ini_set('session.use_strict_mode','1');ini_set('session.use_only_cookies','1');session_save_path($dir);session_name('effkowe_cms');session_set_cookie_params(['lifetime'=>0,'path'=>'/','secure'=>!testing(),'httponly'=>true,'samesite'=>'Strict']);session_start();
}
function same_origin(): void {
 $expected=parse_url(config()['public_url']);$origin=$_SERVER['HTTP_ORIGIN']??'';$actual=parse_url($origin);
 if(!$actual||($actual['host']??'')!==($expected['host']??'')||($actual['scheme']??'')!==($expected['scheme']??'')||($actual['port']??null)!==($expected['port']??null))fail('Odśwież panel i spróbuj ponownie.',403);
}
function authenticated(bool $csrf=false,bool $allowPasswordChange=false): void {
 session_open();$auth=state(fn(&$s)=>['version'=>$s['authVersion'],'change'=>$s['mustChangePassword']],false);
 if(empty($_SESSION['login'])||($_SESSION['authVersion']??0)!==$auth['version']||time()-($_SESSION['seen']??0)>3600||time()-($_SESSION['created']??0)>43200){$_SESSION=[];session_destroy();fail('Zaloguj się ponownie.',401);}
 if($csrf){same_origin();if(!hash_equals($_SESSION['csrf']??'',$_SERVER['HTTP_X_CSRF_TOKEN']??''))fail('Sesja formularza wygasła. Odśwież panel.',403);}
 if($auth['change']&&!$allowPasswordChange)fail('Ustaw własne hasło przed rozpoczęciem pracy.',428);
 $_SESSION['seen']=time();session_write_close();
}
function known_images(array $s): array {
 $known=[];foreach(['projects','articles'] as $kind)foreach($s[$kind] as $row)foreach([$row['draft'],$row['published']] as $d){if(!$d)continue;foreach($d['images']??[] as $i)$known[$i['src']]=$i;}
 foreach($s['media'] as $src=>$m)$known[$src]=$m['image'];return $known;
}
function clean_record(array $raw,array $old,string $kind,array $s,bool $publishing=false): array {
 $d=$old;$d['legacy']=false;$d['updatedAt']=gmdate('c');$d['slug']=text($raw['slug']??$old['slug'],90);
 if(!preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/D',$d['slug']))throw new InvalidArgumentException('Adres może zawierać małe litery, cyfry i krótkie myślniki.');
 if($s[$kind][$old['id']]['published']!==null&&$d['slug']!==$old['slug'])throw new InvalidArgumentException('Adres opublikowanej strony jest stały.');
 foreach($s[$kind] as $id=>$row)if($id!==$old['id']&&$row['draft']['slug']===$d['slug'])throw new InvalidArgumentException('Taki adres już istnieje.');
 $known=known_images($s);
 if($kind==='projects'){
  $d['name']=text($raw['name']??'',180);$d['place']=text($raw['place']??'',180);$d['area']=text($raw['area']??'',100);$d['featured']=!empty($raw['featured']);$d['display_order']=max(-100,min(999,(int)($raw['display_order']??0)));
  $desc=$raw['description']??[];if(!is_array($desc)||count($desc)>50)throw new InvalidArgumentException('Nieprawidłowy opis projektu.');$d['description']=array_values(array_filter(array_map(fn($v)=>text($v,6000),$desc)));
  $d['facts']=['Lokalizacja'=>$d['place'],'Powierzchnia'=>$d['area'],'Styl'=>text($raw['facts']['Styl']??'',500),'Główne elementy'=>text($raw['facts']['Główne elementy']??'',1500)];
  $images=$raw['images']??[];if(!is_array($images)||count($images)>100)throw new InvalidArgumentException('Możesz dodać do 100 zdjęć.');$d['images']=[];$tops=0;$seen=[];
  foreach($images as $image){$src=$image['src']??'';if(!isset($known[$src])||isset($seen[$src]))throw new InvalidArgumentException('Wybierz zdjęcie przesłane do panelu.');$seen[$src]=true;$i=$known[$src];$i['alt']=text($image['alt']??'',250);$i['is_top']=!empty($image['is_top']);$tops+=(int)$i['is_top'];$d['images'][]=$i;}
  if($tops>1)throw new InvalidArgumentException('Wybierz tylko jeden widok z góry.');$d['has_top']=$tops===1;$d['cover']=text($raw['cover']??'',300);
  if($d['images']&&!isset($seen[$d['cover']]))$d['cover']=$d['images'][0]['src'];
  $title=$d['name'];$description=implode(' ',$d['description']);
  if($publishing&&(mb_strlen($title)<3||mb_strlen($description)<30||!$d['images']))throw new InvalidArgumentException('Uzupełnij nazwę, opis projektu i co najmniej jedno zdjęcie.');
 }else{
  $d['title']=text($raw['title']??'',180);$d['summary']=text($raw['summary']??'',1800);$d['category']=text($raw['category']??'Ogrodowy notatnik',100);$d['date']=text($raw['date']??date('Y-m-d'),10);
  if(!preg_match('/^\d{4}-\d{2}-\d{2}$/D',$d['date']))throw new InvalidArgumentException('Nieprawidłowa data.');
  $d['cover']=text($raw['cover']??'',300);if($d['cover']&&!isset($known[$d['cover']]))throw new InvalidArgumentException('Nieprawidłowe zdjęcie artykułu.');
  $blocks=$raw['blocks']??[];if(!is_array($blocks)||count($blocks)>100)throw new InvalidArgumentException('Artykuł może mieć do 100 bloków.');$d['blocks']=[];
  foreach($blocks as $b){if(!in_array($b['type']??'',['heading','paragraph','list','image'],true))throw new InvalidArgumentException('Nieprawidłowy fragment artykułu.');$b=['type'=>$b['type'],'text'=>text($b['text']??'',12000),'src'=>text($b['src']??'',300),'alt'=>text($b['alt']??'',250)];if($b['type']==='image'&&(($b['src']&&!isset($known[$b['src']]))||($publishing&&!$b['src'])))throw new InvalidArgumentException('Wybierz zdjęcie przesłane do panelu.');$d['blocks'][]=$b;}
  $title=$d['title'];$description=$d['summary']?:implode(' ',array_column($d['blocks'],'text'));
  if($publishing&&(mb_strlen($title)<3||mb_strlen(implode(' ',array_column($d['blocks'],'text')))<30))throw new InvalidArgumentException('Uzupełnij tytuł i treść artykułu.');
 }
 $d['seoTitle']=text($raw['seoTitle']??'',180)?:$title.' | Effkowe Ogrody';$d['seoDescription']=text($raw['seoDescription']??'',300);
 if(!$d['seoDescription'])$d['seoDescription']=mb_substr($title.'. '.$description.' Poznaj inspiracje i projekty pracowni Effkowe Ogrody we Wrocławiu.',0,260);
 if($publishing&&mb_strlen($d['seoDescription'])<90)$d['seoDescription']=mb_substr($d['seoDescription'].' Zobacz zdjęcia i poznaj pracownię projektowania ogrodów Ewy Katrycz - Effkowe Ogrody.',0,260);
 return $d;
}