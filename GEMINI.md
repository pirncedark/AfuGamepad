# Afu ekosistemi — basitlik kuralı (zorunlu)

AfuDM, AfuRemote, AfuTube, AfuDesk, PadKöprü ve gelecekteki tüm Afu uygulamalarında kullanıcıya dönük her iş bu kurala uyar.

Kullanıcı hedefi: Aç → cihazı seç → ana düğmeye bas → çalışsın. Teknik detayları uygulama kendi yönetir.

1. Varsayılanlar doğru çalışır. Kullanıcı gereksiz ayar yapmak zorunda kalmaz; sistem gerekli seçimleri mümkün olduğunca otomatik yapar.
2. Ekran başına tek ana işlem: büyük, net, kolay anlaşılır tek ana düğme. IP, port, protokol, NAT, relay gibi teknik terimler normal kullanıcıya gösterilmez. Cihazlar adresle değil adıyla gösterilir.
3. Sorunu uygulama çözer. Eksik izin varsa izni kendisi ister. Eksik sürücü/bileşen varsa ne gerektiğini söyler ve tek dokunuşla çözüm sunar (ör. resmi indirme linkini açar). Mümkünse kullanıcıyı elle işlem yapmaya göndermez.
4. Hata mesajı tek cümle: ne oldu + kullanıcı ne yapmalı. Uzun teknik hata gösterilmez. Örnek: "Gamepad sürücüsü eksik. Kurmak için dokun."
5. Yeni bir özellik ilk kez açıldığında kısa yönlendirme gösterilir; aynı açıklama tekrar gösterilmez.
6. Gelişmiş ayarlar gizlidir. Teknik ayarlar arka planda otomatik yönetilir. Yalnız uzman kullanıcı için gerçekten gerekiyorsa ayrı bir "Gelişmiş" bölümünde durur; ana ekranda asla.
7. Otomatik en iyi seçim. AfuRemote gibi sistemlerde en hızlı bağlantı yolu, en iyi host, codec, FPS, bitrate ve çözünürlük mümkün olduğunca otomatik seçilir.
