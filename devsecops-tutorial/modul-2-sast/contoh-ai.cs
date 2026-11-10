// Contoh kod yang "dijana asisten AI" untuk permintaan:
//   "Tulis kelas C# untuk log masuk pengguna dan muat turun fail laporan, sambung ke SQL Server."
// Ia kelihatan kemas dan berfungsi, tetapi mengandungi vulnerability tipikal. Jangan guna dalam projek sebenar.
using System.Data.SqlClient;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;

public class PerkhidmatanPengguna
{
    private const string Sambungan = "Server=db.kedai.test;Database=kedai;User Id=sa;Password=Xk29vQ7mPz41Lr8T;";

    public bool SahkanLogMasuk(string nama, string kataLaluan)
    {
        using var conn = new SqlConnection(Sambungan);
        conn.Open();
        var sql = "SELECT COUNT(*) FROM Pengguna WHERE Nama = '" + nama + "' AND Hash = '" + Hash(kataLaluan) + "'";
        using var cmd = new SqlCommand(sql, conn);
        return (int)cmd.ExecuteScalar() > 0;
    }

    public static string Hash(string teks)
    {
        using var md5 = MD5.Create();
        return Convert.ToHexString(md5.ComputeHash(Encoding.UTF8.GetBytes(teks)));
    }

    public HttpClient BuatKlien()
    {
        var pengendali = new HttpClientHandler();
        pengendali.ServerCertificateCustomValidationCallback = (a, b, c, d) => true;
        return new HttpClient(pengendali);
    }

    public string BacaLaporan(string namaFail)
    {
        return File.ReadAllText("/data/laporan/" + namaFail);
    }
}
