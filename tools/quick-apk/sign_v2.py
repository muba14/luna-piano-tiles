"""Luna APK: zip hizalama (4 bayt) + APK Signature Scheme v2 imzası (RSA 2048, SHA-256).
Kullanım: python3 sign_v2.py girdi.apk cikti.apk anahtar_klasoru
"""
import os, struct, sys, zipfile, hashlib, datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

src, dst, keydir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(keydir, exist_ok=True)
kp, cp = os.path.join(keydir, 'luna-test-key.pem'), os.path.join(keydir, 'luna-test-cert.der')

# ---- anahtar ve sertifika (bir kez üretilir, sonraki sürümler aynı imzayla güncellenebilsin diye saklanır)
if os.path.exists(kp):
    key = serialization.load_pem_private_key(open(kp, 'rb').read(), None)
    cert_der = open(cp, 'rb').read()
else:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Luna Piano Tiles Test'),
                      x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Luna')])
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=365 * 30)).sign(key, hashes.SHA256()))
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    open(kp, 'wb').write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    open(cp, 'wb').write(cert_der)
pub_der = key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)

# ---- 1) yeniden paketle + hizala: resources.arsc ve png'ler sıkıştırmasız, veri başlangıcı 4 bayta hizalı
aligned = dst + '.aligned'
STORE = ('resources.arsc', '.png')
with zipfile.ZipFile(src) as zin, open(aligned, 'wb') as raw:
    with zipfile.ZipFile(raw, 'w') as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            zi = zipfile.ZipInfo(info.filename, date_time=(2026, 1, 1, 0, 0, 0))
            zi.external_attr = 0o644 << 16
            stored = info.filename == 'resources.arsc' or info.filename.endswith('.png')
            zi.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            if stored:
                off = raw.tell() + 30 + len(info.filename.encode())
                padlen = (-(off + 4)) % 4          # 4 baytlık ek alan başlığı + dolgu
                zi.extra = struct.pack('<HH', 0xD935, padlen) + b'\0' * padlen
            zout.writestr(zi, data)

apk = open(aligned, 'rb').read()
os.remove(aligned)

# ---- 2) zip bölümlerini bul
eocd = apk.rfind(b'PK\x05\x06')
cd_size, cd_off = struct.unpack('<II', apk[eocd + 12:eocd + 20])
sec1, sec3, sec4 = apk[:cd_off], apk[cd_off:cd_off + cd_size], apk[eocd:]

def chunked_digest(parts):
    digests = []
    for p in parts:
        for i in range(0, len(p), 1 << 20):
            c = p[i:i + (1 << 20)]
            digests.append(hashlib.sha256(b'\xa5' + struct.pack('<I', len(c)) + c).digest())
    return hashlib.sha256(b'\x5a' + struct.pack('<I', len(digests)) + b''.join(digests)).digest()

lp = lambda b: struct.pack('<I', len(b)) + b       # uzunluk önekli
ALG = 0x0103                                        # RSASSA-PKCS1-v1_5 + SHA2-256
digest = chunked_digest([sec1, sec3, sec4])
signed_data = lp(lp(struct.pack('<I', ALG) + lp(digest))) + lp(lp(cert_der)) + lp(b'')
sig = key.sign(signed_data, padding.PKCS1v15(), hashes.SHA256())
signer = lp(signed_data) + lp(lp(struct.pack('<I', ALG) + lp(sig))) + lp(pub_der)
v2_value = lp(lp(signer))
pair = struct.pack('<Q', 4 + len(v2_value)) + struct.pack('<I', 0x7109871a) + v2_value
block_size = len(pair) + 8 + 16
block = struct.pack('<Q', block_size) + pair + struct.pack('<Q', block_size) + b'APK Sig Block 42'

new_eocd = sec4[:16] + struct.pack('<I', cd_off + len(block)) + sec4[20:]
open(dst, 'wb').write(sec1 + block + sec3 + new_eocd)
print('imzalandı:', dst, len(sec1) + len(block) + len(sec3) + len(new_eocd), 'bayt')
print('sertifika SHA-256:', hashlib.sha256(cert_der).hexdigest())
