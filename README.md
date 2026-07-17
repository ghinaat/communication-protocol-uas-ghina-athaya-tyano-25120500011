<<<<<<< HEAD
# communication-protocol-uas-ghina-athaya-tyano-25120500011
=======
# UAS Mini Project Individu - Communication Protocol

## Identitas Mahasiswa
- Nama: Ghina Athaya Tyano
- NIM: 25120500011
- Kelas: Sains Data Profesional
- Mata Kuliah: Communication Protocol
- Judul Project: Task/Order Tracking API (Use Case 4)

## Link Penting
- GitHub: (isi link repo ini)
- YouTube Demo (Unlisted): (isi setelah upload video)

## Deskripsi Singkat
Mini project ini mengimplementasikan **Task/Order Tracking API** menggunakan
REST (Python/Flask) yang diorkestrasi dengan **n8n** untuk mensimulasikan
pembuatan task melalui webhook, retry saat gagal, dan notifikasi. Project ini
membuktikan alur request/response, error handling, observability, dan traffic
protocol secara teknis dan dapat direproduksi.

## Use Case
Use Case 4 - Task/Order Tracking (REST wajib, n8n sebagai orkestrasi opsional
yang diimplementasikan untuk memperkuat nilai desain arsitektur).

## Endpoint / Action

| No | Method | Path                     | Fungsi                                   |
|----|--------|--------------------------|-------------------------------------------|
| 1  | POST   | /api/tasks               | Membuat task baru                        |
| 2  | GET    | /api/tasks               | List semua task (bisa filter `?status=`) |
| 3  | GET    | /api/tasks/{id}          | Detail satu task                         |
| 4  | PUT    | /api/tasks/{id}/status   | Update status (dengan validasi transisi) |
| 5  | DELETE | /api/tasks/{id}          | Hapus/cancel task                        |

## Status Transition Rules
```
pending      -> in_progress, cancelled
in_progress  -> done, cancelled
done         -> (final, tidak bisa diubah lagi)
cancelled    -> (final, tidak bisa diubah lagi)
```

## Success Scenario (2)
1. POST /api/tasks dengan body valid -> 201 Created
2. PUT /api/tasks/{id}/status dari pending ke in_progress -> 200 OK

## Failure/Error Scenario (2, dilengkapi 1 tambahan)
1. POST /api/tasks tanpa field `title` -> 400 Bad Request (VALIDATION_ERROR)
2. PUT status ke transisi tidak valid (misal in_progress -> pending) -> 409 Conflict (INVALID_STATE_TRANSITION)
3. GET /api/tasks/{id} dengan id tidak ada -> 404 Not Found (TASK_NOT_FOUND)

## Observability
- Setiap request diberi `X-Request-ID` (correlation ID) di response header.
- `X-Response-Time` mencatat waktu proses tiap request (ms).
- Semua request/response tercatat di `app/app.log`.
- n8n execution history mencatat status tiap workflow run (success/retry/fail).

## Reliability
- Error contract konsisten: `{ "error": { "code", "message" }, "requestId", "timestamp" }`.
- Validasi input mencegah data tidak lengkap masuk ke sistem (400).
- Validasi state machine mencegah transisi status yang tidak logis (409).
- n8n melakukan retry otomatis (3x, delay 1 detik) saat API tidak merespon.

## Cara Menjalankan
```bash
cd app
pip install -r requirements.txt
python main.py
# Server berjalan di http://127.0.0.1:8088
```

Import `postman/collection.json` ke Postman, jalankan folder request secara
berurutan (create -> update status -> failure scenarios -> delete).

## Wireshark
Capture pada interface loopback dengan filter `http` saat mengirim request
dari Postman ke `127.0.0.1:8088`. Karena traffic berjalan di HTTP localhost
(bukan HTTPS), payload JSON dapat terlihat penuh di Wireshark. Jika di masa
depan API dipindah ke HTTPS, payload tidak akan terbaca dan hanya metadata
TCP/TLS handshake yang terlihat - keterbatasan ini akan dicatat di laporan.

## Struktur Repository
```
uas-commprotocol-ghina-25120500011/
├─ README.md
├─ docs/
│  ├─ architecture.svg / architecture.png
│  └─ (laporan & slide final diletakkan di sini sebelum submit)
├─ app/
│  ├─ main.py
│  └─ requirements.txt
├─ postman/
│  └─ collection.json
├─ n8n/
│  └─ workflow.json
└─ evidence/
   ├─ success-01.png (POST create task)
   ├─ success-02.png (PUT update status)
   ├─ failure-01.png (400 validation error)
   ├─ failure-02.png (409 invalid transition)
   ├─ failure-03.png (404 not found)
   ├─ observability-log.png (isi app.log)
   ├─ n8n-execution.png (execution history n8n)
   └─ wireshark-capture.png (capture traffic http)
```

## Catatan Keamanan
Repository ini tidak menampilkan token, password, API key, credential asli,
atau data pribadi. URL webhook pada `n8n/workflow.json` bersifat placeholder.
>>>>>>> master
