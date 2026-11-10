<?php

// Kedai Bengkel (Laravel): app SENGAJA tidak selamat untuk latihan DevSecOps.

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;

Route::get('/', fn () => view('home'));

// SQL injection + reflected XSS
Route::get('/search', function (Request $request) {
    $q = $request->query('q', '');
    $error = null;
    $rows = [];
    try {
        $rows = DB::select("SELECT id, name, price FROM products WHERE name LIKE ?", ['%' . $q . '%']);
    } catch (\Throwable $e) {
        $error = $e->getMessage();
    }
    return view('search', ['q' => $q, 'rows' => $rows, 'error' => $error]);
});

// Stored XSS + CSRF dimatikan
Route::get('/guestbook', fn () => view('guestbook', ['items' => DB::table('guestbook')->orderByDesc('id')->get()]));
Route::post('/guestbook', function (Request $request) {
    DB::table('guestbook')->insert([
        'name' => $request->input('name'),
        'message' => $request->input('message'),
    ]);
    return redirect('/guestbook');
});

// Command injection
Route::get('/ping', function (Request $request) {
    $host = $request->query('host', '127.0.0.1');
    if (! preg_match('/^[A-Za-z0-9.\-]{1,253}$/', $host)) {
        abort(400, 'Nama hos tidak sah');
    }
    $output = shell_exec('ping -c 1 ' . escapeshellarg($host) . ' 2>&1');
    return view('ping', ['host' => $host, 'output' => $output]);
});

// Path traversal
Route::get('/download', function (Request $request) {
    $path = base_path('files/' . $request->query('file'));
    return file_exists($path)
        ? response(file_get_contents($path), 200, ['Content-Type' => 'text/plain'])
        : response('Fail tidak ditemui', 404);
});

// Open redirect
Route::get('/redirect', fn (Request $request) => redirect($request->query('url')));

Route::get('/login', fn () => view('login'));

// SQL injection pada log masuk + MD5 + cookie sesi lemah (tanpa HttpOnly/Secure)
Route::post('/login', function (Request $request) {
    $username = $request->input('username');
    $hash = md5((string) $request->input('password'));
    $rows = DB::select("SELECT name, role FROM users WHERE name = ? AND password = ?", [$username, $hash]);
    if (count($rows) === 0) {
        return response('<h1>Log masuk gagal</h1>', 200);
    }
    $value = base64_encode($rows[0]->name . ':' . $rows[0]->role);
    return response('<h1>Selamat datang, ' . $rows[0]->name . '</h1>')
        ->withCookie(cookie('session', $value, 60, '/', null, false, false, true));
});

// Pengesahan rosak: peranan dipercayai daripada cookie yang boleh dipalsukan klien
Route::get('/admin', function () {
    $decoded = base64_decode($_COOKIE['session'] ?? '', true) ?: '';
    $parts = explode(':', $decoded);
    if (end($parts) !== 'admin') {
        return response('<h1>Akses ditolak</h1>', 403);
    }
    return view('admin', ['users' => DB::table('users')->get()]);
});

// IDOR: tiada pengesahan dan hash kata laluan didedahkan ($hidden dikosongkan)
Route::get('/api/users/{id}', fn ($id) => User::findOrFail($id));
Route::get('/api/products/{id}', fn ($id) => DB::table('products')->where('id', $id)->first());

// Mass assignment: pengguna boleh menetapkan `role` sendiri
Route::post('/api/profile/{id}', function (Request $request, $id) {
    $user = User::findOrFail($id);
    $user->update($request->all());
    return $user;
});

// Deserialization tidak selamat
Route::post('/api/import', function (Request $request) {
    $obj = unserialize($request->input('data'), ['allowed_classes' => false]);
    return response()->json(['received' => is_object($obj) ? get_class($obj) : gettype($obj)]);
});
