<?php
declare(strict_types=1);
ini_set('display_errors','0');ini_set('log_errors','1');require __DIR__.'/contact-core.php';
header('Content-Type: application/json; charset=utf-8');header('Cache-Control: no-store');header('X-Robots-Tag: noindex, nofollow');header('X-Content-Type-Options: nosniff');header('Vary: Origin');
function contact_response(array $body,int $status=200): never {http_response_code($status);echo json_encode($body,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);exit;}
$origin=$_SERVER['HTTP_ORIGIN']??'';if(!in_array($origin,['https://effkoweogrody.pl','https://www.effkoweogrody.pl'],true))contact_response(['success'=>false,'message'=>'Otwórz formularz na effkoweogrody.pl.'],403);header('Access-Control-Allow-Origin: '.$origin);header('Access-Control-Allow-Methods: GET, POST, OPTIONS');header('Access-Control-Allow-Headers: Content-Type');
if(empty($_SERVER['HTTPS'])||$_SERVER['HTTPS']==='off')contact_response(['success'=>false,'message'=>'Wymagane jest połączenie HTTPS.'],403);
if($_SERVER['REQUEST_METHOD']==='OPTIONS'){http_response_code(204);exit;}
try{
 if($_SERVER['REQUEST_METHOD']==='GET')contact_response(['token'=>contact_challenge(time())]);
 if($_SERVER['REQUEST_METHOD']!=='POST')contact_response(['success'=>false,'message'=>'Niedozwolona metoda.'],405);
 if((int)($_SERVER['CONTENT_LENGTH']??0)>7000000)contact_response(['success'=>false,'message'=>'Zdjęcia są za duże. Wybierz mniejsze pliki.'],413);
 foreach($_FILES as $file)if(($file['error']??UPLOAD_ERR_NO_FILE)!==UPLOAD_ERR_NO_FILE&&!is_uploaded_file($file['tmp_name']??''))throw new InvalidArgumentException('Nieprawidłowy załącznik.');
 contact_response(contact_submit($_POST,$_FILES,$_SERVER['REMOTE_ADDR']??'',time()));
}catch(OverflowException $e){contact_response(['success'=>false,'message'=>$e->getMessage()],429);}catch(InvalidArgumentException $e){contact_response(['success'=>false,'message'=>$e->getMessage()],422);}catch(Throwable $e){error_log('Effkowe contact: '.$e->getMessage());contact_response(['success'=>false,'message'=>$e instanceof RuntimeException?$e->getMessage():'Nie udało się przyjąć zapytania. Napisz bezpośrednio na e-mail.'],503);}
