import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Personel Verimlilik Analizi", layout="centered")
st.title("🏨 Personel Performans Analizi")

# Dosya yükleme
uploaded_file = st.file_uploader("Veri dosyasını yükleyin (CSV veya Excel)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df["Tarih"] = pd.to_datetime(df["Tarih"])
        st.success(f"Veri başarıyla yüklendi. Toplam kayıt: {len(df)}")

        # Ay isimleri 
        ay_adlari = {
            "Tüm yıl": "Tüm yıl",
            "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6,
            "Temmuz": 7, "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12
        }

        # Süre hesaplama (dakika)
        df["Giriş Saati"] = pd.to_datetime(df["Giriş Saati"], format="%H:%M")
        df["Çıkış Saati"] = pd.to_datetime(df["Çıkış Saati"], format="%H:%M")
        df["gercek_sure_dk"] = (df["Çıkış Saati"] - df["Giriş Saati"]).dt.total_seconds() / 60

        # Ortalama temizlik sürelerini hesapla (müşteri talebi hariç)
        ort_sure_df = df[
            (df["gercek_sure_dk"] > 0) &
            (df["Temizlik Türü"].isin(["Rutin", "Detaylı"]))
        ].groupby(["Temizlik Türü", "Oda Tipi"])["gercek_sure_dk"].mean()

        # Beklenen süreleri atama
        def veri_tabanli_beklenen_sure(row):
            return ort_sure_df.get((row["Temizlik Türü"], row["Oda Tipi"]), 0)

        df["beklenen_sure_dk"] = df.apply(veri_tabanli_beklenen_sure, axis=1)

        # Giriş alanları
        col1, col2 = st.columns(2)
        with col1:
            personel_id = st.text_input("Personel ID", max_chars=4).strip().upper()
        with col2:
            ay_secimi_gorunen = st.selectbox("Ay Seçimi", list(ay_adlari.keys()))
            ay_secimi = ay_adlari[ay_secimi_gorunen]

        if personel_id:
            df_personel = df[
                (df["Personel ID"] == personel_id) &
                (df["Temizlik Türü"].isin(["Rutin", "Detaylı"]))
            ]
            if ay_secimi != "Tüm yıl":
                df_personel = df_personel[df_personel["Tarih"].dt.month == int(ay_secimi)]

            df_personel = df_personel[df_personel["gercek_sure_dk"] > 0]

            if not df_personel.empty:
                # Kat bilgisi (ilk oda numarasından alınır)
                oda_numarasi = int(df_personel.iloc[0]["Oda Numarası"])
                kat = oda_numarasi // 100

                # Toplam oda sayısı
                toplam_oda = len(df_personel)

                # Çalıştığı gün sayısı
                toplam_gun = df_personel["Tarih"].dt.date.nunique()

                # Hız hesapla
                df_personel["hiz_skoru"] = (df_personel["beklenen_sure_dk"] / df_personel["gercek_sure_dk"]) * 100
                df_personel["hiz_skoru"] = df_personel["hiz_skoru"].clip(upper=200)

                hiz_ortalama = df_personel["hiz_skoru"].mean()

                # Yoğunluk skoru hesapla (kırpma: alt %35, üst %5)
                df_aktif = df[(df["Temizlik Türü"].isin(["Rutin", "Detaylı"]))]
                if ay_secimi != "Tüm yıl":
                    df_aktif = df_aktif[df_aktif["Tarih"].dt.month == int(ay_secimi)]

                oda_sayilari = df_aktif.groupby("Personel ID").size().sort_values()  # Artan sıralama
                n = len(oda_sayilari)
                alt_kes = int(n * 0.35)
                ust_kes = int(n * 0.95)
                kırpılmış = oda_sayilari.iloc[alt_kes:ust_kes]
                referans_ortalama = kırpılmış.mean() if not kırpılmış.empty else 1
                yogunluk_skoru = (toplam_oda / referans_ortalama) * 100

                # Verimlilik skoru (yoğunluğa daha fazla ağırlık verildi)
                verimlilik_skoru = (hiz_ortalama * 0.3) + (yogunluk_skoru * 0.7)

                renk = "#d9534f" if verimlilik_skoru < 40 else "#f0ad4e" if verimlilik_skoru < 80 else "#5cb85c"

                # Bilgileri göster
                st.markdown(f"**👤 Personel ID:** {personel_id}")
                st.markdown(f"**📍 Çalıştığı Kat:** {kat}. kat")
                st.markdown(f"**🧹 Toplam Temizlenen Oda:** {toplam_oda}")
                st.markdown(f"**📅 Çalıştığı Gün Sayısı:** {toplam_gun}")
                st.markdown(f"**⚡ Hız Skoru:** {hiz_ortalama:.1f}%")
                st.markdown(f"**📦 Yoğunluk Skoru:** {yogunluk_skoru:.1f}%")
                st.markdown(f"**📊 Genel Verimlilik Skoru:** {verimlilik_skoru:.1f}%")

                # Verimlilik çubuğu
                bar_html = f"""
                <div style='background-color: #eee; border-radius: 8px; height: 28px; width: 100%; margin-top: 8px;'>
                    <div style='background-color: {renk}; width: {min(verimlilik_skoru, 100)}%; height: 100%; 
                                border-radius: 8px; text-align: center; color: white; font-weight: bold; 
                                line-height: 28px;'>
                        {verimlilik_skoru:.0f}%
                    </div>
                </div>
                """
                st.markdown(bar_html, unsafe_allow_html=True)

            else:
                st.warning("Bu ID ve ay seçimi için geçerli veri bulunamadı.")
    except Exception as e:
        st.error(f"Veri yüklenirken hata oluştu: {e}")
