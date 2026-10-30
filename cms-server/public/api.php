<?php
declare(strict_types=1);
ini_set('display_errors','0');ini_set('log_errors','1');require __DIR__.'/core.php';require __DIR__.'/publish.php';require __DIR__.'/leads.php';
header('Cache-Control: no-store');header('X-Content-Type-Options: nosniff');header('X-Frame-Options: DENY');header('X-Robots-Tag: noindex, nofollow');header('Referrer-Policy: same-origin');
try {
 $c=config();if(!testing()&&empty($_SERVER['HTTPS'])&&($_SERVER['SERVER_PORT']??0)!=443)fail('Panel wymaga bezpiecznego połączenia HTTPS.',403);
 $action=$_GET['action']??'me';$method=$_SERVER['REQUEST_METHOD'];$writes=['login','logout','password','create','save','upload','publish','archive','restore','lead_update'];if(in_array($action,$writes,true)&&$method!=='POST')fail('Niedozwolona metoda.',405);
 if($action==='login'){
  same_origin();$data=input();$key=hash('sha256',$_SERVER['REMOTE_ADDR']??'local');$blocked=state(function(&$s)use($key){$s['attempts']=array_filter($s['attempts']??[],fn($r)=>$r['at']>time()-3600);$a=$s['attempts'][$key]??['count'=>0,'at'=>time()];return $a['count']>=8&&$a['at']>time()-900;});if($blocked)fail('Za dużo prób. Spróbuj ponownie za 15 minut.',429);
  if(strlen((string)($data['password']??''))>128)fail('Nieprawidłowy login lub hasło.',401);
  $auth=state(fn(&$s)=>['hash'=>$s['passwordHash'],'version'=>$s['authVersion'],'change'=>$s['mustChangePassword']],false);$ok=password_verify((string)($data['password']??''),$auth['hash'])&&hash_equals($c['login'],(string)($data['login']??''));
  state(function(&$s)use($key,$ok){if($ok)unset($s['attempts'][$key]);else{$s['attempts'][$key]=['count'=>($s['attempts'][$key]['count']??0)+1,'at'=>time()];}});if(!$ok)fail('Nieprawidłowy login lub hasło.',401);
  session_open();session_regenerate_id(true);$_SESSION=['login'=>$c['login'],'authVersion'=>$auth['version'],'csrf'=>bin2hex(random_bytes(24)),'created'=>time(),'seen'=>time()];out(['ok'=>true,'csrf'=>$_SESSION['csrf'],'mustChangePassword'=>$auth['change']]);
 }
 authenticated(in_array($action,$writes,true),in_array($action,['me','password','logout'],true));
 if($action==='lead_list')out(lead_list());
 if($action==='lead_item')out(['lead'=>lead_load(record_id())]);
 if($action==='lead_update')out(['lead'=>lead_update(record_id(),input())]);
 if($action==='lead_photo'){$number=filter_var($_GET['number']??'',FILTER_VALIDATE_INT);$path=lead_photo_path(record_id(),$number===false?0:$number);header('Content-Type: image/jpeg');header('Content-Length: '.filesize($path));header('Content-Disposition: inline; filename="zdjecie-dzialki.jpg"');readfile($path);exit;}
 if($action==='me'){session_open();$csrf=$_SESSION['csrf'];session_write_close();$d=state(fn(&$s)=>['mustChangePassword'=>$s['mustChangePassword'],'lastCommit'=>$s['lastCommit'],'publishing'=>!empty($s['publishing']),'history'=>$s['history']],false);out(['login'=>$c['login'],'csrf'=>$csrf,'siteUrl'=>$c['site_url'],...$d]);}
 if($action==='logout'){session_open();$_SESSION=[];session_destroy();setcookie(session_name(),'',time()-3600,'/','',!testing(),true);out(['ok'=>true]);}
 if($action==='password'){
  $d=input();$password=(string)($d['newPassword']??'');if(strlen($password)<12||strlen($password)>128)fail('Hasło powinno mieć od 12 do 128 znaków.');
  $version=state(function(&$s)use($d,$password){if(!password_verify((string)($d['currentPassword']??''),$s['passwordHash']))throw new InvalidArgumentException('Nieprawidłowe obecne hasło.');$s['passwordHash']=password_hash($password,PASSWORD_DEFAULT);$s['mustChangePassword']=false;return ++$s['authVersion'];});session_open();session_regenerate_id(true);$_SESSION['authVersion']=$version;$_SESSION['csrf']=bin2hex(random_bytes(24));out(['ok'=>true,'csrf'=>$_SESSION['csrf']]);
 }
 if($action==='list'){$kind=collection();out(['items'=>state(fn(&$s)=>array_values(array_map('summary',$s[$kind])),false)]);}
 if($action==='item'){$kind=collection();$id=record_id();$row=state(fn(&$s)=>$s[$kind][$id]??null,false);if(!$row)fail('Nie znaleziono treści.',404);out(['item'=>$row['draft'],'meta'=>summary($row)]);}
 if($action==='create'){
  $kind=collection();$result=state(function(&$s)use($kind){$id=($kind==='projects'?'project-':'article-').bin2hex(random_bytes(8));$base=['id'=>$id,'slug'=>'nowy-'.bin2hex(random_bytes(4)),'legacy'=>false,'cover'=>'','seoTitle'=>'','seoDescription'=>'','updatedAt'=>gmdate('c')];
   if($kind==='projects'){$number=1;foreach($s['projects'] as $r)$number=max($number,$r['draft']['number']+1);$base+=['number'=>$number,'name'=>'Nowy projekt','place'=>'','area'=>'','facts'=>['Styl'=>'','Główne elementy'=>''],'description'=>[],'images'=>[],'display_order'=>0,'featured'=>true];}
   else $base+=['title'=>'Nowy artykuł','summary'=>'','category'=>'Ogrodowy notatnik','date'=>date('Y-m-d'),'blocks'=>[['type'=>'heading','text'=>''],['type'=>'paragraph','text'=>'']]];
   $s[$kind][$id]=['draft'=>$base,'published'=>null,'version'=>1,'archived'=>false,'savedAt'=>gmdate('c')];return ['item'=>$base,'meta'=>summary($s[$kind][$id])];});out($result,201);
 }
 if($action==='save'){$kind=collection();$id=record_id();$data=input();$result=state(function(&$s)use($kind,$id,$data){if(!isset($s[$kind][$id]))throw new InvalidArgumentException('Nie znaleziono treści.');$row=&$s[$kind][$id];if(($data['version']??0)!==$row['version'])throw new RuntimeException('Ta treść została zmieniona w drugim oknie. Odśwież panel.');$row['draft']=clean_record($data['item']??[],$row['draft'],$kind,$s);$row['version']++;$row['savedAt']=gmdate('c');return ['item'=>$row['draft'],'meta'=>summary($row)];});out($result);}
 if($action==='upload')out(['image'=>upload_photo()],201);
 if($action==='media'){
  $file=$_GET['file']??'';if(!preg_match('~^assets/cms/[a-f0-9]{32}(?:-(?:thumb|display|card))?\.webp$~D',$file))fail('Nie znaleziono zdjęcia.',404);$path=private_dir().'/uploads/'.basename($file);if(!is_file($path)){$known=state(fn(&$s)=>$s['media'][preg_replace('/-(thumb|display|card)\\.webp$/','.webp',$file)]['published']??false,false);if(!$known)fail('Nie znaleziono zdjęcia.',404);header('Location: '.rtrim($c['site_url'],'/').'/'.$file,302);exit;}header('Content-Type: image/webp');header('Content-Length: '.filesize($path));readfile($path);exit;
 }
 if($action==='publish'){$kind=collection();$id=record_id();$data=input();out(publish_record($kind,$id,(int)($data['version']??0)));}
 if($action==='archive'){$kind=collection();$id=record_id();$data=input();$published=state(fn(&$s)=>isset($s[$kind][$id])&&$s[$kind][$id]['published']!==null,false);if($published)out(publish_record($kind,$id,(int)($data['version']??0),true));state(function(&$s)use($kind,$id){if(!isset($s[$kind][$id]))throw new InvalidArgumentException('Nie znaleziono treści.');$s[$kind][$id]['archived']=true;});out(['ok'=>true]);}
 if($action==='restore'){$kind=collection();$id=record_id();state(function(&$s)use($kind,$id){if(!isset($s[$kind][$id]))throw new InvalidArgumentException('Nie znaleziono treści.');$s[$kind][$id]['archived']=false;});out(['ok'=>true]);}
 if($action==='publication'){
  $sha=state(fn(&$s)=>$s['lastCommit'],false);if(!$sha)out(['status'=>'idle']);$runs=github('GET','/actions/workflows/cms-publish.yml/runs?head_sha='.rawurlencode($sha).'&per_page=1');$run=$runs['workflow_runs'][0]??null;
  // A repair commit may successfully deploy the same publication after its original build failed.
  if(!$run||($run['status']==='completed'&&$run['conclusion']!=='success')){
   $latest=github('GET','/actions/workflows/cms-publish.yml/runs?branch='.rawurlencode($c['branch']??'main').'&per_page=1')['workflow_runs'][0]??null;
   if($latest&&$latest['head_sha']!==$sha){
    $comparison=github('GET','/compare/'.rawurlencode($sha).'...'.rawurlencode($latest['head_sha']));
    if(in_array($comparison['status']??'',['ahead','identical'],true)){
     $remote=github('GET','/contents/cms/published.json?ref='.rawurlencode($latest['head_sha']));
     $snapshot=json_decode(base64_decode($remote['content'],true),true,512,JSON_THROW_ON_ERROR);
     $revision=state(fn(&$s)=>$s['revision'],false);
     if(($snapshot['revision']??null)===$revision)$run=$latest;
    }
   }
  }

  out(['commit'=>$sha,'status'=>!$run?'queued':($run['status']!=='completed'?'building':($run['conclusion']==='success'?'published':'failed')),'message'=>$run&&$run['conclusion']==='failure'?'Publikacja wymaga sprawdzenia przez opiekuna strony. Szkic i poprzednia strona zostały zachowane.':null]);
 }
 fail('Nie znaleziono tej funkcji.',404);
}catch(InvalidArgumentException $e){fail($e->getMessage(),422);}catch(Throwable $e){error_log('CMS: '.$e->getMessage());fail($e instanceof RuntimeException?$e->getMessage():'Nie udało się wykonać operacji. Spróbuj ponownie.',503);}