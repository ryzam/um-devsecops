// Kedai Bengkel (ASP.NET Core): app SENGAJA tidak selamat untuk latihan DevSecOps.
// Jangan deploy di mana-mana selain persekitaran lab anda sendiri.
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Data.Sqlite;
using Newtonsoft.Json;

const string ConnectionString = "Data Source=app.db";

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddOpenApi();
builder.Services.AddCors(o => o.AddDefaultPolicy(p => p.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod()));

var app = builder.Build();

app.UseDeveloperExceptionPage();
app.UseCors();
app.MapOpenApi();

Db.Init(ConnectionString);

static IResult Html(string body) =>
    Results.Content(
        "<!doctype html><html lang='ms'><head><meta charset='utf-8'><title>Kedai Bengkel</title></head><body>" +
        "<nav><a href='/'>Utama</a> | <a href='/search?q='>Cari</a> | <a href='/guestbook'>Buku pelawat</a> | <a href='/login'>Log masuk</a></nav><hr>" +
        body + "</body></html>",
        "text/html; charset=utf-8");

app.MapGet("/", () => Html(
    "<h1>Kedai Bengkel</h1><ul>" +
    "<li><a href='/search?q=laptop'>Cari produk</a></li>" +
    "<li><a href='/guestbook'>Buku pelawat</a></li>" +
    "<li><a href='/ping?host=127.0.0.1'>Alat ping</a></li>" +
    "<li><a href='/download?file=notis.txt'>Muat turun notis</a></li>" +
    "<li><a href='/login'>Log masuk</a></li>" +
    "<li><a href='/admin'>Admin</a></li>" +
    "<li><a href='/openapi/v1.json'>Dokumen OpenAPI</a></li></ul>"));

// SQL injection + reflected XSS
app.MapGet("/search", (string? q) =>
{
    q ??= "";
    var sql = "SELECT id, name, price FROM products WHERE name LIKE @q";
    var rows = new StringBuilder();
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();
    try
    {
        using var cmd = new SqliteCommand(sql, conn);
        cmd.Parameters.AddWithValue("@q", "%" + q + "%");
        using var r = cmd.ExecuteReader();
        while (r.Read())
            rows.Append($"<tr><td>{r.GetInt64(0)}</td><td>{r.GetString(1)}</td><td>{r.GetDouble(2):F2}</td></tr>");
    }
    catch (Exception ex)
    {
        rows.Append("<tr><td colspan='3'>Ralat: " + ex.Message + "</td></tr>");
    }
    return Html($"<h1>Hasil carian untuk: {q}</h1><table border='1'><tr><th>ID</th><th>Nama</th><th>Harga (RM)</th></tr>{rows}</table>");
});

// Stored XSS + tiada perlindungan CSRF
app.MapGet("/guestbook", () =>
{
    var items = new StringBuilder();
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();
    using var cmd = new SqliteCommand("SELECT name, message FROM guestbook ORDER BY id DESC", conn);
    using var r = cmd.ExecuteReader();
    while (r.Read())
        items.Append($"<li><b>{r.GetString(0)}</b>: {r.GetString(1)}</li>");
    return Html(
        "<h1>Buku pelawat</h1>" +
        "<form method='post' action='/guestbook'>" +
        "<input name='name' placeholder='Nama'> <input name='message' placeholder='Mesej'> <button>Hantar</button></form>" +
        $"<ul>{items}</ul>");
});

app.MapPost("/guestbook", async (HttpRequest req) =>
{
    var form = await req.ReadFormAsync();
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();
    using var cmd = new SqliteCommand("INSERT INTO guestbook (name, message) VALUES ($n, $m)", conn);
    cmd.Parameters.AddWithValue("$n", form["name"].ToString());
    cmd.Parameters.AddWithValue("$m", form["message"].ToString());
    cmd.ExecuteNonQuery();
    return Results.Redirect("/guestbook");
});

// Command injection
app.MapGet("/ping", (string? host) =>
{
    host ??= "127.0.0.1";
    if (!System.Text.RegularExpressions.Regex.IsMatch(host, @"^[A-Za-z0-9.\-]{1,253}$"))
        return Results.BadRequest("Nama hos tidak sah");
    var psi = new ProcessStartInfo("ping")
    {
        RedirectStandardOutput = true,
        RedirectStandardError = true
    };
    psi.ArgumentList.Add("-c");
    psi.ArgumentList.Add("1");
    psi.ArgumentList.Add(host);
    using var p = Process.Start(psi)!;
    var output = p.StandardOutput.ReadToEnd() + p.StandardError.ReadToEnd();
    p.WaitForExit();
    return Html($"<h1>Ping {host}</h1><pre>{output}</pre>");
});

// Path traversal
app.MapGet("/download", (string file) =>
{
    var path = Path.Combine("files", file);
    return File.Exists(path) ? Results.Text(File.ReadAllText(path)) : Results.NotFound("Fail tidak ditemui");
});

// Open redirect
app.MapGet("/redirect", (string url) => Results.Redirect(url));

app.MapGet("/login", () => Html(
    "<h1>Log masuk</h1><form method='post' action='/login'>" +
    "<input name='username' placeholder='Nama pengguna'> <input name='password' type='password' placeholder='Kata laluan'> <button>Masuk</button></form>"));

