import html
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

NAMA_APP = "CBS Mini Lab Kampus"
WIB = timezone(timedelta(hours=7))

# Bagan akun sederhana: kode -> (nama akun, saldo normal)
AKUN = {
    "101": ("Kas Teller", "D"),
    "201": ("Tabungan Nasabah", "K"),
    "301": ("Modal Disetor", "K"),
}
JENIS = {
    "saldo_awal": "Saldo Awal",
    "setor": "Setor Tunai",
    "tarik": "Tarik Tunai",
    "transfer": "Transfer",
    "buka": "Buka Rekening",
    "tutup": "Tutup Rekening",
}
JENIS_KEY = {"Setor Tunai": "setor", "Tarik Tunai": "tarik", "Transfer": "transfer"}
MIN_TRANSAKSI = 10_000
MIN_SETORAN_AWAL = 50_000

st.set_page_config(
    page_title=NAMA_APP,
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
.block-container{padding-top:1.6rem;padding-bottom:3rem;max-width:1180px}
.hero{background:linear-gradient(135deg,#0B3C49 0%,#0E6B6B 55%,#2A9D8F 100%);
  color:#fff;border-radius:16px;padding:22px 26px;margin-bottom:16px}
.hero .tag{display:inline-block;font:600 11px/1 ui-monospace,Menlo,monospace;letter-spacing:.14em;
  padding:6px 10px;border:1px solid rgba(255,255,255,.45);border-radius:999px;margin-bottom:10px}
.hero .judul{font-size:clamp(1.5rem,4.5vw,2.2rem);font-weight:700;letter-spacing:-.01em;line-height:1.15;color:#fff}
.hero .sub{margin-top:6px;opacity:.9;font-size:.92rem;color:#fff}
[data-testid="stMetric"]{background:rgba(127,127,127,.08);border:1px solid rgba(127,127,127,.25);
  border-radius:12px;padding:14px 16px}
[data-testid="stMetricLabel"] p{font-size:.82rem;opacity:.85}
[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums;font-size:1.55rem}
.stTabs [data-baseweb="tab-list"]{gap:2px;overflow-x:auto}
.stTabs [data-baseweb="tab"]{padding:10px 14px;white-space:nowrap}
.stTabs [aria-selected="true"]{color:#2A9D8F}
.stTabs [data-baseweb="tab-highlight"]{background-color:#2A9D8F}
[data-testid="stFormSubmitButton"]>button,.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#0E6B6B,#2A9D8F);color:#fff;border:0;border-radius:10px;font-weight:600;min-height:44px}
[data-testid="stFormSubmitButton"]>button:hover,.stButton>button[kind="primary"]:hover{filter:brightness(1.08);color:#fff}
[data-testid="stForm"]{border:1px solid rgba(127,127,127,.28);border-radius:14px;padding:18px}
.pill{display:inline-block;font:600 11px/1 ui-monospace,Menlo,monospace;letter-spacing:.08em;
  padding:7px 10px;border-radius:999px;border:1px solid rgba(127,127,127,.35)}
.pill b{color:#2A9D8F}
.brand-side{font-weight:700;font-size:1.05rem;margin-bottom:4px}
.badge{display:inline-block;font:600 12px/1 ui-monospace,Menlo,monospace;letter-spacing:.06em;
  padding:6px 10px;border-radius:6px}
.badge.ok{background:rgba(46,160,100,.18);color:#2EA064}
.badge.no{background:rgba(220,80,70,.18);color:#DC5046}
.slip{position:relative;border:1px dashed rgba(127,127,127,.6);border-radius:8px;padding:20px 18px 14px;
  background:rgba(127,127,127,.06);font:13px/1.7 ui-monospace,Menlo,monospace;margin:10px 0}
.slip .jdl{font-weight:700;letter-spacing:.1em;font-size:12px;padding-right:90px;opacity:.85}
.slip .baris{display:flex;justify-content:space-between;gap:12px}
.slip .baris span:last-child{text-align:right}
.slip hr{border:0;border-top:1px dashed rgba(127,127,127,.5);margin:10px 0}
.slip .stempel{position:absolute;right:14px;top:12px;border:2px solid #DC5046;color:#DC5046;
  padding:2px 9px;border-radius:4px;font-weight:700;letter-spacing:.16em;transform:rotate(-8deg)}
.slip .total{font-weight:700;font-size:15px}
</style>
"""


# ---------------------------------------------------------------- util
def now():
    return datetime.now(WIB)


def angka(n):
    return f"{int(round(n)):,}".replace(",", ".")


def rp(n):
    return "Rp " + angka(n)


def esc(s):
    return html.escape(str(s if s is not None else ""))


def tampil_df(df, **kw):
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kw)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True, **kw)


def pastikan_pilihan(kunci, opsi):
    """Buang pilihan lama yang sudah tidak ada di daftar (misal rekening ditutup)."""
    if st.session_state.get(kunci) not in opsi:
        st.session_state.pop(kunci, None)


# ---------------------------------------------------------------- data
def init_state():
    s = st.session_state
    if "rekening" in s:
        return
    ts = now()
    s.rekening = {"123456": {"nama": "Budi Santoso", "status": "Aktif", "dibuka": ts}}
    s.transaksi = [
        {
            "no": 1, "waktu": ts, "jenis": "saldo_awal", "rek": "", "rek2": "",
            "jumlah": 0, "ket": "Saldo awal sistem",
            "lines": [
                {"akun": "101", "rek": "", "debit": 100_000_000, "kredit": 0},
                {"akun": "201", "rek": "123456", "debit": 0, "kredit": 5_000_000},
                {"akun": "301", "rek": "", "debit": 0, "kredit": 95_000_000},
            ],
        }
    ]
    s.slip = None
    s.slip_tab = ""
    s.t_jml = 50_000
    s.t_ket = ""
    s.t_err = ""
    s.c_nama = ""
    s.c_jml = 50_000
    s.c_err = ""
    s.x_ok = False
    s.x_err = ""
    s.x_msg = ""
    s.r_ok = False
    s.r_err = ""


def trx():
    return st.session_state.transaksi


def saldo_map():
    hasil = {}
    for t in trx():
        for l in t["lines"]:
            if l["akun"] == "201":
                hasil[l["rek"]] = hasil.get(l["rek"], 0) + l["kredit"] - l["debit"]
    return hasil


def total_akun():
    a = {k: {"d": 0, "k": 0} for k in AKUN}
    for t in trx():
        for l in t["lines"]:
            a[l["akun"]]["d"] += l["debit"]
            a[l["akun"]]["k"] += l["kredit"]
    return a


def kas():
    a = total_akun()["101"]
    return a["d"] - a["k"]


def simpanan():
    a = total_akun()["201"]
    return a["k"] - a["d"]


def rek_aktif():
    return [no for no, r in sorted(st.session_state.rekening.items()) if r["status"] == "Aktif"]


def label_rek(no):
    return f"{no} · {st.session_state.rekening[no]['nama']}"


def no_rek_berikut():
    angka_rek = [int(n) for n in st.session_state.rekening] or [123455]
    return str(max(max(angka_rek), 123456) + 1)


def no_trx(t):
    return f"TRX-{t['no']:04d}"


def fmt_waktu(ts):
    return ts.strftime("%d/%m/%Y %H:%M")


def catat(jenis, rek, rek2, jumlah, ket=""):
    if jenis in ("setor", "buka"):
        lines = [
            {"akun": "101", "rek": "", "debit": jumlah, "kredit": 0},
            {"akun": "201", "rek": rek, "debit": 0, "kredit": jumlah},
        ]
    elif jenis in ("tarik", "tutup"):
        lines = [
            {"akun": "201", "rek": rek, "debit": jumlah, "kredit": 0},
            {"akun": "101", "rek": "", "debit": 0, "kredit": jumlah},
        ]
    else:
        lines = [
            {"akun": "201", "rek": rek, "debit": jumlah, "kredit": 0},
            {"akun": "201", "rek": rek2, "debit": 0, "kredit": jumlah},
        ]
    t = {
        "no": len(trx()) + 1, "waktu": now(), "jenis": jenis, "rek": rek, "rek2": rek2,
        "jumlah": jumlah, "ket": ket, "lines": lines,
    }
    trx().append(t)
    return t


def validasi_teller(jenis, no, tujuan, jml):
    saldo = saldo_map()
    if not no:
        return "Pilih rekening terlebih dahulu."
    if jml < MIN_TRANSAKSI:
        return f"Jumlah minimal {rp(MIN_TRANSAKSI)}."
    if jenis in ("tarik", "transfer") and jml > saldo.get(no, 0):
        return f"Saldo tidak cukup. Saldo tersedia {rp(saldo.get(no, 0))}."
    if jenis == "tarik" and jml > kas():
        return f"Kas teller tidak cukup. Kas tersedia {rp(kas())}."
    if jenis == "transfer":
        if not tujuan:
            return "Pilih rekening tujuan."
        if tujuan == no:
            return "Rekening tujuan harus berbeda dari rekening sumber."
    return ""


# ---------------------------------------------------------------- callback aksi
def cb_teller():
    s = st.session_state
    jenis = JENIS_KEY[s.t_jenis]
    no = s.get("t_rek")
    tujuan = s.get("t_to") if jenis == "transfer" else ""
    jml = int(s.t_jml)
    err = validasi_teller(jenis, no, tujuan, jml)
    if err:
        s.t_err = err
        return
    s.slip = catat(jenis, no, tujuan, jml, (s.t_ket or "").strip())
    s.slip_tab = "teller"
    s.t_err = ""
    s.t_ket = ""
    s.t_jml = 50_000


def cb_buka():
    s = st.session_state
    nama = (s.c_nama or "").strip()
    jml = int(s.c_jml)
    if not nama:
        s.c_err = "Nama nasabah tidak boleh kosong."
        return
    if jml < MIN_SETORAN_AWAL:
        s.c_err = f"Setoran awal minimal {rp(MIN_SETORAN_AWAL)}."
        return
    no = no_rek_berikut()
    s.rekening[no] = {"nama": nama, "status": "Aktif", "dibuka": now()}
    s.slip = catat("buka", no, "", jml, "Setoran awal")
    s.slip_tab = "cs"
    s.c_err = ""
    s.c_nama = ""
    s.c_jml = 50_000


def cb_tutup():
    s = st.session_state
    s.x_msg = ""
    no = s.get("x_rek")
    if not no:
        return
    if not s.x_ok:
        s.x_err = "Centang kotak konfirmasi terlebih dahulu."
        return
    saldo = saldo_map().get(no, 0)
    if saldo > kas():
        s.x_err = "Kas teller tidak cukup untuk mengembalikan saldo nasabah."
        return
    if saldo > 0:
        s.slip = catat("tutup", no, "", saldo, "Penutupan rekening")
        s.slip_tab = "cs"
    s.rekening[no]["status"] = "Ditutup"
    s.x_err = ""
    s.x_ok = False
    s.x_msg = f"Rekening {no} berhasil ditutup."


def cb_reset():
    s = st.session_state
    if not s.r_ok:
        s.r_err = "Centang kotak konfirmasi terlebih dahulu."
        return
    for k in list(s.keys()):
        del s[k]
    # init_state() membuat ulang data awal pada putaran berikutnya
    s.r_msg = "Data berhasil dikembalikan ke kondisi awal."


# ---------------------------------------------------------------- komponen tampilan
def slip_html(t):
    baris = [
        ("Waktu", fmt_waktu(t["waktu"]) + " WIB"),
    ]
    nama = st.session_state.rekening
    if t["jenis"] == "transfer":
        baris.append(("Dari", f"{t['rek']} · {nama[t['rek']]['nama']}"))
        baris.append(("Ke", f"{t['rek2']} · {nama[t['rek2']]['nama']}"))
    else:
        baris.append(("Rekening", f"{t['rek']} · {nama[t['rek']]['nama']}"))
    if t["ket"] and t["jenis"] not in ("buka", "tutup"):
        baris.append(("Keterangan", t["ket"]))
    out = "".join(f'<div class="baris"><span>{esc(a)}</span><span>{esc(b)}</span></div>' for a, b in baris)
    out += f'<div class="baris total"><span>Jumlah</span><span>{esc(rp(t["jumlah"]))}</span></div>'
    out += (
        f'<div class="baris"><span>Saldo rekening kini</span>'
        f'<span>{esc(rp(saldo_map().get(t["rek"], 0)))}</span></div>'
    )
    out += '<hr><div style="opacity:.8;font-size:12px;letter-spacing:.06em">JURNAL OTOMATIS (D = DEBIT, K = KREDIT)</div>'
    for l in t["lines"]:
        k = l["kredit"] > 0
        nm = AKUN[l["akun"]][0]
        rek = f" ({l['rek']})" if l["rek"] else ""
        out += (
            f'<div class="baris"><span>{"&nbsp;&nbsp;K" if k else "D"} {l["akun"]} {esc(nm)}{esc(rek)}</span>'
            f'<span>{angka(l["kredit"] if k else l["debit"])}</span></div>'
        )
    return (
        f'<div class="slip"><span class="stempel">VALID</span>'
        f'<div class="jdl">BUKTI {esc(JENIS[t["jenis"]].upper())} · {no_trx(t)}</div>{out}</div>'
    )


def tampil_slip(tab):
    s = st.session_state
    if s.slip and s.slip_tab == tab:
        st.success("Transaksi berhasil dicatat dan jurnal otomatis sudah terbentuk.")
        st.markdown(slip_html(s.slip), unsafe_allow_html=True)


def badge_seimbang(ok, teks_ok="Seimbang", teks_no="Tidak seimbang"):
    kelas = "ok" if ok else "no"
    st.markdown(f'<span class="badge {kelas}">{teks_ok if ok else teks_no}</span>', unsafe_allow_html=True)


def df_jurnal(filter_jenis=None):
    baris = []
    for t in trx():
        if filter_jenis is not None and t["jenis"] not in filter_jenis:
            continue
        for l in t["lines"]:
            baris.append({
                "Waktu": fmt_waktu(t["waktu"]), "No": no_trx(t), "Jenis": JENIS[t["jenis"]],
                "Kode Akun": l["akun"], "Nama Akun": AKUN[l["akun"]][0], "Rek": l["rek"],
                "Debit": l["debit"], "Kredit": l["kredit"],
            })
    kolom = ["Waktu", "No", "Jenis", "Kode Akun", "Nama Akun", "Rek", "Debit", "Kredit"]
    return pd.DataFrame(baris, columns=kolom)


def rapikan(df, kolom_angka):
    v = df.copy()
    for c in kolom_angka:
        v[c] = v[c].map(lambda x: angka(x) if x else "")
    return v


def unduh(df, nama_file, label="⬇️ Unduh CSV"):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=nama_file, mime="text/csv")


# ---------------------------------------------------------------- tab-tab
def tab_dashboard():
    saldo = saldo_map()
    aktif = rek_aktif()
    hari_ini = [t for t in trx() if t["jenis"] != "saldo_awal" and t["waktu"].date() == now().date()]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kas Teller (101)", rp(kas()))
    c2.metric("Simpanan Nasabah (201)", rp(simpanan()))
    c3.metric("Rekening Aktif", len(aktif))
    c4.metric("Transaksi Hari Ini", len(hari_ini))

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("##### Saldo per rekening")
        if aktif:
            df = pd.DataFrame(
                {"Saldo": [saldo.get(n, 0) for n in aktif]},
                index=[label_rek(n) for n in aktif],
            )
            try:
                st.bar_chart(df, horizontal=True)
            except TypeError:
                st.bar_chart(df)
        else:
            st.info("Belum ada rekening aktif.")
    with g2:
        st.markdown("##### Pergerakan kas teller")
        titik, berjalan = [], 0
        for t in trx():
            ls = [l for l in t["lines"] if l["akun"] == "101"]
            if ls:
                berjalan += sum(l["debit"] - l["kredit"] for l in ls)
                titik.append({"Transaksi": no_trx(t), "Kas": berjalan})
        if len(titik) >= 2:
            st.line_chart(pd.DataFrame(titik).set_index("Transaksi"))
        else:
            st.info("Grafik muncul setelah ada transaksi tunai: setor, tarik, atau buka rekening.")

    st.markdown("##### Transaksi terakhir")
    terakhir = []
    for t in reversed(trx()[-8:]):
        if t["jenis"] == "transfer":
            ket = f"{t['rek']} → {t['rek2']}"
        elif t["jenis"] == "saldo_awal":
            ket = "Saldo awal sistem"
        else:
            ket = label_rek(t["rek"])
        terakhir.append({
            "Waktu": fmt_waktu(t["waktu"]), "No": no_trx(t), "Jenis": JENIS[t["jenis"]],
            "Keterangan": ket, "Jumlah": angka(t["jumlah"]) if t["jumlah"] else "",
        })
    tampil_df(pd.DataFrame(terakhir))


def tab_teller():
    st.markdown("#### 🏧 Transaksi Teller")
    aktif = rek_aktif()
    if not aktif:
        st.warning("Belum ada rekening aktif. Buka rekening di menu Customer Service.")
        return
    jenis_label = st.radio("Jenis transaksi", list(JENIS_KEY), horizontal=True, key="t_jenis")
    transfer = JENIS_KEY[jenis_label] == "transfer"
    kiri, kanan = st.columns([3, 2])
    with kiri:
        with st.form("form_teller"):
            pastikan_pilihan("t_rek", aktif)
            pastikan_pilihan("t_to", aktif)
            st.selectbox("Rekening sumber" if transfer else "Rekening nasabah", aktif, format_func=label_rek, key="t_rek")
            if transfer:
                st.selectbox("Rekening tujuan", aktif, format_func=label_rek, key="t_to")
            st.number_input("Jumlah (Rp)", min_value=MIN_TRANSAKSI, step=50_000, key="t_jml")
            st.text_input("Keterangan (opsional)", max_chars=60, key="t_ket")
            st.form_submit_button("Proses Transaksi", type="primary", on_click=cb_teller)
        if st.session_state.t_err:
            st.error(st.session_state.t_err)
    with kanan:
        st.markdown("##### Posisi saat ini")
        st.metric("Kas Teller", rp(kas()))
        saldo = saldo_map()
        tampil_df(pd.DataFrame({
            "No. Rek": aktif,
            "Nama": [st.session_state.rekening[n]["nama"] for n in aktif],
            "Saldo": [angka(saldo.get(n, 0)) for n in aktif],
        }))
        st.caption(
            "Jurnal otomatis: setor = debit 101, kredit 201. Tarik = debit 201, kredit 101. "
            "Transfer = debit 201 sumber, kredit 201 tujuan."
        )
    tampil_slip("teller")


def tab_cs():
    st.markdown("#### 🧑‍💼 Customer Service")
    t1, t2, t3 = st.tabs(["Buka Rekening", "Daftar Nasabah", "Tutup Rekening"])
    with t1:
        st.caption(f"Nomor rekening berikutnya: {no_rek_berikut()}")
        with st.form("form_buka"):
            st.text_input("Nama lengkap nasabah", max_chars=40, key="c_nama", placeholder="Contoh: Siti Rahma")
            st.number_input("Setoran awal (Rp)", min_value=MIN_SETORAN_AWAL, step=50_000, key="c_jml")
            st.form_submit_button("Buka Rekening", type="primary", on_click=cb_buka)
        if st.session_state.c_err:
            st.error(st.session_state.c_err)
    with t2:
        cari = st.text_input("Cari nama atau nomor rekening", key="c_cari")
        saldo = saldo_map()
        baris = []
        for no, r in sorted(st.session_state.rekening.items()):
            if cari and cari.lower() not in (no + " " + r["nama"]).lower():
                continue
            baris.append({
                "No. Rek": no, "Nama": r["nama"], "Dibuka": fmt_waktu(r["dibuka"]),
                "Status": r["status"], "Saldo": angka(saldo.get(no, 0)),
            })
        if baris:
            tampil_df(pd.DataFrame(baris))
        else:
            st.info("Tidak ada nasabah yang cocok.")
    with t3:
        aktif = rek_aktif()
        if not aktif:
            st.info("Tidak ada rekening aktif untuk ditutup.")
        else:
            pastikan_pilihan("x_rek", aktif)
            st.selectbox("Pilih rekening yang ditutup", aktif, format_func=label_rek, key="x_rek")
            st.caption("Saldo rekening akan dikembalikan tunai ke nasabah dan tercatat di jurnal.")
            st.checkbox("Saya yakin menutup rekening ini", key="x_ok")
            st.button("Tutup Rekening", on_click=cb_tutup)
        if st.session_state.x_err:
            st.error(st.session_state.x_err)
        if st.session_state.x_msg:
            st.success(st.session_state.x_msg)
    tampil_slip("cs")


def tab_mutasi():
    st.markdown("#### 📒 Mutasi Rekening (Rekening Koran)")
    semua = sorted(st.session_state.rekening)
    no = st.selectbox("Pilih rekening", semua, format_func=label_rek, key="m_rek")
    if not no:
        return
    r = st.session_state.rekening[no]
    saldo = saldo_map().get(no, 0)
    a, b, c = st.columns(3)
    a.metric("Nama", r["nama"])
    b.metric("Status", r["status"])
    c.metric("Saldo", rp(saldo))
    baris, berjalan = [], 0
    for t in trx():
        for l in t["lines"]:
            if l["akun"] == "201" and l["rek"] == no:
                berjalan += l["kredit"] - l["debit"]
                if t["jenis"] == "transfer":
                    ket = f"Transfer ke {t['rek2']}" if l["debit"] else f"Transfer dari {t['rek']}"
                else:
                    ket = JENIS[t["jenis"]]
                if t["ket"] and t["jenis"] not in ("buka", "tutup", "saldo_awal"):
                    ket += f" · {t['ket']}"
                baris.append({
                    "Waktu": fmt_waktu(t["waktu"]), "No": no_trx(t), "Keterangan": ket,
                    "Debit": l["debit"], "Kredit": l["kredit"], "Saldo": berjalan,
                })
    df = pd.DataFrame(baris, columns=["Waktu", "No", "Keterangan", "Debit", "Kredit", "Saldo"])
    tampil_df(rapikan(df, ["Debit", "Kredit", "Saldo"]))
    unduh(df, f"mutasi_{no}.csv")


def tab_jurnal():
    st.markdown("#### 📜 Jurnal Umum")
    semua = list(JENIS.values())
    pilih = st.multiselect("Filter jenis transaksi", semua, default=semua, key="j_filter")
    kunci = [k for k, v in JENIS.items() if v in pilih]
    df = df_jurnal(kunci)
    tampil = rapikan(df, ["Debit", "Kredit"])
    tampil["Waktu"] = tampil["Waktu"].where(df["No"] != df["No"].shift(), "")
    tampil["Jenis"] = tampil["Jenis"].where(df["No"] != df["No"].shift(), "")
    tampil["No"] = tampil["No"].where(df["No"] != df["No"].shift(), "")
    tampil_df(tampil)
    td, tk = int(df["Debit"].sum()), int(df["Kredit"].sum())
    a, b, c = st.columns(3)
    a.metric("Total Debit", rp(td))
    b.metric("Total Kredit", rp(tk))
    with c:
        st.write("")
        badge_seimbang(td == tk)
    unduh(df, "jurnal_umum.csv")


def tab_buku_besar():
    st.markdown("#### 📚 Buku Besar")
    kode = st.selectbox("Pilih akun", list(AKUN), format_func=lambda k: f"{k} · {AKUN[k][0]}", key="b_akun")
    normal = AKUN[kode][1]
    baris, berjalan = [], 0
    for t in trx():
        for l in t["lines"]:
            if l["akun"] == kode:
                berjalan += (l["debit"] - l["kredit"]) if normal == "D" else (l["kredit"] - l["debit"])
                baris.append({
                    "Waktu": fmt_waktu(t["waktu"]), "No": no_trx(t), "Jenis": JENIS[t["jenis"]],
                    "Rek": l["rek"], "Debit": l["debit"], "Kredit": l["kredit"], "Saldo": berjalan,
                })
    df = pd.DataFrame(baris, columns=["Waktu", "No", "Jenis", "Rek", "Debit", "Kredit", "Saldo"])
    st.metric(f"Saldo akhir akun {kode} ({'debit' if normal == 'D' else 'kredit'})", rp(berjalan))
    tampil_df(rapikan(df, ["Debit", "Kredit", "Saldo"]))
    unduh(df, f"buku_besar_{kode}.csv")


def tab_neraca():
    st.markdown("#### ⚖️ Neraca Saldo")
    a = total_akun()
    baris, sd, sk, md, mk = [], 0, 0, 0, 0
    for k in AKUN:
        net = a[k]["d"] - a[k]["k"]
        cd, ck = (net, 0) if net >= 0 else (0, -net)
        sd += cd
        sk += ck
        md += a[k]["d"]
        mk += a[k]["k"]
        baris.append({
            "Kode": k, "Nama Akun": AKUN[k][0], "Mutasi Debit": angka(a[k]["d"]),
            "Mutasi Kredit": angka(a[k]["k"]), "Saldo Debit": angka(cd) if cd else "",
            "Saldo Kredit": angka(ck) if ck else "",
        })
    baris.append({
        "Kode": "", "Nama Akun": "JUMLAH", "Mutasi Debit": angka(md), "Mutasi Kredit": angka(mk),
        "Saldo Debit": angka(sd), "Saldo Kredit": angka(sk),
    })
    tampil_df(pd.DataFrame(baris))
    badge_seimbang(sd == sk)
    st.caption("Dihitung otomatis dari seluruh jurnal.")

    st.markdown("##### Rincian akun 201 per rekening")
    saldo = saldo_map()
    rinci = [
        {"No. Rek": no, "Nama": r["nama"], "Saldo": angka(saldo.get(no, 0))}
        for no, r in sorted(st.session_state.rekening.items())
        if r["status"] == "Aktif" or saldo.get(no, 0) != 0
    ]
    jumlah = sum(saldo.get(no, 0) for no in st.session_state.rekening)
    rinci.append({"No. Rek": "", "Nama": "JUMLAH", "Saldo": angka(jumlah)})
    tampil_df(pd.DataFrame(rinci))
    badge_seimbang(jumlah == simpanan(), "Cocok dengan akun 201", "Selisih dengan akun 201")


def tab_laporan():
    st.markdown("#### 📅 Laporan Harian")
    tgl = st.date_input("Tanggal laporan", value=now().date(), key="l_tgl")
    harian = [t for t in trx() if t["jenis"] != "saldo_awal" and t["waktu"].date() == tgl]
    masuk = sum(t["jumlah"] for t in harian if t["jenis"] in ("setor", "buka"))
    keluar = sum(t["jumlah"] for t in harian if t["jenis"] in ("tarik", "tutup"))
    kas_akhir = 0
    for t in trx():
        if t["waktu"].date() <= tgl:
            kas_akhir += sum(l["debit"] - l["kredit"] for l in t["lines"] if l["akun"] == "101")
    a, b, c, d = st.columns(4)
    a.metric("Jumlah Transaksi", len(harian))
    b.metric("Uang Masuk", rp(masuk))
    c.metric("Uang Keluar", rp(keluar))
    d.metric("Kas Akhir Hari", rp(kas_akhir))
    if not harian:
        st.info("Belum ada transaksi pada tanggal ini.")
        return
    rekap = []
    for k in ("setor", "tarik", "transfer", "buka", "tutup"):
        ts = [t for t in harian if t["jenis"] == k]
        if ts:
            rekap.append({"Jenis": JENIS[k], "Jumlah Transaksi": len(ts), "Total Nominal": sum(t["jumlah"] for t in ts)})
    df = pd.DataFrame(rekap)
    st.markdown("##### Rekap per jenis")
    tampil_df(rapikan(df, ["Total Nominal"]))
    st.bar_chart(df.set_index("Jenis")["Total Nominal"])
    rinci = pd.DataFrame([
        {"Waktu": fmt_waktu(t["waktu"]), "No": no_trx(t), "Jenis": JENIS[t["jenis"]], "Rek": t["rek"],
         "Rek Tujuan": t["rek2"], "Jumlah": t["jumlah"], "Keterangan": t["ket"]}
        for t in harian
    ])
    unduh(rinci, f"laporan_{tgl.isoformat()}.csv")


def tab_pengaturan():
    st.markdown("#### ⚙️ Pengaturan")
    st.markdown("##### Tentang aplikasi")
    st.write(
        f"**{NAMA_APP}** adalah simulasi Core Banking System untuk lab perbankan kampus, berbasis "
        "SEOJK No. 34/SEOJK.03/2021 (BPAK). Setiap transaksi otomatis menjadi jurnal debit dan kredit, "
        "lalu mengalir ke buku besar dan neraca saldo."
    )
    with st.expander("Alur kerja yang disarankan"):
        st.markdown(
            "1. **Customer Service**: buka rekening nasabah dengan setoran awal.\n"
            "2. **Teller**: setor tunai, tarik tunai, atau transfer antar rekening.\n"
            "3. **Mutasi Rekening**: lihat rekening koran per nasabah.\n"
            "4. **Jurnal Umum**, **Buku Besar**, **Neraca Saldo**: periksa pencatatan dan keseimbangannya.\n"
            "5. **Laporan Harian**: rekap transaksi per tanggal, bisa diunduh sebagai CSV."
        )
    st.markdown("##### Atur ulang data")
    st.caption("Mengembalikan semua data ke kondisi awal: kas Rp 100.000.000 dan satu rekening contoh.")
    st.checkbox("Saya yakin ingin mengatur ulang semua data", key="r_ok")
    st.button("Atur Ulang Data", on_click=cb_reset)
    if st.session_state.get("r_err"):
        st.error(st.session_state.r_err)
    if st.session_state.get("r_msg"):
        st.success(st.session_state.r_msg)
    st.caption("Data disimpan di sesi browser, jadi juga kembali ke awal saat halaman dimuat ulang.")


# ---------------------------------------------------------------- halaman
def main():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f'<div class="brand-side">🏦 {esc(NAMA_APP)}</div>', unsafe_allow_html=True)
        st.markdown('<span class="pill"><b>●</b> ONLINE · REAL-TIME BATCH</span>', unsafe_allow_html=True)
        st.write("")
        st.metric("Kas Teller", rp(kas()))
        st.metric("Rekening Aktif", len(rek_aktif()))
        st.caption("Data bersifat simulasi.")

    st.markdown(
        f"""<div class="hero"><div class="tag">LAB PERBANKAN KAMPUS</div>
        <div class="judul">Core Banking System (CBS)</div>
        <div class="sub">Lab Perbankan Kampus · berbasis SEOJK No. 34/SEOJK.03/2021 (BPAK)</div></div>""",
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "📊 Dashboard", "🏧 Teller", "🧑‍💼 Customer Service", "📒 Mutasi", "📜 Jurnal Umum",
        "📚 Buku Besar", "⚖️ Neraca Saldo", "📅 Laporan", "⚙️ Pengaturan",
    ])
    fungsi = [
        tab_dashboard, tab_teller, tab_cs, tab_mutasi, tab_jurnal,
        tab_buku_besar, tab_neraca, tab_laporan, tab_pengaturan,
    ]
    for tab, fn in zip(tabs, fungsi):
        with tab:
            fn()


if __name__ == "__main__":
    main()
