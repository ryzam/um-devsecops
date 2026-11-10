<?php
// Contoh kod yang "dijana asisten AI" untuk permintaan:
//   "Tulis skrip PHP untuk carian pengguna, muat halaman dan simpan tetapan daripada cookie."
// Ia kelihatan kemas dan berfungsi, tetapi mengandungi vulnerability tipikal. Jangan guna dalam projek sebenar.

$db = new mysqli('db.kedai.test', 'root', 'Xk29vQ7mPz41Lr8T', 'kedai');

// Carian pengguna
$id = $_GET['id'];
$hasil = $db->query("SELECT * FROM pengguna WHERE id = " . $id);

// Muat halaman mengikut parameter
include($_GET['halaman'] . '.php');

// Simpan hash kata laluan
$hash = md5($_POST['kata_laluan']);

// Pulihkan tetapan daripada cookie
$tetapan = unserialize(base64_decode($_COOKIE['tetapan']));

// Jalankan arahan untuk pratonton imej
system('convert ' . $_GET['fail'] . ' pratonton.png');

// Papar nama pengguna
echo "<h1>Selamat datang, " . $_GET['nama'] . "</h1>";
