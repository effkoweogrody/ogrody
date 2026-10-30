<?php
require __DIR__.'/../cms-server/public/contact-core.php';
file_put_contents(contact_store().'/config.php',"<?php return ['recipient'=>'owner@example.com','sender'=>'form@example.com'];");
$now=time();$token=contact_challenge($now-3);$input=['_token'=>$token,'imie'=>'Test formularza','email'=>'test@example.com','powierzchnia'=>'100','lokalizacja'=>'Wrocław','wiadomosc'=>'To jest przykładowy opis ogrodu do testów.','zgoda_rodo'=>'on'];$sent=0;
$send=function($to,$subject,$body,$headers)use(&$sent){assert($to==='owner@example.com');assert(!isset($headers['Cc'])&&!isset($headers['Bcc']));assert($headers['Reply-To']==='test@example.com');assert(str_contains($body,'Content-Type: text/plain; charset=UTF-8'));assert(!str_contains($subject,"\nBcc:"));$sent++;return true;};
$a=contact_submit($input,[],'127.0.0.1',$now,$send);assert($a['success']);$b=contact_submit($input,[],'127.0.0.1',$now,$send);assert($b['duplicate']&&$sent===1);
foreach([['_token'=>'bad'],['email'=>"attacker@example.com\r\nBcc: other@example.com"],['zgoda_rodo'=>''],['powierzchnia'=>'-2'],['wiadomosc'=>'test']] as $change){try{contact_submit(array_replace($input,$change),[],'127.0.0.1',$now,$send);throw new Exception('Invalid input accepted');}catch(InvalidArgumentException $e){}}
assert($sent===1);echo "PASS: fixed recipients, reply-to, idempotency, token, header-injection and form validation\n";
