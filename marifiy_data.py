# marifiy_data.py

# --- ALLOHNING 99 ISMI ---
ALL_NAMES = [
    ("Ar-Rahman", "Rahmli", "Allohning cheksiz rahm-shafqati va marhamati barcha yaratilganlarga, mo'minu kofirga ham qamrab oladi."),
    ("Ar-Rahim", "Mehribon", "Allohning mo'minlarga bo'lgan alohida rahmati va ularni jannat bilan mukofotlashi."),
    ("Al-Malik", "Podsho", "Alloh butun olamning yagona egasi va hukmdori, U hech kimga hisob bermaydi."),
    ("Al-Quddus", "Muqaddas", "Alloh har qanday kamchilik, nuqson va ayblardan pok va mukammaldir."),
    ("As-Salam", "Tinchlik", "Alloh tinchlik manbai, bandalarini xatar va halokatdan xalos qiluvchidir."),
    ("Al-Mu'min", "Ishonch beruvchi", "Alloh bandalariga xavfsizlik, omonlik va ishonch beruvchi zotdir."),
    ("Al-Muhaymin", "Nazorat qiluvchi", "Alloh barcha narsani kuzatib turadi, ularni himoya qiladi va boshqaradi."),
    ("Al-Aziz", "Qudratli", "Alloh cheksiz qudrat egasi, hech kim Unga g'olib kela olmaydi va Unga zarar yetkaza olmaydi."),
    ("Al-Jabbar", "Kuchli", "Alloh o'z irodasi bilan hamma narsani o'zgartira oladi, siniklarni tuzatuvchidir."),
    ("Al-Mutakabbir", "Ulug'", "Alloh barcha ulug'lik va buyuklikning egasidir, takabburlik faqat Unga xosdir."),
    ("Al-Khaliq", "Yaratuvchi", "Alloh barcha mavjudotni yo'qdan yaratgan va taqdirlarni belgilagan."),
    ("Al-Bari'", "Ijodkor", "Alloh har bir narsani o'ziga xos, tengsiz va uyg'un shaklda ijod qilgan."),
    ("Al-Musawwir", "Shakl beruvchi", "Alloh yaratilganlarga chiroyli, mos va mukammal shakl bergan."),
    ("Al-Ghaffar", "Kechiruvchi", "Alloh bandalarining gunohlarini ko'p marta va cheksiz kechiradigan zotdir."),
    ("Al-Qahhar", "G'olib", "Alloh barcha narsadan ustun, Uning qudrati va g'azabi hamma narsani qamrab olgan."),
    ("Al-Wahhab", "Sovg'a beruvchi", "Alloh bandalariga qaytarib berilmaydigan bebaho ne'matlar, in'om va sovg'alar beradi."),
    ("Ar-Razzaq", "Rizq beruvchi", "Alloh barcha jonzotlarga rizq, ozuqa, mol-dunyo va ma'naviy ozuqani yetkazib beruvchidir."),
    ("Al-Fattah", "Ochib beruvchi", "Alloh barcha yopiq eshiklarni ochadi, qiyinchiliklarni hal qiladi va zafarlar beradi."),
    ("Al-Alim", "Biluvchi", "Alloh hamma narsani, o'tmish va kelajakni, yashirin va oshkorni to'liq biladi."),
    ("Al-Qabid", "Ushatuvchi", "Alloh o'z hikmati bilan rizqni, qalblarni va ruhlarni ushlab turadi, toraytiradi."),
    ("Al-Basit", "Kengaytiruvchi", "Alloh xohlagan narsasini, rizqni va qalblarni kengaytiradi, ochadi."),
    ("Al-Khafid", "Tushiruvchi", "Alloh zolimlarni, takabbur va mutakabbir kishilarni xor qilib pastga tushiradi."),
    ("Ar-Rafi'", "Ko'taruvchi", "Alloh solih bandalarini, mo'minlarni va ilmlilarni darajalarini yuksakka ko'taradi."),
    ("Al-Mu'izz", "Izzat beruvchi", "Alloh xohlagan bandasiga izzat, obro', sharaf va yuksak mavqe beradi."),
    ("Al-Muzill", "Xor qiluvchi", "Alloh zulm va kibr qiluvchilarni xor qiladi va pastga tushiradi."),
    ("As-Sami'", "Eshituvchi", "Alloh barcha tovushlarni, hatto eng yashirin pichirlashlarni va qalb nidolarini ham eshitadi."),
    ("Al-Basir", "Ko'ruvchi", "Alloh hamma narsani, hatto zulmatdagi qora chumolini va zarrachani ham ko'radi."),
    ("Al-Hakam", "Hukm qiluvchi", "Alloh barcha narsa ustidan adolatli va to'g'ri hukm chiqaruvchi mutlaq hukmdordir."),
    ("Al-Adl", "Adolatli", "Alloh cheksiz adolat egasi, U hech qachon zarracha zulm qilmaydi va adolat o'rnatadi."),
    ("Al-Latif", "Latif", "Alloh bandalariga yumshoq muomala qiladi, ularga sezilmagan holda va yashirincha yordam beradi."),
    ("Al-Khabir", "Xabardor", "Alloh barcha narsadan, hatto qalblardagi niyatlardan ham to'liq xabardor."),
    ("Al-Halim", "Halim", "Alloh juda sabrli, bandalarining isyoniga qaramay, ularni jazolashga shoshilmaydi."),
    ("Al-Azim", "Ulug'", "Alloh cheksiz ulug'lik, buyuklik va azamat egasi bo'lib, aql-idrok Undan ojizdir."),
    ("Al-Ghafur", "Kechiruvchi", "Alloh bandalarining katta gunohlarini ham kechiradi va ularni afv etadi."),
    ("Ash-Shakur", "Qadrlovchi", "Alloh bandalarining kichik yaxshiliklariga ham katta savob va mukofot beradi."),
    ("Al-Aliy", "Yuksak", "Alloh barcha narsadan yuksak, baland va O'z zotida ulug'dir."),
    ("Al-Kabir", "Buyuk", "Alloh barcha narsadan buyuk va ulug'dir, Uning kattaligi cheksizdir."),
    ("Al-Hafiz", "Himoyachi", "Alloh barcha narsani saqlaydi, asraydi va bandalarini turli ofatlardan himoya qiladi."),
    ("Al-Muqit", "Rizq beruvchi", "Alloh barcha jonzotlarga ozuqa, kuch-quvvat va yashash uchun zarur rizq beradi."),
    ("Al-Hasib", "Hisob-kitob qiluvchi", "Alloh bandalarining amallarini hisoblaydi, qiyomatda adolatli hisob-kitob qiladi va yetarli bo'ladi."),
    ("Al-Jalil", "Jaloliy", "Alloh cheksiz ulug'lik, buyuklik, azamat va jaloliyat egasidir."),
    ("Al-Karim", "Karim", "Alloh juda saxiy, qo'li ochiq, ko'p ne'mat beruvchi va berganini qaytarib olmaydigan zotdir."),
    ("Ar-Raqib", "Kuzatuvchi", "Alloh barcha narsani, bandalarning amallarini doimiy kuzatib turadi, hech narsa Undan yashirin emas."),
    ("Al-Mujib", "Javob beruvchi", "Alloh bandalarining duolariga, iltijolariga, yaxshi so'zlariga va so'rovlariga ijobat qiladi."),
    ("Al-Wasi'", "Keng", "Allohning ilmi, rahmati, mag'firati va qudrati cheksiz kengdir, hamma narsani qamrab oladi."),
    ("Al-Hakim", "Hikmatli", "Alloh barcha ishlarni eng yaxshi hikmat, donolik va to'g'ri hukm bilan qiladi."),
    ("Al-Wadud", "Sevuvchi", "Alloh solih va taqvodor bandalarini yaxshi ko'radi va ularga sevgi beradi."),
    ("Al-Majid", "Ulug'", "Alloh ulug'lik, sharaf va shon-shuhrat egasidir, Uning ezguligi cheksizdir."),
    ("Al-Ba'ith", "Tiriltiruvchi", "Alloh qiyomat kuni o'liklarni qabrlardan tiriltirib, hisob-kitob uchun to'playdi."),
    ("Ash-Shahid", "Guvoh", "Alloh barcha narsaga guvohdir, U hamma narsani ko'radi va biladi, hech narsa Undan yashirin emas."),
    ("Al-Haqq", "Haq", "Allohning mavjudligi va ilohligi mutlaq haqiqatdir, Undan boshqa narsa yo'q."),
    ("Al-Wakil", "Ishonchli", "Alloh bandalarining ishlarini o'z zimmasiga oladi, tavakkal qiluvchilarga yetarli bo'ladi."),
    ("Al-Qawiy", "Kuchli", "Alloh cheksiz kuch va qudrat egasi, hech qanday narsa Uni ojiz qila olmaydi."),
    ("Al-Matin", "Mustahkam", "Alloh o'z ishlarida, hukmlarida va qudratida juda mustahkam va kuchlidir."),
    ("Al-Waliy", "Yaqin", "Alloh mo'minlarga yaqin, ularni qo'llab-quvvatlaydi va yordam beruvchi do'stdir."),
    ("Al-Hamid", "Maqtovli", "Alloh barcha maqtov va hamdlarga loyiqdir, har qanday shukr Unga xosdir."),
    ("Al-Muhsiy", "Hisoblovchi", "Alloh barcha narsani, vaqtni, amallarni va zotlarni birma-bir hisoblab chiqqan va biladi."),
    ("Al-Mubdi'", "Boshlovchi", "Alloh barcha narsani yo'qdan yaratib, unga boshlang'ich nuqta qo'ygan zotdir."),
    ("Al-Mu'id", "Qaytaruvchi", "Alloh vafot etgan mavjudotlarni yana hayotga qaytaradi va avvalgi holiga keltiradi."),
    ("Al-Muhyi", "Hayot beruvchi", "Alloh xohlagan narsasiga, jonsiz narsalarga ham hayot beradi va tiriltiradi."),
    ("Al-Mumit", "O'ldiruvchi", "Alloh xohlagan mavjudotini o'ldirib, uning hayotini tugatadi va o'limni yaratuvchidir."),
    ("Al-Hayy", "Tirik", "Alloh abadiy tirikdir, hech qachon o'lmaydi, Uning hayoti cheksizdir."),
    ("Al-Qayyum", "Qo'llab-quvvatlovchi", "Alloh barcha mavjudotlarni o'z holida saqlaydi, ularni boshqaradi va hech kimga muhtoj emas."),
    ("Al-Wajid", "Topuvchi", "Alloh xohlagan narsasini topadi, hech qanday narsa Undan yashirin qolmaydi."),
    ("Al-Majid", "Ulug'", "Alloh ulug'lik va sharaf egasi bo'lib, Uning zikri va yo'li ulug'dir."),
    ("Al-Wahid", "Yagona", "Alloh O'z zotida, sifatlarida va ishlarida yagonadir, Uning sherigi yo'q."),
    ("Al-Ahad", "Birlik", "Alloh birlik va yagonalik egasi bo'lib, bo'linmaydi va hech kimga o'xshamaydi."),
    ("As-Samad", "Mustaqil", "Alloh hech kimga muhtoj emas, balki barcha mavjudot Unga muhtojdir."),
    ("Al-Qadir", "Qodir", "Alloh barcha narsaga qodir va kuchlidir, Uning qudrati cheksizdir."),
    ("Al-Muqtadir", "Quvvatli", "Alloh cheksiz kuch va qudrat egasi bo'lib, hamma narsani O'z irodasiga bo'ysundiradi."),
    ("Al-Muqaddim", "Oldinga o'tkazuvchi", "Alloh xohlagan narsasini, insonlarni va amallarni o'z hikmati bilan oldinga o'tkazadi."),
    ("Al-Mu'akhkhir", "Kechiktiruvchi", "Alloh xohlagan narsasini, jazolarni va taqdirlarni o'z hikmati bilan kechiktiradi."),
    ("Al-Awwal", "Birinchi", "Alloh barcha narsadan oldin mavjud bo'lgan, boshlanishi yo'q zotdir."),
    ("Al-Akhir", "Oxirgi", "Alloh barcha narsa yo'q bo'lgandan keyin ham mavjud bo'lib qoladigan, tugashi yo'q zotdir."),
    ("Az-Zahir", "Oshkor", "Alloh o'zining qudrati, yaratishidagi mo''jizalar va dalillari bilan oshkordir."),
    ("Al-Batin", "Yashirin", "Allohning zoti, sirlari va hikmatlari inson aql-idrokidan yashirin va pinhondir."),
    ("Al-Waliy", "Boshqaruvchi", "Alloh barcha narsani boshqaradi, olamlarning ishini idora qiluvchidir."),
    ("Al-Muta'aliy", "Yuksak", "Alloh barcha narsadan yuksak, kamchiliklardan pok va balanddir."),
    ("Al-Barr", "Yaxshilik qiluvchi", "Alloh bandalariga yaxshilik qiladi, ularga rahm qiladi va yaxshilarni sevadi."),
    ("At-Tawwab", "Tavbani qabul qiluvchi", "Alloh bandalarining gunohlaridan tavba qilishlarini qabul qiladi va ularni kechiradi."),
    ("Al-Muntaqim", "Adolatli jazolovchi", "Alloh zolimlarni, gunohkorlarni va azob beruvchilarni adolat bilan jazolaydi."),
    ("Al-Afuww", "Kechiruvchi", "Alloh bandalarining gunohlarini kechiradi, ularni o'chiradi va afv etadi."),
    ("Ar-Ra'uf", "Mehribon", "Alloh bandalariga juda mehribon va rahmdildir, ularning azoblanishini xohlamaydi."),
    ("Malik-ul-Mulk", "Mulk egasi", "Alloh butun olamning, mulk va saltanatning yagona egasi va hukmdoridir."),
    ("Zul-Jalali-wal-Ikram", "Ulug'lik egasi", "Alloh ulug'lik, azamat va sharaf egasi bo'lib, U zotga hamdu sanolar bo'lsin."),
    ("Al-Muqsit", "Adolatli", "Alloh adolatli hukm qiluvchi va zulm qiluvchilardan adolatni talab qiluvchidir."),
    ("Al-Jami'", "To'plovchi", "Alloh barcha narsani, insonlarni va qiyomat kunini bir joyga to'playdi."),
    ("Al-Ghaniy", "Boy", "Alloh hech kimga muhtoj emas, balki barcha mavjudot Unga muhtojdir."),
    ("Al-Mughniy", "Boyitadigan", "Alloh xohlagan bandasini boyitadi, unga yetarli ne'mat va rizq beradi."),
    ("Al-Mani'", "To'sqinlik qiluvchi", "Alloh yomonliklardan va zararlardan saqlaydi, to'sqinlik qiladi va himoya qiladi."),
    ("Ad-Darr", "Zarar yetkazuvchi", "Alloh o'z hikmati bilan xohlagan narsasiga zarar yetkazadi va sinovlar yuboradi."),
    ("An-Nafi'", "Foyda beruvchi", "Alloh xohlagan narsasiga foyda beradi va bandalariga yaxshilik yetkazadi."),
    ("An-Nur", "Nur", "Alloh barcha narsani yorituvchi nurdir, U zulmatlarni yoritadi va hidoyat beradi."),
    ("Al-Hadiy", "Yo'l ko'rsatuvchi", "Alloh bandalarini to'g'ri yo'lga hidoyat qiladi va yaxshilikka yo'naltiradi."),
    ("Al-Badi'", "Misli yo'q yaratuvchi", "Alloh barcha narsani mislsiz, tengsiz va hech qanday namunasiz yaratgan zotdir."),
    ("Al-Baqiy", "Abadiy", "Alloh abadiy qoladi, hech qachon yo'q bo'lmaydi, Uning zoti va mavjudligi doimiydir."),
    ("Al-Warith", "Meros oluvchi", "Alloh barcha narsaning oxirgi egasi va merosxo'ridir, hamma narsa Unga qaytadi."),
    ("Ar-Rashid", "To'g'ri yo'l ko'rsatuvchi", "Alloh bandalarini to'g'ri yo'lga yo'naltiradi, hikmatli va donodir."),
    ("As-Sabur", "Sabrli", "Alloh juda sabrlidir, bandalarining gunohlariga qaramay ularni jazolashga shoshilmaydi.")
]

