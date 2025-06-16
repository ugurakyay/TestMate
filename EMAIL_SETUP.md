# TestMate Studio - Email Ayarları

## Gmail SMTP Ayarları

TestMate Studio, plan talepleri için email gönderme özelliği kullanır. Gmail SMTP kullanarak email göndermek için aşağıdaki adımları takip edin:

### 1. Gmail App Password Oluşturma

1. Gmail hesabınıza giriş yapın
2. [Google Hesap Ayarları](https://myaccount.google.com/) sayfasına gidin
3. Sol menüden "Güvenlik" seçeneğini tıklayın
4. "2 Adımlı Doğrulama" bölümünü bulun ve etkinleştirin
5. "Uygulama Şifreleri" bölümünü bulun
6. "Uygulama Seç" dropdown'undan "Diğer (Özel ad)" seçin
7. İsim olarak "TestMate Studio" yazın
8. "Oluştur" butonuna tıklayın
9. 16 haneli şifreyi kopyalayın (örn: `abcd efgh ijkl mnop`)

### 2. Email Konfigürasyonu

`email_config.json` dosyasını düzenleyin:

```json
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "info@testmatestudio.com",
    "admin_email": "ugurakyay@gmail.com",
    "sender_password": "your-16-digit-app-password",
    "use_ssl": true,
    "use_tls": true
}
```

### 3. Environment Variable (Alternatif)

Alternatif olarak, environment variable kullanabilirsiniz:

```bash
export EMAIL_PASSWORD="your-16-digit-app-password"
```

### 4. Email Test

Email ayarlarını test etmek için:

```bash
curl http://localhost:8000/api/contact/test
```

### 5. Güvenlik Notları

- App password'ü asla kod içinde saklamayın
- Environment variable kullanımı önerilir
- Gmail hesabınızda 2 adımlı doğrulama etkin olmalıdır
- App password'ü düzenli olarak yenileyin

### 6. Email Şablonları

Sistem iki tür email gönderir:

1. **Admin Bildirimi**: Yeni plan talebi geldiğinde size bildirim
2. **Müşteri Onayı**: Müşteriye talebinin alındığını bildiren email

### 7. Sorun Giderme

**Hata: "Authentication failed"**
- App password'ün doğru olduğundan emin olun
- 2 adımlı doğrulamanın etkin olduğunu kontrol edin

**Hata: "Connection refused"**
- Firewall ayarlarını kontrol edin
- SMTP port'unun açık olduğundan emin olun

**Hata: "SSL/TLS required"**
- `use_ssl` ve `use_tls` ayarlarını kontrol edin
- Gmail için SSL/TLS zorunludur 