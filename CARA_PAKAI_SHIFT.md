# Cara Pakai Definisi Shift (V6 - ATURAN BARU, yang benar)

## 1. Definisi di Pengaturan Shift - kode P1, P2, S1, S2, M1, M2, C, OFF
```
P1=6,8
P2=6,5
P3=7,8
P4=8,8
S1=11,8
S2=14,8
M1=22,8
C=CUTI
OFF=OFF
LIBUR=LIBUR
```
Format: `KODE=JAM_MULAI,DURASI`. Semua kode bisa di-setting jam + durasinya.
`C=CUTI`, `OFF=OFF`, `LIBUR=LIBUR` = tidak kerja.
Satu kode = satu jam + satu durasi. Tidak ada lagi duplikat `P=6,8` + `P=6,5` -
kalau mau beda jam, bedakan kodenya: `P1` vs `P2`.

## 2. Isi Excel dengan KODE (P1/S1/M1), bukan angka
| Nama | ... | 1 Nov | 2 Nov | 3 Nov | 4 Nov | 5 Nov | 6 Nov | 7 Nov |
| Dirlan | ... | OFF | P1 | P1 | P1 | P1 | P1 | OFF |
| Alwyd  | ... | OFF | P1 | P1 | P1 | P1 | P1 | P1 | OFF (lihat bawah) |

## 3. ATURAN WAKTU - yang benar (V6)
Cari BLOK kerja: hari kerja berturut-turut yang DIAPIT 2 OFF (OFF/LIBUR/C di kiri dan kanan).

- **Blok 5 hari kerja** (OFF | 5 hari | OFF):
  4 hari pertama tetap sesuai definisi (mis. 8 jam),
  **hari TERAKHIR sebelum OFF dipaksa jadi 5 JAM.**
  Contoh: OFF | P1 P1 P1 P1 P1 | OFF -> 8, 8, 8, 8, **5**

- **Blok 6 hari kerja** (OFF | 6 hari | OFF):
  **Hari terakhir TETAP 8 jam** (sesuai definisi, tidak dipotong).
  Contoh: OFF | P1 x6 | OFF -> 8, 8, 8, 8, 8, 8

- Blok 1-4 hari atau 7+ hari: tidak ada override, pakai definisi kode.
- Blok yang tidak diapit 2 OFF (terpotong awal/akhir bulan): tidak di-override,
  karena tidak terbukti "di antara 2 OFF".

## 4. Kenapa P2=6,5 masih ada?
P2 dipakai kalau kamu memang mau menulis `P2` di Excel untuk hari yang
sudah pasti 5 jam. Aturan blok di atas berlaku OTOMATIS walaupun kamu tulis
P1 di semua 5 hari - hari terakhir akan jadi 5 jam sendiri. Jadi kamu tidak
perlu pusing menulis P2 manual di hari terakhir, tapi tetap boleh.

## 5. Urutan
1. Buka app -> Pengaturan Shift -> paste daftar di atas -> Simpan
2. Unggah Jadwal Excel yang isinya kode P1/S1/M1 + OFF/C
3. Cek Widget 1: blok 5 hari harus tampil 8,8,8,8,5 dan blok 6 hari 8,8,8,8,8,8.