# --- TAHORAT OLISH ---
TAHORAT_TEXT = """**💧 Tahorat qilish tartibi:**

1. Qalbda niyat qilish va "Bismillah" deyish.
2. Qo'llarni bilakgacha 3 marta yuvish.
3. Og'izni 3 marta chayish.
4. Burunni 3 marta yuvish.
5. Yuzni 3 marta yuvish.
6. O'ng qo'lni tirsakkacha, so'ng chap qo'lni 3 martadan yuvish.
7. Boshni bir marta masq qilish (ho'l qo'l bilan).
8. Quloqlarni bir marta masq qilish.
9. O'ng oyoqni to'piqgacha, so'ng chap oyoqni 3 martadan yuvish."""

# --- RAMAZON REJIMI ---
RAMAZON_TEXT = """**🌙 Ramazon oyi haqida:**

Ramazon — Hijriy taqvim bo'yicha to'qqizinchi oy bo'lib, Islomning besh ruknidan biri hisoblangan ro'za tutish oyi. Bu oyda Qur'on nozil bo'la boshlagan. Ramazon oyida tongdan quyosh botgunga qadar yeb-ichishdan va jinsiy aloqadan tiyilish farzdir. Kechalari taroveh namozi o'qiladi. Ramazon oyi Qadr kechasi bilan ham mashhurdir."""
# --- PAYG'AMBARIMIZ (s.a.v) SIYRATLARI ---
SIYRAT_TEXT = """**🕋 PAYG'AMBARIMIZ MUHAMMAD (s.a.v) HAYOTLARI (BATAFSIL SIYRAT)**

1-BOB. ARABISTON VA MAKKA SHAHRINING TARIXIY HOLATI
1.1. Payg'ambarimiz tug'ilishidan oldin Arabiston yarim orolida johiliyat davri hukm surar edi. Odamlar butlarga sig'inishar, qiz bolalarni tiriklayin ko'mishar, qon to'kish, talonchilik va zinokorlik avj olgan edi. Biroq, Makka shahri o'zining Ka'ba ibodatxonasi tufayli alohida mavqega ega edi. Butun Arabiston qabilalari har yili Ka'bani ziyorat qilish uchun Makkaga kelishardi. Makkaning boshqaruvchilari Quraysh qabilasining zodagonlari edi. Ular savdo-sotiq bilan shug'ullanib, Yaman va Shom o'rtasida karvonlar uyushtirishardi.
1.2. Ka'ba milodiy 570-yilda yuz bergan "Fil voqeasi" bilan ham mashhur. Yamanning hukmdori Abraha katta qo'shin va fillar bilan Ka'bani buzish uchun Makkaga yurish qilgan edi. Biroq, Alloh taolo tomonidan yuborilgan qushlar (Abobil) toshlar otib, Abrahaning qo'shinini tor-mor keltirdi. Aynan shu yili Payg'ambarimiz (s.a.v) dunyoga keldilar.

2-BOB. TUG'ILISHLARI, BOLALIGI VA YOSHLIGI
2.1. Muhammad (s.a.v) milodiy 570-yilda, Rabiul avval oyida, dushanba kuni Makka shahrida tug'ildilar. Otalari Abdulloh ibn Abdulmuttolib, onalari Omina bint Vahb edi. Otalari Abdulloh ular dunyoga kelishlaridan bir necha oy oldin Madinaga savdo safari chog'ida vafot etgan edi. Bobosi Abdulmuttolib ularga "Muhammad" (maqtovga loyiq) deb ism qo'ydi.
2.2. Onalari Omina ularni 6 yoshga to'lganlarida vafot etdi. Shundan so'ng ularga bobosi Abdulmuttolib, u vafot etgach esa amakisi Abu Tolib g'amxo'rlik qildi. Bolalik yillarida ular Halima Sa'diya ismli badaviy ayolning uyida tarbiyalandilar. Cho'l havosi va sof arab tilida o'sishlari uchun shunday qilindi.
2.3. 8 yoshidanoq cho'ponlik qilib, tabiat bilan yaqin bo'ldilar. 12 yoshida amakisi Abu Tolib bilan savdo karvonida Shomga safar qildilar. Yo'lda Bushro shahri yaqinida Rohib Bahira ismli nasroniy olim ularni ko'rib qolib, bolaning kelajakda buyuk payg'ambar bo'lishini amakisi bilan o'z kitoblarida ko'rganini aytdi va uni asrab qolishni so'radi.
2.4. Yoshlik davrlarida ham yolg'ondan, yomonlikdan, johiliyatning buzuq ishlaridan yiroq yashadilar. 20 yoshga to'lganlarida "Hilful Fudul" (Ezgu ishlar ittifoqi) degan mazlumlarga yordam beruvchi jamiyatga a'zo bo'ldilar. 35 yoshga to'lganlarida Ka'bani ta'mirlash vaqtida "Hajarul Asvad" (Qora tosh)ni o'z joyiga qo'yish masalasida qabilalar o'rtasida kelishmovchilik chiqdi. Ular Muhammad (s.a.v)ni hakam qilib tanladilar. U zot toshni kiyimga solib, barcha qabila boshliqlariga ushlatib, o'zlari joyiga qo'ydilar va urushning oldini oldilar. Halolligi uchun xalq ularni "Al-Amin" (Ishonchli) deb atay boshladi.

3-BOB. XADIJA (R.A) BILAN TURMUSH QURISHLARI
3.1. 25 yoshga to'lganlarida Makkaning boy va obro'li savdogar ayoli Xadicha bint Xuvaylid (r.a) bilan turmush qurdilar. Ular Xadichaning savdo karvonlarini boshqarib Shomga borib kelgan, halol savdogarligi va xushmuomalaligi orqali Xadichaning ishonchini qozongan edilar. Bu nikoh 25 yil davom etdi.
3.2. Xadicha (r.a) 40 yoshda, o'zidan 15 yosh katta bo'lishiga qaramay, ularga sodiq va vafodor yor bo'ldi. Ularning nikohidan 2 o'g'il (Qosim, Abdulloh) va 4 qiz (Zaynab, Ruqayya, Ummu Kulsum, Fotima) dunyoga keldi. O'g'illari yoshligida vafot etdilar.
3.3. Payg'ambarimiz (s.a.v) turmush qurgandan so'ng, jamiyatning buzuqligidan uzoqlashib, ko'pincha Makka yaqinidagi Nur tog'idagi Hiro g'origa chiqib, yolg'izlikda o'ylar, Alloh taoloning yaratganlarini mushohada qilardilar. Bu orada jamiyatda adolat o'rnatish, odamlarni to'g'ri yo'lga boshlash haqida o'ylardilar.

4-BOB. VAHIYNING NOZIL BO'LISHI VA ILK MUSULMONLAR
4.1. Milodiy 610-yil, Ramazon oyining 17-kuni, dushanba kuni 40 yoshga to'lganlarida Hiro g'orida jabroil (a.s) farishta kelib, "O'qi!" dedi. Ular "Men o'qiydigan emasman" dedilar. Farishta ularni qattiq siqib, yana "O'qi!" dedi. Oxir-oqibat farishta Alaq surasining birinchi 5 oyatini o'qib berdi. Bu Islomdagi ilk vahiy edi.
4.2. Ular qo'rqib uylariga qaytib, xotini Xadicha (r.a) ga voqeani aytib berdilar. Xadicha (r.a) ularni taskinlab, "Alloh sizni hech qachon xor qilmaydi, chunki siz haqiqatgo'ysiz, omonatga xiyonat qilmaysiz" dedi. Xadicha (r.a) ularni o'z amakivachchasi, nasroniy olimi Varaka ibn Navfalning oldiga olib bordi. Varaka ularning payg'ambar ekanliklarini tasdiqladi.
4.3. Ilk musulmonlar: Xadicha (r.a) birinchi ayol, Abu Bakr (r.a) birinchi erkak, Ali (r.a) birinchi bola, Zayd ibn Horisa (r.a) birinchi ozod qilingan qul. Keyinchalik Usmon (r.a), Zubayr, Abdurrahmon ibn Avf, Sa'd ibn Abu Vaqqos kabi sahobalar islomni qabul qildilar. 3 yil davomida da'vat yashirincha olib borildi. Dorul Arqam sahobalar yig'iladigan ilk maskan bo'ldi.
4.4. 3 yildan so'ng, "Eng yaqin qarindoshlaringni ogohlantir" oyati nozil bo'lgach, ochiq da'vat boshlandi. Safo tepaligida barcha qabilalarni to'plab, ularni Allohga yakkaga-yakka sig'inishga chaqirdilar.

5-BOB. MAKKA MUShRIKLARINING AZOB-UQUBATLARI VA QARSHILIGI
5.1. Payg'ambarimizning da'vati Makkaning boylari va zodagonlariga (Abu Jahl, Abu Lahab, Abu Sufyon, Umayya ibn Xalaf va boshqalar) yoqmadi. Ular o'z obro'lari va Ka'ba atrofidagi butparastlik biznesidan ayrilishdan qo'rqishdi. Ular dastlab Payg'ambarimizni masxara qilishdi, keyinroq uni yo'ldan urish uchun turli takliflar (boylik, hokimiyat, ayollar) berdilar. Ular rad javobini olgach, ochiq dushmanlikka o'tishdi.
5.2. Kambag'al va quvvatsiz sahobalar eng qattiq azob-uqubatlarga uchradilar. Bilol Habashiy (r.a) Abu Jahlning quli edi, uni cho'l qumiga yotqizib, ko'kragiga tosh qo'yib azoblashardi. Sumayya (r.a) va Yosir (r.a) oilasi qattiq qiynoqqa solindi. Sumayya (r.a) Islom tarixidagi ilk shahid ayol, Yosir (r.a) esa ilk shahid erkak bo'ldilar. Payg'ambarimiz (s.a.v) o'z amakisi Abu Tolibning himoyasida bo'lganliklari uchun ularga jismoniy azob yetkazisha olmadilar. Ammo amakisi vafot etgach, ular ham ko'plab azob-uqubatlarga uchradilar.
5.3. Mushriklar Payg'ambarimizni yo'ldan urish uchun turli hiylalarga, jumladan, sehrgarlik va jinnilikda ayblashga ham urindilar. Ba'zilar she'r aytishni, ba'zilar boshqa dinlardan nusxa ko'chirishni taklif qilishdi, ammo bariga Alloh taolo "Hijr", "Qalam", "Kofirun" suralarini nozil qilib, javob berdi.
5.4. 615-yilda musulmonlarga bo'lgan azob-uqubatlar kuchaygach, Payg'ambarimiz (s.a.v) sahobalarga Habashiston (Efiopiya)ga hijrat qilishni maslahat berdilar. Adolatli hukmdor Najoshiy ularni yaxshi qabul qildi va himoya qildi. Birinchi hijratda 15 nafar kishi (11 erkak, 4 ayol) qatnashdi.

6-BOB. HIJRATDAN OLDINGI QIYINCHILIKLAR
6.1. 617-yilda Quraysh mushriklari Hashim va Muttolib urug'larini butunlay blokada qilishga qaror qildilar. Ular bilan hech qanday savdo qilinmas, qiz berilmas, oziq-ovqat sotilmasligi haqida shartnoma imzolab, Ka'ba ichiga osib qo'yishdi. Bu blokada 3 yil davom etdi. Sahobalar Shi'bu Abu Tolib (Abu Tolib darasi)da qamalib, daraxt barglari va terini yeb kun kechirishga majbur bo'lishdi. Oxir-oqibat, Alloh taolo termitlarni yuborib, butun shartnoma bitigini yeb bitirganidan keyin blokada bekor qilindi.
6.2. 620-yil "Huzn yili" (G'am-g'ussa yili) deb nomlandi. Bu yilda Payg'ambarimizning eng katta himoyachisi, amakisi Abu Tolib vafot etdi. Shundan ko'p o'tmay, ularning eng sodiq hamdami va birinchi xotini Xadicha (r.a) ham vafot etdilar. Payg'ambarimiz (s.a.v) uchun bu juda og'ir yo'qotish bo'ldi.
6.3. Makka aholisi ularga qarshi yanada qattiqroq o'ta boshlaganidan so'ng, ular yordam izlab Toif shahriga bordilar. Ammo Toif zodagonlari ularni yomon kutib oldilar, orqalaridan bolalarni va tentaklarni tashlab, toshbo'ron qildilar. Payg'ambarimiz (s.a.v) yaralanib, qonlar oqib, daraxt soyasida dam oldilar. Shunda ham Allohga shunday duo qildilar: "Agar Sen mening ustimdan g'azablanmagan bo'lsang, menga bu azoblarning hammasi oson".
6.4. Bu qiyinchiliklardan so'ng, Isro va Mi'roj mo''jizasi ro'y berdi. Bir kechada Jabroil (a.s) ularni Buroq ismli ulovda Makkadan Quddusdagi Masjidul Aqsoga olib bordilar. U yerda barcha payg'ambarlarga imom bo'lib namoz o'qidilar. So'ngra yetti qavat osmonga ko'tarilib, Sidratul Muntaho darajasiga yetdilar. U yerda 5 vaqt namoz farz qilindi. Payg'ambarimiz Makkaga qaytib kelib, bu voqeani aytganlarida mushriklar uni yana yolg'onchilikda aybladilar, ammo Abu Bakr (r.a) hech ikkilanmasdan uni tasdiqladi.

7-BOB. AQABA BAY'ATLARI VA MADINAGA HIJRAT
7.1. Payg'ambarimizning da'vati Yamanning Yasrib (Madina) shahridan kelgan qabilalar (Avs va Xazraj) orasida tarqaldi. 621-yilda Yasribdan 12 nafar kishi Makkaga kelib, Aqaba vodiysida Payg'ambarimizga bay'at berdilar. Bu Birinchi Aqaba bay'ati edi. 622-yilda esa Yasribdan 73 nafar erkak va 2 nafar ayol kelib, Ikkinchi Aqaba bay'atini berdilar. Ular Payg'ambarimizni o'z shaharlariga taklif qildilar va himoya qilishga va'da berdilar.
7.2. Shundan so'ng, sahobalarga Madinaga hijrat qilishga ruxsat berildi. Ular yashirincha guruh-guruh bo'lib Madinaga ko'chib o'ta boshladilar. Makka mushriklari buni sezib qolib, ularni to'xtatishga urindilar, ammo muvaffaqiyatsizlikka uchradilar.
7.3. Mushriklar oxir-oqibat barcha qabilalardan yigitlarni to'plab, Payg'ambarimizni o'ldirishga (qatl qilishga) qaror qildilar. Alloh taolo ularni uxlatib qo'ydi va Payg'ambarimiz (s.a.v) Ali (r.a) ni o'z to'shagiga yotqizib, Abu Bakr (r.a) bilan birga Makkadan chiqib ketdilar. Ular Sovr g'orida 3 kun yashirindilar. Mushriklar g'orning og'ziga qadar yetib kelishdi, ammo o'rgimchak in qurib, kaptar tuxum qo'yib qo'ygan edi. Abu Bakr (r.a) qo'rqib "Agar ular boshini ko'tarsa, bizni ko'radi" deganida, Payg'ambarimiz "G'am yema, Alloh biz bilan" dedilar.
7.4. 622-yil sentyabr oyida ular Madinaga (o'sha paytda Yasrib) yetib keldilar. Madina aholisi ularni juda katta shodiyona bilan kutib oldilar. Bu voqea Islom taqvimining (Hijriy yil hisobining) boshlanishi bo'ldi.

8-BOB. MADINA DAVRI. ILK ISLOM DAVLATINING SHAKLLANISHI
8.1. Madinaga hijrat qilingach, Payg'ambarimiz (s.a.v) birinchi navbatda Qubo masjidini qurdilar. Keyin esa shahar markazida Masjidun Nabawiyni (Payg'ambar masjidini) bunyod etdilar. Masjid yonida o'zlari va ahli a'yonlari uchun xonalar qurildi.
8.2. Muhajirin (Makkaliklar) va Ansor (Madinaliklar) o'rtasida "Muaxot" - birodarlik munosabatlari o'rnatildi. Har bir ansoriy o'z uyini, mol-mulkini muhajir birodari bilan teng bo'lishdi. Bu tarixda misli ko'rilmagan bag'rikenglik va birodarlik edi.
8.3. Madinada yahudiylar va boshqa qabilalar ham yashar edi. Ular bilan tinch-totuv yashash, shaharni birgalikda himoya qilish uchun "Madina sahifasi" (birinchi konstitutsiya) tuzildi. Unda barcha diniy va siyosiy huquqlar, majburiyatlar belgilab qo'yildi.
8.4. Musulmonlar Makkadagi azob-uqubatlardan qutilib, Madinada erkin yashay boshladilar. Ammo Makka mushriklari ularni tashlab qo'yishmadi. Ular Madinadagi musulmonlarga qarshi fitnalar uyushtirishni, ularning savdo karvonlarini to'sishni boshladilar.

9-BOB. BADR, UHUD VA XANDAQ JANGLARI
9.1. Badr jangi (624-yil, Hijriy 2-yil, Ramazon oyi): Makka mushriklarining katta savdo karvoni Abu Sufyon boshchiligida Shomdan qaytayotgan edi. Musulmonlar karvonni to'sib qolish niyatida chiqdilar. Buni eshitgan Makka mushriklari 1000 kishilik qo'shin bilan Madinaga yurish qildilar. Musulmonlar 313 kishi edi. Badr quduqlari yonida bo'lib o'tgan bu jangda Alloh taolo musulmonlarga g'alaba berdi. 70 nafar mushrik o'ldirildi, 70 nafari asirga olindi.
9.2. Uhud jangi (625-yil, Hijriy 3-yil, Shavvol oyi): Makka mushriklari Badrning qasosini olish uchun 3000 kishilik qo'shin bilan Madinaga yurish qildilar. Musulmonlar 700 kishi edilar. Uhud tog'i etagida bo'lib o'tgan jangda dastlab musulmonlar g'alaba qozonishayotgan edi. Ammo kamonchilar Payg'ambarimizning "Joyingizdan qimirlamang" degan buyruqlariga qarshi chiqib, o'lja yig'ishga tushib ketishdi. Shunda Xolid bin Valid boshchiligidagi mushriklar orqadan hujum qilib, musulmonlarni mag'lub etishdi. Bu jangda 70 nafar sahoba, jumladan Payg'ambarimizning amakilari Hamza (r.a) shahid bo'ldilar. Payg'ambarimizning o'zlari ham yaralandilar.
9.3. Xandaq (Ahzob) jangi (627-yil, Hijriy 5-yil, Shavvol oyi): Makka mushriklari, Madinadagi munofiq va yahudiylar bilan til biriktirib, 10000 kishilik qo'shin bilan Madinani qurshab oldilar. Payg'ambarimiz (s.a.v) sahobalar bilan maslahatlashib, Salman Forsiyning taklifiga ko'ra, Madina atrofidagi ochiq joylarga chuqur xandaq qazishga qaror qildilar. Musulmonlar 3000 kishi edi. Xandaq dushman otliqlari uchun to'siq bo'ldi. Qamal taxminan bir oy davom etdi. Oxir-oqibat, kuchli shamol va sovuq tufayli dushman qo'shini tarqalib ketdi.

10-BOB. HUDAYBIYA SULHI, MAKKA FATHI VA BOSHQA VOQEALAR
10.1. Hudaybiya sulhi (628-yil, Hijriy 6-yil, Zulqa'da oyi): Payg'ambarimiz (s.a.v) 1400 nafar sahoba bilan kichik haj (Umra) qilish niyatida Makkaga qarab yo'lga chiqdilar. Makka mushriklari ularni shaharga kiritmasliklarini aytishdi. Hudaybiya nomli joyda ular o'rtasida 10 yillik sulh tuzildi. Musulmonlar bu yili Umra qilmasdan qaytishdi, keyingi yili qilishlari shart qilindi. Bu sulh musulmonlar uchun katta siyosiy g'alaba edi.
10.2. Xaybar fath etilishi (628-yil, Hijriy 7-yil): Hudaybiyadan qaytishgach, Payg'ambarimiz (s.a.v) Madina yaqinidagi Xaybar yahudiylari ustiga yurish qildilar. Xaybar qal'alari birin-ketin fath etildi. Ali (r.a) qahramonlik ko'rsatib, eng mustahkam qal'ani ochdi.
10.3. Makka fathi (630-yil, Hijriy 8-yil, Ramazon oyi): Hudaybiya sulhi buzilgach, Payg'ambarimiz (s.a.v) 10000 kishilik qo'shin bilan yashirincha Makkaga yurish qildilar. Mushriklar buni kutmagan edilar. Musulmonlar Makkaga jangsiz, deyarli qonsiz kirdilar. Payg'ambarimiz (s.a.v) Ka'bani butlardan tozaladilar va barcha mushriklarga amon (kechirim) berdilar. "Bugun sizlar ustidan hech qanday ayblov yo'q, boringlar, ozodsizlar" dedilar. Bu g'alaba Islomning butun Arabistonga tarqalishiga sabab bo'ldi.
10.4. Huzayn va Toif janglari (630-yil): Makka fathi ortidan Huzayn qabilasi va Toif shahri mushriklari qarshi chiqdilar. Huzayn jangida musulmonlar dastlab qiyinchilikka uchradilar, ammo keyin g'alaba qozondilar. Toif qamal qilindi, ammo olinmaganidan keyin musulmonlar qaytishdi. Keyinchalik Toif aholisi o'zlari Islomni qabul qilishdi.

11-BOB. VIDOLASHUV HAJJI VA VAFOTLARI
11.1. 632-yil (Hijriy 10-yil, Zulhijja oyi): Payg'ambarimiz (s.a.v) yuz mingdan ortiq musulmonlar bilan birga "Vidolashuv Hajji" (Hajjatul Vida)ni ado etdilar. Arafot tog'ida mashhur xutbani o'qidilar. Bu xutbada inson huquqlari, ayollar huquqlari, qon to'kishning haromligi, omonatga xiyonat qilishning haromligi, barcha musulmonlarning birodarligi e'lon qilindi. "Men sizlarga ikki narsa qoldirdim: Allohning Kitobi (Qur'on) va mening Sunnatim. Agar ularga amal qilsangiz, hech qachon adashmaysizlar" dedilar.
11.2. Vidolashuv hajjidan qaytgach, Payg'ambarimiz (s.a.v) Madinada kasal bo'lib qoldilar. 632-yil, Rabiul avval oyining 12-kuni, dushanba kuni, 63 yoshida Madinada vafot etdilar. Vafot etishlaridan oldin oxirgi so'zlari: "Namozga va qo'lingiz ostidagi (qullaringizga) amal qilinglar" bo'ldi.
11.3. Ular Masjidun Nabawiydagi Oysha (r.a)ning xonasida dafn etildilar. Butun Arabiston va Makka musulmonlar uchun motam tutdi. Payg'ambarimiz (s.a.v) o'zlaridan keyin bevosita o'rinbosar (xalifa) tayinlamadilar, ammo sahobalar maslahati bilan Abu Bakr Siddiq (r.a) birinchi xalifa etib saylandi.
11.4. Payg'ambarimiz (s.a.v) vafot etganlarida Islom dini Arabiston yarim orolining deyarli barcha qismiga tarqalgan, musulmonlar soni yuz minglab kishiga yetgan edi. Ular o'zlaridan keyin ulkan meros - Qur'oni Karim va Sunnatni qoldirdilar.
"""
