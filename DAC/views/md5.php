<?php
$password = $argv[1];
$pass = md5($password, true);
$cryptedPass = mb_convert_encoding($pass, "ASCII", "ASCII");
echo $cryptedPass;
?>