// SQL injection pada log masuk + hash MD5 + cookie sesi yang lemah
app.MapPost("/login", async (HttpRequest req, HttpResponse res) =>
{
    var form = await req.ReadFormAsync();
    var username = form["username"].ToString();
    var password = form["password"].ToString();
    var sql = "SELECT username, role FROM users WHERE username = @u AND password_hash = @p";
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();
    using var cmd = new SqliteCommand(sql, conn);
    cmd.Parameters.AddWithValue("@u", username);
    cmd.Parameters.AddWithValue("@p", Db.Md5(password));
    using var r = cmd.ExecuteReader();
    if (r.Read())
    {
        var name = r.GetString(0);
        var role = r.GetString(1);
        res.Cookies.Append("session", Convert.ToBase64String(Encoding.UTF8.GetBytes(name + ":" + role)));
        return Html($"<h1>Selamat datang, {name}</h1><p>Peranan: {role}</p>");
    }
    return Html("<h1>Log masuk gagal</h1><p>Nama pengguna atau kata laluan salah.</p>");
});

// Pengesahan rosak: peranan dipercayai daripada cookie yang boleh dipalsukan klien
app.MapGet("/admin", (HttpRequest req) =>
{
    var cookie = req.Cookies["session"];
    var role = "";
    try
    {
        if (cookie is not null)
            role = Encoding.UTF8.GetString(Convert.FromBase64String(cookie)).Split(':').Last();
    }
    catch (FormatException) { }
    if (role != "admin")
        return Html("<h1>Akses ditolak</h1>");

    var items = new StringBuilder();
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();
    using var cmd = new SqliteCommand("SELECT username, email, password_hash FROM users", conn);
    using var r = cmd.ExecuteReader();
    while (r.Read())
        items.Append($"<tr><td>{r.GetString(0)}</td><td>{r.GetString(1)}</td><td>{r.GetString(2)}</td></tr>");
    return Html($"<h1>Panel admin</h1><table border='1'>{items}</table>");
});

// IDOR: tiada pengesahan dan hash kata laluan didedahkan
app.MapGet("/api/users/{id:int}", (int id) =>
{
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();
    using var cmd = new SqliteCommand("SELECT id, username, email, role, password_hash FROM users WHERE id = $id", conn);
    cmd.Parameters.AddWithValue("$id", id);
    using var r = cmd.ExecuteReader();
    if (!r.Read())
        return Results.NotFound();
    return Results.Json(new
    {
        id = r.GetInt64(0),
        username = r.GetString(1),
        email = r.GetString(2),
        role = r.GetString(3),
        passwordHash = r.GetString(4)
    });
});

app.MapGet("/api/products/{id:int}", (int id) =>
{
    using var conn = new SqliteConnection(ConnectionString);
    conn.Open();
    using var cmd = new SqliteCommand("SELECT id, name, price FROM products WHERE id = $id", conn);
    cmd.Parameters.AddWithValue("$id", id);
    using var r = cmd.ExecuteReader();
    return r.Read()
        ? Results.Json(new { id = r.GetInt64(0), name = r.GetString(1), price = r.GetDouble(2) })
        : Results.NotFound();
});

// Deserialization tidak selamat
app.MapPost("/api/import", async (HttpRequest req) =>
{
    using var reader = new StreamReader(req.Body);
    var body = await reader.ReadToEndAsync();
    var obj = JsonConvert.DeserializeObject<Dictionary<string, object>>(body);
    return Results.Ok(new { received = obj?.GetType().Name });
});

app.Run();

static class Db
{
    public static void Init(string connectionString)
    {
        using var conn = new SqliteConnection(connectionString);
        conn.Open();
        Exec(conn, "CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL)");
        Exec(conn, "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, role TEXT, password_hash TEXT)");
        Exec(conn, "CREATE TABLE IF NOT EXISTS guestbook (id INTEGER PRIMARY KEY, name TEXT, message TEXT)");

        using var check = new SqliteCommand("SELECT COUNT(*) FROM products", conn);
        if ((long)check.ExecuteScalar()! > 0)
            return;

        Exec(conn, "INSERT INTO products (name, price) VALUES ('Laptop Bengkel 14 inci', 2499.00), ('Tetikus tanpa wayar', 59.90), ('Papan kekunci mekanikal', 199.00)");
        Exec(conn, $"INSERT INTO users (username, email, role, password_hash) VALUES ('admin', 'admin@kedai.test', 'admin', '{Md5("admin123")}'), ('alice', 'alice@kedai.test', 'user', '{Md5("kata-laluan-alice")}')");
        Exec(conn, "INSERT INTO guestbook (name, message) VALUES ('Aisyah', 'Kedai yang bagus!')");
    }

    static void Exec(SqliteConnection conn, string sql)
    {
        using var cmd = new SqliteCommand(sql, conn);
        cmd.ExecuteNonQuery();
    }

    // MD5 untuk kata laluan: sengaja lemah
    public static string Md5(string s) =>
        Convert.ToHexString(MD5.HashData(Encoding.UTF8.GetBytes(s))).ToLowerInvariant();
}
